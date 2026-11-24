from flask import Flask, jsonify, request

from gateway import dispatch

app = Flask(__name__)


@app.post("/orders")
def create_order():
    body = request.get_json()
    if not isinstance(body, dict):
        return {"error": "expected a JSON object"}, 400
    if not isinstance(body.get("account_id", ""), str):
        return {"error": "account_id must be a string"}, 400

    handler, result = dispatch(body)
    response = jsonify(result)
    response.headers["X-Order-Handler"] = handler
    return response, 201 if handler == "v2" else 200
