"""Lab 4: weighted tasks and 1% client-side simulated failures for year searches.

SIMULATED_500_CLIENT_SIDE is a Locust failure label, NOT an HTTP 500
returned by Flask. Actual non-200 responses are recorded separately.

Run: locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 \
         -u 10 -r 2 -t 30s --html reports/A.html
"""
import itertools
import random

from locust import HttpUser, between, task

_counter = itertools.count(1)


class BooksUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_books(self):
        self.client.get("/books", name="GET /books")

    @task(2)
    def read_book(self):
        book_id = random.randint(1, 50)
        with self.client.get(
            f"/books/{book_id}", name="GET /books/{id}", catch_response=True
        ) as response:
            # Expected 404 (random id absent) is not an operational failure.
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def create_book(self):
        unique = next(_counter)
        self.client.post(
            "/books",
            json={"title": f"Load test {unique}", "author": "locust",
                  "year": 2015 + unique % 10},
            name="POST /books",
        )

    @task(1)
    def search_by_year(self, year=None):
        year = year if year is not None else random.randint(2015, 2024)
        with self.client.get(
            "/books", params={"year": year}, name="GET /books?year",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected HTTP {response.status_code}")
                return
            try:
                books = response.json()
                if not isinstance(books, list) or any(
                    not isinstance(book, dict) or book.get("year") != year
                    for book in books
                ):
                    response.failure("Year search returned invalid or unfiltered data")
                    return
            except ValueError:
                response.failure("Year search returned invalid JSON")
                return
            if random.random() < 0.01:
                response.failure("SIMULATED_500_CLIENT_SIDE (actual HTTP 200)")
