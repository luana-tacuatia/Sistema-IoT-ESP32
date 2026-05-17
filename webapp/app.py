from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone
import sqlite3
import os

app = Flask(__name__)

DATABASE = os.path.join(os.path.dirname(__file__), 'database.db')

# Períodos válidos aceitos pela API
PERIODOS_VALIDOS = {
    '30min': '-30 minutes',
    '1h':    '-1 hour',
    '24h':   '-24 hours',
    '1mes':  '-1 month',
    '6m':    '-6 months',
    '12m':   '-12 months',
}

# Fração mínima da janela que os dados precisam cobrir para o período ser habilitado.
# Ex: 0.8 = os dados precisam começar em até 20% do início da janela.
COBERTURA_MINIMA = 0.8


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperatura REAL,
                umidade_ar REAL,
                umidade_solo REAL,
                timestamp TEXT
            )
        """)
        conn.commit()


init_db()


@app.route('/dados', methods=['POST'])
def receber_dados():

    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"status": "erro", "mensagem": "Payload inválido ou Content-Type incorreto"}), 400

    temperatura  = dados.get("temp")
    umidade_ar   = dados.get("hum")
    umidade_solo = dados.get("soil")

    if temperatura is None or umidade_ar is None or umidade_solo is None:
        return jsonify({
            "status": "erro",
            "mensagem": "Campos obrigatórios ausentes: 'temp', 'hum', 'soil'"
        }), 400

    if not all(isinstance(v, (int, float)) for v in [temperatura, umidade_ar, umidade_solo]):
        return jsonify({
            "status": "erro",
            "mensagem": "Os campos 'temp', 'hum' e 'soil' devem ser numéricos"
        }), 400

    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leituras (temperatura, umidade_ar, umidade_solo, timestamp)
                VALUES (?, ?, ?, ?)
            """, (temperatura, umidade_ar, umidade_solo, timestamp))
            conn.commit()
    except sqlite3.Error as e:
        return jsonify({"status": "erro", "mensagem": f"Erro no banco de dados: {str(e)}"}), 500

    return jsonify({"status": "sucesso"}), 201


@app.route('/api/dados')
def api_dados():

    periodo = request.args.get('periodo', '30min')
    filtro  = PERIODOS_VALIDOS.get(periodo)

    if filtro is None:
        return jsonify({
            "status": "erro",
            "mensagem": f"Período inválido. Opções válidas: {list(PERIODOS_VALIDOS.keys())}"
        }), 400

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT temperatura, umidade_ar, umidade_solo, timestamp
                FROM leituras
                WHERE datetime(timestamp) >= datetime('now', ?)
                ORDER BY id ASC
            ''', (filtro,))
            dados = cursor.fetchall()
    except sqlite3.Error as e:
        return jsonify({"status": "erro", "mensagem": f"Erro no banco de dados: {str(e)}"}), 500

    resultado = [
        {
            'temperatura':  linha[0],
            'umidade_ar':   linha[1],
            'umidade_solo': linha[2],
            'timestamp':    linha[3]
        }
        for linha in dados
    ]

    return jsonify(resultado)


@app.route('/api/periodos-disponiveis')
def periodos_disponiveis():
    """
    Um período é considerado disponível quando o registro mais antigo dentro
    da janela cobre pelo menos COBERTURA_MINIMA da duração total do período.

    Exemplo com '24h' e COBERTURA_MINIMA = 0.8:
      - A janela começa em now - 24h.
      - O registro mais antigo precisa ter timestamp <= now - 24h * 0.8 = now - 19.2h.
      - Se o sistema tem apenas 14h de dados, o mais antigo estará em now - 14h,
        que é mais recente que now - 19.2h → período desabilitado. ✓
    """
    disponibilidade = {}

    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            for periodo, filtro in PERIODOS_VALIDOS.items():
                # Timestamp mais antigo dentro da janela do período
                cursor.execute('''
                    SELECT MIN(timestamp) FROM leituras
                    WHERE datetime(timestamp) >= datetime('now', ?)
                ''', (filtro,))
                row = cursor.fetchone()
                mais_antigo = row[0] if row else None

                if not mais_antigo:
                    disponibilidade[periodo] = False
                    continue

                # Calcula cobertura real: quanto da janela os dados cobrem
                # Usa o SQLite para calcular o início esperado da janela em segundos
                cursor.execute(
                    "SELECT (julianday('now') - julianday(?)) * 86400.0",
                    (mais_antigo,)
                )
                segundos_cobertos = cursor.fetchone()[0] or 0

                cursor.execute(
                    "SELECT (julianday('now') - julianday(datetime('now', ?))) * 86400.0",
                    (filtro,)
                )
                segundos_janela = cursor.fetchone()[0] or 1

                cobertura = segundos_cobertos / segundos_janela
                disponibilidade[periodo] = cobertura >= COBERTURA_MINIMA

    except sqlite3.Error as e:
        return jsonify({"status": "erro", "mensagem": f"Erro no banco de dados: {str(e)}"}), 500

    return jsonify(disponibilidade)


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug)