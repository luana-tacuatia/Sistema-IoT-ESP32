from flask import Flask, request

app = Flask(__name__)

@app.route('/dados', methods=['POST'])
def receber():
    print(request.json)
    return {"ok": True}

app.run(host='0.0.0.0', port=5000)