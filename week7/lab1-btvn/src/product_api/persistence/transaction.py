from contextlib import contextmanager

from sqlalchemy.exc import IntegrityError

from ..extensions import db


class PersistenceConflictError(Exception):
    """Vi phạm constraint của DB, để service chuyển thành lỗi nghiệp vụ."""


@contextmanager
def transaction():
    """Service quyết định phạm vi transaction; repository không tự commit."""
    try:
        yield
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        raise PersistenceConflictError("Database constraint violation") from error
    except Exception:
        db.session.rollback()
        raise
