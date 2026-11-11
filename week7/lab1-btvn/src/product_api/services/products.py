from ..exceptions.business import ConflictError, NotFoundError, OutOfStockError
from ..persistence.models import Product
from ..persistence.repositories import products as product_repository
from ..persistence.transaction import PersistenceConflictError, transaction


def list_products(page, size):
    return product_repository.list_active(page, size)


def get_product(product_id):
    product = product_repository.find_active(product_id)
    if product is None:
        raise NotFoundError("Không tìm thấy sản phẩm.")
    return product


def create_product(data):
    product = Product(**data)
    try:
        with transaction():
            product_repository.add(product)
    except PersistenceConflictError:
        raise ConflictError("SKU đã tồn tại.") from None
    return product


def update_product(product_id, data):
    product = get_product(product_id)
    try:
        with transaction():
            for key, value in data.items():
                setattr(product, key, value)
    except PersistenceConflictError:
        raise ConflictError("SKU đã tồn tại.") from None
    return product


def delete_product(product_id):
    product = get_product(product_id)
    with transaction():
        product.archived = True


def decrease_stock(product_id, qty):
    """Dùng trong transaction của reserve hoặc tạo đơn; không tự commit."""
    if not product_repository.decrease_stock(product_id, qty):
        raise OutOfStockError(f"Sản phẩm {product_id} không đủ tồn kho.")


def reserve_product(product_id, qty):
    product = get_product(product_id)
    with transaction():
        decrease_stock(product_id, qty)
    return product
