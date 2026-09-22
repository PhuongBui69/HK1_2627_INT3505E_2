import sqlite3
import hashlib
from flask import Flask, jsonify, request, make_response, g

app = Flask(__name__)
DATABASE = 'database.db'

DEFAULT_SIZE, MAX_SIZE = 20, 100

def calc_etag(title, author, isbn, price):
    content = f"{title}:{author}:{isbn}:{price}"
    return hashlib.md5(content.encode()).hexdigest()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT,
                price REAL,
                etag TEXT
            )
        ''')
        # Seed mock data if table is empty
        cur = db.execute('SELECT COUNT(*) FROM books')
        if cur.fetchone()[0] == 0:
            books_data = [
                ("Clean Code", "Robert C. Martin", "111", 29.99),
                ("Clean Architecture", "Robert C. Martin", "222", 34.99),
                ("The Pragmatic Programmer", "Andrew Hunt", "333", 39.99),
                ("1984", "George Orwell", "444", 19.99),
                ("Animal Farm", "George Orwell", "555", 14.99),
                ("Design Patterns", "Erich Gamma", "666", 45.00),
                ("Refactoring", "Martin Fowler", "777", 40.00),
                ("Domain-Driven Design", "Eric Evans", "888", 50.00),
                ("Introduction to Algorithms", "Thomas H. Cormen", "999", 60.00),
                ("Code Complete", "Steve McConnell", "101", 35.00),
                ("The Mythical Man-Month", "Frederick P. Brooks Jr.", "102", 25.00),
                ("Head First Design Patterns", "Eric Freeman", "103", 45.00),
                ("Python Crash Course", "Eric Matthes", "104", 30.00),
                ("Fluent Python", "Luciano Ramalho", "105", 42.00),
                ("Grokking Algorithms", "Aditya Bhargava", "106", 38.00),
                ("Clean Agile", "Robert C. Martin", "107", 28.00),
                ("Structure and Interpretation of Computer Programs", "Harold Abelson", "108", 55.00),
                ("Computer Systems: A Programmer's Perspective", "Randal E. Bryant", "109", 70.00),
                ("Operating System Concepts", "Abraham Silberschatz", "110", 65.00),
                ("Compilers: Principles, Techniques, and Tools", "Alfred V. Aho", "111", 68.00),
                ("Homage to Catalonia", "George Orwell", "112", 15.99),
                ("Down and Out in Paris and London", "George Orwell", "113", 12.99),
                ("Effective Java", "Joshua Bloch", "114", 45.00),
                ("Java Concurrency in Practice", "Brian Goetz", "115", 35.00),
                ("Spring in Action", "Craig Walls", "116", 40.00),
            ]
            for t, a, i, p in books_data:
                db.execute('INSERT INTO books (title, author, isbn, price, etag) VALUES (?, ?, ?, ?, ?)', 
                           (t, a, i, p, calc_etag(t, a, i, p)))
            db.commit()

# --- APP 1 + 3: GET list + filter + paginate + links & POST create ---

@app.route("/books", methods=["GET", "POST"])
def books_endpoint():
    db = get_db()
    
    if request.method == "GET":
        try:
            page = int(request.args.get("page", 1))
            size = int(request.args.get("size", DEFAULT_SIZE))
        except ValueError:
            return jsonify(error="page and size must be int"), 400
        page = max(page, 1); size = max(min(size, MAX_SIZE), 1)
        
        # Build query
        query = "SELECT * FROM books WHERE 1=1"
        params = []
        
        a = request.args.get("author")
        if a:
            query += " AND LOWER(author) = ?"
            params.append(a.lower())
            
        q = request.args.get("q")
        if q:
            query += " AND LOWER(title) LIKE ?"
            params.append(f"%{q.lower()}%")
            
        # Count total for pagination
        cur = db.execute(f"SELECT COUNT(*) FROM ({query})", params)
        total = cur.fetchone()[0]
        
        # Add pagination
        offset = (page - 1) * size
        query += " LIMIT ? OFFSET ?"
        params.extend([size, offset])
        
        # Fetch items
        cur = db.execute(query, params)
        # Exclude etag from the GET list body to save bandwidth (or include it if you wish)
        items = []
        for row in cur.fetchall():
            rec = dict(row)
            rec.pop("etag", None)
            items.append(rec)
        
        last = max((total + size - 1) // size, 1) if total > 0 else 0
        
        # HATEOAS links
        def u(p): return f"/books?page={p}&size={size}"
        links = {
            "self": {"href": u(page)},
            "first": {"href": u(1)},
            "last": {"href": u(max(last, 1))}
        }
        if page > 1: links["prev"] = {"href": u(page - 1)}
        if offset + size < total: links["next"] = {"href": u(page + 1)}
        
        body = {
            "data": items,
            "pagination": {"page": page, "size": size, "total": total, "total_pages": last},
            "_links": links
        }
        resp = make_response(jsonify(body), 200)
        resp.headers["Cache-Control"] = "public, max-age=30"
        return resp

    elif request.method == "POST":
        p = request.get_json(silent=True) or {}
        t = (p.get("title") or "").strip()
        a = (p.get("author") or "").strip()
        if not t or not a:
            return jsonify(error="title and author required"), 422
            
        etag = calc_etag(t, a, p.get("isbn"), p.get("price"))
        cur = db.execute('INSERT INTO books (title, author, isbn, price, etag) VALUES (?, ?, ?, ?, ?)', 
                         (t, a, p.get("isbn"), p.get("price"), etag))
        db.commit()
        
        new_id = cur.lastrowid
        cur = db.execute('SELECT * FROM books WHERE id = ?', (new_id,))
        new_book = dict(cur.fetchone())
        new_book.pop("etag", None)
        
        resp = make_response(jsonify(new_book), 201)
        resp.headers["Location"] = f"/books/{new_id}"
        resp.headers["ETag"] = etag
        return resp

# --- APP 2: GET (single) + PUT + PATCH + DELETE ---

@app.route("/books/<int:bid>", methods=["GET", "PUT", "PATCH", "DELETE"])
def book_endpoint(bid):
    db = get_db()
    
    # Check if exists
    cur = db.execute('SELECT * FROM books WHERE id = ?', (bid,))
    row = cur.fetchone()
    if row is None:
        return jsonify(error="not found"), 404
        
    if request.method == "GET":
        record = dict(row)
        etag = record.pop("etag", None)
        
        if request.headers.get("If-None-Match") == etag:
            return "", 304
            
        resp = make_response(jsonify(record), 200)
        resp.headers["Cache-Control"] = "max-age=60"
        if etag:
            resp.headers["ETag"] = etag
        return resp
        
    elif request.method == "PUT":
        p = request.get_json(silent=True) or {}
        t = (p.get("title") or "").strip()
        a = (p.get("author") or "").strip()
        if not t or not a:
            return jsonify(error="need title+author"), 422
            
        etag = calc_etag(t, a, p.get("isbn"), p.get("price"))
        db.execute('UPDATE books SET title = ?, author = ?, isbn = ?, price = ?, etag = ? WHERE id = ?',
                   (t, a, p.get("isbn"), p.get("price"), etag, bid))
        db.commit()
        
        cur = db.execute('SELECT * FROM books WHERE id = ?', (bid,))
        updated = dict(cur.fetchone())
        updated.pop("etag", None)
        
        resp = make_response(jsonify(updated), 200)
        resp.headers["ETag"] = etag
        return resp
        
    elif request.method == "PATCH":
        p = request.get_json(silent=True) or {}
        if p.get("price", 0) < 0:
            return jsonify(error="price must be positive"), 422
            
        # Update dynamically
        current = dict(row)
        for k in "title author isbn price".split():
            if k in p:
                current[k] = p[k] if not isinstance(p[k], str) else p[k].strip()
                
        new_etag = calc_etag(current.get("title"), current.get("author"), current.get("isbn"), current.get("price"))
        
        db.execute('UPDATE books SET title = ?, author = ?, isbn = ?, price = ?, etag = ? WHERE id = ?',
                   (current.get("title"), current.get("author"), current.get("isbn"), current.get("price"), new_etag, bid))
        db.commit()
            
        cur = db.execute('SELECT * FROM books WHERE id = ?', (bid,))
        updated = dict(cur.fetchone())
        updated.pop("etag", None)
        
        resp = make_response(jsonify(updated), 200)
        resp.headers["ETag"] = new_etag
        return resp
        
    elif request.method == "DELETE":
        db.execute('DELETE FROM books WHERE id = ?', (bid,))
        db.commit()
        return "", 204

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
