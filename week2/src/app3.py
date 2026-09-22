from flask import Flask, jsonify, request, make_response

app = Flask(__name__)
BOOKS = [
    {"id": 1, "title": "Clean Code", "author": "Robert C. Martin"},
    {"id": 2, "title": "Clean Architecture", "author": "Robert C. Martin"},
    {"id": 3, "title": "The Pragmatic Programmer", "author": "Andrew Hunt"},
    {"id": 4, "title": "1984", "author": "George Orwell"},
    {"id": 5, "title": "Animal Farm", "author": "George Orwell"},
    {"id": 6, "title": "Design Patterns", "author": "Erich Gamma"},
    {"id": 7, "title": "Refactoring", "author": "Martin Fowler"},
    {"id": 8, "title": "Domain-Driven Design", "author": "Eric Evans"},
    {"id": 9, "title": "Introduction to Algorithms", "author": "Thomas H. Cormen"},
    {"id": 10, "title": "Code Complete", "author": "Steve McConnell"},
    {"id": 11, "title": "The Mythical Man-Month", "author": "Frederick P. Brooks Jr."},
    {"id": 12, "title": "Head First Design Patterns", "author": "Eric Freeman"},
    {"id": 13, "title": "Python Crash Course", "author": "Eric Matthes"},
    {"id": 14, "title": "Fluent Python", "author": "Luciano Ramalho"},
    {"id": 15, "title": "Grokking Algorithms", "author": "Aditya Bhargava"},
    {"id": 16, "title": "Clean Agile", "author": "Robert C. Martin"},
    {"id": 17, "title": "Structure and Interpretation of Computer Programs", "author": "Harold Abelson"},
    {"id": 18, "title": "Computer Systems: A Programmer's Perspective", "author": "Randal E. Bryant"},
    {"id": 19, "title": "Operating System Concepts", "author": "Abraham Silberschatz"},
    {"id": 20, "title": "Compilers: Principles, Techniques, and Tools", "author": "Alfred V. Aho"},
    {"id": 21, "title": "Homage to Catalonia", "author": "George Orwell"},
    {"id": 22, "title": "Down and Out in Paris and London", "author": "George Orwell"},
    {"id": 23, "title": "Effective Java", "author": "Joshua Bloch"},
    {"id": 24, "title": "Java Concurrency in Practice", "author": "Brian Goetz"},
    {"id": 25, "title": "Spring in Action", "author": "Craig Walls"},
]

# ----- tham số phân trang
DEFAULT_SIZE, MAX_SIZE = 20, 100

# ----- list + filter + paginate + links
@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify(error="page and size must be int"), 400
    page = max(page, 1); size = max(min(size, MAX_SIZE), 1)
    
    # filter: author chính xác, q tìm trong title
    flt = BOOKS
    a = request.args.get("author")
    if a: flt = [b for b in flt if b["author"].lower()==a.lower()]
    q = (request.args.get("q") or "").lower()
    if q: flt = [b for b in flt if q in b["title"].lower()]
    
    # paginate
    total = len(flt); start=(page-1)*size; end=start+size
    items = flt[start:end]; last=max((total+size-1)//size, 1) if total > 0 else 0
    
    # HATEOAS links
    def u(p): return f"/books?page={p}&size={size}"
    links = {"self":{"href":u(page)},
             "first":{"href":u(1)},
             "last":{"href":u(max(last,1))}}
    if page > 1: links["prev"]={"href":u(page-1)}
    if end < total: links["next"]={"href":u(page+1)}
    
    body = {"data":items,
            "pagination":{"page":page,"size":size,"total":total,"total_pages":last},
            "_links":links}
    
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"]="public, max-age=30"
    return resp

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)