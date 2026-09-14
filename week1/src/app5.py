from flask import Flask, jsonify

app = Flask(__name__)

# Mock data giả lập DB
ORDERS = {
    "1": {"id": "1", "status": "pending"},
    "2": {"id": "2", "status": "shipped"},
    "3": {"id": "3", "status": "delivered"}
}

# DELETE /orders/<order_id>
@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = ORDERS.get(order_id)
    
    # 404 - không tìm thấy
    if order is None:
        return {"error": "not found"}, 404
        
    # 409 business rule
    if order["status"] in ("shipped", "delivered"):
        return {"error": "cannot delete"}, 409
        
    ORDERS.pop(order_id, None)
    
    # 204 success, no body
    return "", 204

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)