from models import db, Category, Book

CATEGORIES_DATA = [
    {"name": "Technology", "slug": "tech"},
    {"name": "Science", "slug": "science"},
    {"name": "Fiction", "slug": "fiction"},
    {"name": "Business", "slug": "business"},
]

BOOKS_DATA = [
    # Technology (slug: tech)
    # Notice multiple books share the exact same price (e.g. 350000, 250000) to test tie-breakers
    {"title": "Clean Code", "author": "Robert C. Martin", "isbn": "9780132350884", "price": 350000.0, "category_slug": "tech"},
    {"title": "Clean Architecture", "author": "Robert C. Martin", "isbn": "9780134494166", "price": 350000.0, "category_slug": "tech"},
    {"title": "The Pragmatic Programmer", "author": "Andrew Hunt", "isbn": "9780201616224", "price": 420000.0, "category_slug": "tech"},
    {"title": "Refactoring", "author": "Martin Fowler", "isbn": "9780201485677", "price": 420000.0, "category_slug": "tech"},
    {"title": "Design Patterns", "author": "Erich Gamma", "isbn": "9780201633610", "price": 450000.0, "category_slug": "tech"},
    {"title": "Head First Design Patterns", "author": "Eric Freeman", "isbn": "9780596007126", "price": 350000.0, "category_slug": "tech"},
    {"title": "Python Crash Course", "author": "Eric Matthes", "isbn": "9781593276034", "price": 280000.0, "category_slug": "tech"},
    {"title": "Fluent Python", "author": "Luciano Ramalho", "isbn": "9781491946008", "price": 450000.0, "category_slug": "tech"},
    {"title": "Introduction to Algorithms", "author": "Thomas H. Cormen", "isbn": "9780262033848", "price": 600000.0, "category_slug": "tech"},
    {"title": "Grokking Algorithms", "author": "Aditya Bhargava", "isbn": "9781617292231", "price": 250000.0, "category_slug": "tech"},
    {"title": "Domain-Driven Design", "author": "Eric Evans", "isbn": "9780321125217", "price": 500000.0, "category_slug": "tech"},
    {"title": "Computer Systems", "author": "Randal E. Bryant", "isbn": "9780134092669", "price": 550000.0, "category_slug": "tech"},
    {"title": "Operating System Concepts", "author": "Abraham Silberschatz", "isbn": "9781118063330", "price": 500000.0, "category_slug": "tech"},
    {"title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "isbn": "9781449373320", "price": 480000.0, "category_slug": "tech"},
    {"title": "Site Reliability Engineering", "author": "Niall Richard Murphy", "isbn": "9781491929124", "price": 380000.0, "category_slug": "tech"},

    # Science (slug: science)
    {"title": "A Brief History of Time", "author": "Stephen Hawking", "isbn": "9780553380163", "price": 250000.0, "category_slug": "science"},
    {"title": "Cosmos", "author": "Carl Sagan", "isbn": "9780345331359", "price": 280000.0, "category_slug": "science"},
    {"title": "The Selfish Gene", "author": "Richard Dawkins", "isbn": "9780199291151", "price": 250000.0, "category_slug": "science"},
    {"title": "What If?", "author": "Randall Munroe", "isbn": "9780544272996", "price": 220000.0, "category_slug": "science"},
    {"title": "Astrophysics for People in a Hurry", "author": "Neil deGrasse Tyson", "isbn": "9780393609394", "price": 180000.0, "category_slug": "science"},

    # Fiction (slug: fiction)
    {"title": "1984", "author": "George Orwell", "isbn": "9780451524935", "price": 150000.0, "category_slug": "fiction"},
    {"title": "Animal Farm", "author": "George Orwell", "isbn": "9780451526342", "price": 120000.0, "category_slug": "fiction"},
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "isbn": "9780060935467", "price": 180000.0, "category_slug": "fiction"},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "isbn": "9780743273565", "price": 150000.0, "category_slug": "fiction"},
    {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593", "price": 250000.0, "category_slug": "fiction"},

    # Business (slug: business)
    {"title": "Zero to One", "author": "Peter Thiel", "isbn": "9780804139298", "price": 220000.0, "category_slug": "business"},
    {"title": "The Lean Startup", "author": "Eric Ries", "isbn": "9780307887894", "price": 250000.0, "category_slug": "business"},
    {"title": "Good to Great", "author": "Jim Collins", "isbn": "9780066620992", "price": 260000.0, "category_slug": "business"},
    {"title": "Atomic Habits", "author": "James Clear", "isbn": "9780735211292", "price": 200000.0, "category_slug": "business"},
    {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "isbn": "9780374533557", "price": 300000.0, "category_slug": "business"},
]


def seed_database():
    """Seed categories and books if tables are empty."""
    cat_map = {}
    for cat_data in CATEGORIES_DATA:
        cat = Category.query.filter_by(slug=cat_data["slug"]).first()
        if not cat:
            cat = Category(name=cat_data["name"], slug=cat_data["slug"])
            db.session.add(cat)
            db.session.flush()
        cat_map[cat.slug] = cat

    for b in BOOKS_DATA:
        book = Book.query.filter_by(isbn=b["isbn"]).first()
        if not book:
            cat = cat_map[b["category_slug"]]
            book = Book(
                title=b["title"],
                author=b["author"],
                isbn=b["isbn"],
                price_vnd=b["price"],
                category_id=cat.id,
            )
            db.session.add(book)

    db.session.commit()
    print("Database seeding completed.")


if __name__ == "__main__":
    from app import create_app
    app = create_app("development")
    with app.app_context():
        db.create_all()
        seed_database()
