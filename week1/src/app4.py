from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock data
BOOKS = [
    {"id": "1", "title": "Lap trinh Python"},
    {"id": "2", "title": "Flask co ban"}
]

def find_by_id(book_id):
    for book in BOOKS:
        if book["id"] == book_id:
            return book
    return None

# Path params
@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200

@app.route("/items/<int:item_id>")
def get_item(item_id): # int sẵn
    return jsonify({"id": item_id}), 200

# Query string 
@app.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    q = request.args.get("q", "").strip().lower()
    items = [b for b in BOOKS if q in b["title"].lower()]
    return jsonify({"items": items[:limit]}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)