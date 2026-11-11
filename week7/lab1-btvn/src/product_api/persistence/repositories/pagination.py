from sqlalchemy import func, select

from ...extensions import db


def paginate(stmt, model, page, size):
    total = db.session.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    items = db.session.scalars(stmt.order_by(model.id).offset((page - 1) * size).limit(size)).all()
    return {"items": items, "page": page, "size": size, "total": total}
