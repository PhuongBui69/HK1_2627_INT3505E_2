from sqlalchemy.exc import OperationalError

from product_api.extensions import db


def test_healthz_and_ready(client):
    assert client.get("/healthz").get_json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "checks": {"db": "ok"}}


def test_db_failure_only_affects_readiness(client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("DB unavailable"))

    monkeypatch.setattr(db.session, "execute", unavailable)
    assert client.get("/healthz").status_code == 200
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.get_json() == {"status": "degraded", "checks": {"db": "err"}}


def test_openapi_and_swagger(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.get_json()
    assert spec["openapi"] == "3.0.3"
    assert "post" in spec["paths"]["/api/v1/products/{product_id}/reserve"]
    assert "post" in spec["paths"]["/api/v1/orders"]
    assert client.get("/docs").status_code == 200
