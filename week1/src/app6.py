from flask import Flask, jsonify, request

app = Flask(__name__)

_next = 2
BOOKS = [{"id":1,"title":"Clean Code", "author":"R. Martin", "year": 2008}]

def find(bid):
    return next((b for b in BOOKS if b["id"] == bid), None)

# LIST GET /books
@app.route("/books", methods=["GET"])
def list_books():
    q = request.args.get("q", "").strip().lower()
    sort_by = request.args.get("sort", "").strip().lower()
    
    result = BOOKS
    if q:
        result = [b for b in result if q in b["title"].lower()]
        
    if sort_by == "title":
        result = sorted(result, key=lambda b: b.get("title", "").lower())
        
    n = int(request.args.get("limit", 100))
    return jsonify(result[:n]), 200

# DETAIL GET /books/<int:bid>
@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    book = find(bid)
    if not book: return {"error": "not found"}, 404
    return jsonify(book), 200

# CREATE POST /books
@app.route("/books", methods=["POST"])
def create_book():
    global _next
    body = request.get_json(silent=True) or {}
    t, a = body.get("title"), body.get("author")
    year = body.get("year")
    
    if not t or not a:
        return {"error":"need title+author"}, 400
        
    if year is None or type(year) is not int or year < 1900:
        return {"error":"year must be an integer >= 1900"}, 400
        
    book = {"id":_next, "title":t, "author":a, "year": year}
    _next += 1
    BOOKS.append(book)
    
    return jsonify(book), 201, {"Location": f"/books/{book['id']}"}

# UPDATE PUT, DELETE DELETE
@app.route("/books/<int:bid>", methods=["PUT", "DELETE"])
def modify_book(bid):
    book = find(bid)
    if not book: return {"error":"not found"}, 404
    
    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        if "year" in body:
            year = body["year"]
            if type(year) is not int or year < 1900:
                return {"error": "year must be an integer >= 1900"}, 400
        book.update(body)
        return jsonify(book), 200
        
    BOOKS.remove(book)
    return "", 204

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)