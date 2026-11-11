from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ...extensions import db


def database_available():
    try:
        db.session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.session.rollback()
        return False
    return True
