"""
alertas.py — Monitor de alertas em background com notificação via Telegram.

Fluxo:
  1. A cada INTERVALO_SEGUNDOS, busca a leitura mais recente no banco.
  2. Compara com os thresholds definidos em LIMITES.
  3. Se algum valor estiver fora da faixa E ainda não foi alertado para aquela
     condição, envia uma mensagem consolidada pelo Telegram.
  4. Quando TODOS os valores voltam ao normal, envia mensagem de resolução
     (também apenas uma vez).
"""

import os
import sqlite3
import threading
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuração do Telegram ────────────────────────────────────────────────

TELEGRAM_TOKEN   = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

# ── Thresholds ──────────────────────────────────────────────────────────────

LIMITES = {
    'temperatura': {
        'label': '🌡 Temperatura',
        'unidade': '°C',
        'min': 15.0,
        'max': 35.0,
    },
    'umidade_ar': {
        'label': '💧 Umidade do Ar',
        'unidade': '%',
        'min': 30.0,
        'max': 90.0,
    },
    'umidade_solo': {
        'label': '🌱 Umidade do Solo',
        'unidade': '%',
        'min': 20.0,
        'max': 80.0,
    },
}

# Intervalo entre verificações (segundos)
INTERVALO_SEGUNDOS = 5 * 60  # 5 minutos

# ── Estado interno ──────────────────────────────────────────────────────────
# Evita spam: só dispara uma notificação por transição de estado.
#
# _alerta_ativo = True  → já foi enviado alerta; aguardando normalização.
# _alerta_ativo = False → situação normal (ou já foi enviada resolução).

_alerta_ativo = False
_lock = threading.Lock()


# ── Telegram ────────────────────────────────────────────────────────────────

def _enviar_telegram(mensagem: str) -> bool:
    """Envia uma mensagem para o chat configurado. Retorna True se bem-sucedido."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning('Telegram não configurado (TELEGRAM_TOKEN / TELEGRAM_CHAT_ID ausentes).')
        return False

    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': mensagem,
        'parse_mode': 'HTML',
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info('Mensagem Telegram enviada com sucesso.')
        return True
    except requests.RequestException as exc:
        logger.error('Falha ao enviar mensagem Telegram: %s', exc)
        return False


# ── Verificação ─────────────────────────────────────────────────────────────

def _buscar_ultima_leitura(db_path: str) -> dict | None:
    """Retorna a leitura mais recente do banco, ou None se não houver dados."""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT temperatura, umidade_ar, umidade_solo, timestamp
                FROM leituras
                ORDER BY id DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
    except sqlite3.Error as exc:
        logger.error('Erro ao consultar banco de dados: %s', exc)
        return None

    if not row:
        return None

    return {
        'temperatura':  row[0],
        'umidade_ar':   row[1],
        'umidade_solo': row[2],
        'timestamp':    row[3],
    }


def _avaliar_leitura(leitura: dict) -> list[dict]:
    """
    Retorna lista de violações encontradas.
    Cada item: {'campo', 'label', 'valor', 'unidade', 'tipo' ('alto'|'baixo'), 'limite'}
    """
    violacoes = []
    for campo, cfg in LIMITES.items():
        valor = leitura.get(campo)
        if valor is None:
            continue
        if valor < cfg['min']:
            violacoes.append({
                'campo':   campo,
                'label':   cfg['label'],
                'valor':   valor,
                'unidade': cfg['unidade'],
                'tipo':    'baixo',
                'limite':  cfg['min'],
            })
        elif valor > cfg['max']:
            violacoes.append({
                'campo':   campo,
                'label':   cfg['label'],
                'valor':   valor,
                'unidade': cfg['unidade'],
                'tipo':    'alto',
                'limite':  cfg['max'],
            })
    return violacoes


def _montar_mensagem_alerta(violacoes: list[dict], timestamp: str) -> str:
    linhas = ['⚠️ <b>Alerta de Condições Inadequadas</b>\n']
    for v in violacoes:
        seta = '🔺' if v['tipo'] == 'alto' else '🔻'
        linhas.append(
            f"{v['label']}: <b>{v['valor']:.1f}{v['unidade']}</b> "
            f"{seta} (limite {'máx' if v['tipo'] == 'alto' else 'mín'}: "
            f"{v['limite']:.1f}{v['unidade']})"
        )
    linhas.append(f'\n🕐 {_formatar_timestamp(timestamp)}')
    return '\n'.join(linhas)


def _montar_mensagem_resolucao(leitura: dict) -> str:
    temp  = leitura['temperatura']
    hum   = leitura['umidade_ar']
    soil  = leitura['umidade_solo']
    ts    = leitura['timestamp']
    return (
        '✅ <b>Condições Normalizadas</b>\n\n'
        f'🌡 Temperatura: <b>{temp:.1f} °C</b>\n'
        f'💧 Umidade do Ar: <b>{hum:.1f} %</b>\n'
        f'🌱 Umidade do Solo: <b>{soil:.1f} %</b>\n\n'
        f'🕐 {_formatar_timestamp(ts)}'
    )


def _formatar_timestamp(ts: str) -> str:
    """Converte ISO timestamp para formato legível em pt-BR."""
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(ts).astimezone(tz=None)
        return dt.strftime('%d/%m/%Y às %H:%M')
    except Exception:
        return ts


# ── Worker ──────────────────────────────────────────────────────────────────

def _worker(db_path: str) -> None:
    global _alerta_ativo

    logger.info('Monitor de alertas iniciado (intervalo: %ds).', INTERVALO_SEGUNDOS)

    while True:
        try:
            leitura = _buscar_ultima_leitura(db_path)

            if leitura is None:
                logger.debug('Nenhuma leitura disponível ainda.')
            else:
                violacoes = _avaliar_leitura(leitura)

                with _lock:
                    if violacoes and not _alerta_ativo:
                        # Nova condição de alerta — dispara notificação
                        msg = _montar_mensagem_alerta(violacoes, leitura['timestamp'])
                        if _enviar_telegram(msg):
                            _alerta_ativo = True
                        logger.warning(
                            'Alerta disparado: %s',
                            ', '.join(v['campo'] for v in violacoes),
                        )

                    elif not violacoes and _alerta_ativo:
                        # Situação normalizada — dispara resolução
                        msg = _montar_mensagem_resolucao(leitura)
                        if _enviar_telegram(msg):
                            _alerta_ativo = False
                        logger.info('Condições normalizadas. Resolução enviada.')

        except Exception as exc:
            logger.exception('Erro inesperado no monitor de alertas: %s', exc)

        time.sleep(INTERVALO_SEGUNDOS)


def iniciar_monitor(db_path: str) -> None:
    """
    Inicia o worker de alertas em uma thread daemon.
    Chamar uma vez na inicialização da aplicação Flask.
    """
    t = threading.Thread(target=_worker, args=(db_path,), daemon=True, name='AlertMonitor')
    t.start()