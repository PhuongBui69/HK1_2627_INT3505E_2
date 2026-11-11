class BusinessError(Exception):
    """Lỗi nghiệp vụ; không phụ thuộc Flask hay HTTP status."""

    code = "business_error"


class NotFoundError(BusinessError):
    code = "not_found"


class ConflictError(BusinessError):
    code = "conflict"


class OutOfStockError(ConflictError):
    code = "out_of_stock"
