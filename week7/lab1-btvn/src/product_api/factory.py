from pathlib import Path

from flask import Flask
from flask_smorest import Api

from .api.hooks import register_request_hooks
from .config import Config
from .exceptions.handlers import register_error_handlers
from .extensions import db, migrate
from .schemas.common import ErrorSchema


class ProductApi(Api):
    ERROR_SCHEMA = ErrorSchema


def create_app(config=None):
    app = Flask(__name__, instance_path=str(Path.cwd() / "instance"))
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.logger.setLevel(app.config["LOG_LEVEL"])

    db.init_app(app)
    migrate.init_app(app, db)

    from .api import health, orders, products

    api = ProductApi(app)
    api.register_blueprint(products.blp)
    api.register_blueprint(orders.blp)
    app.register_blueprint(health.blp)

    register_request_hooks(app)
    # Đăng ký sau Api để thống nhất lỗi về {error, detail} theo Lab 1.
    register_error_handlers(app)
    return app
