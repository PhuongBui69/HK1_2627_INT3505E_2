from flask.views import MethodView
from flask_smorest import Blueprint
from ..schemas.common import PaginationIn
from ..schemas.products import ProductIn, ProductOut, ProductPage, ProductPatch, ReserveIn
from ..services import products as product_service

blp = Blueprint("products", __name__, url_prefix="/api/v1/products", description="Product CRUD")


@blp.route("")
class ProductList(MethodView):
    @blp.arguments(PaginationIn, location="query")
    @blp.response(200, ProductPage)
    def get(self, args):
        """Danh sách sản phẩm chưa bị xóa, có phân trang."""
        return product_service.list_products(**args)

    @blp.arguments(ProductIn)
    @blp.response(201, ProductOut)
    @blp.alt_response(409, description="SKU đã tồn tại")
    def post(self, data):
        """Tạo sản phẩm."""
        return product_service.create_product(data)


@blp.route("/<int:product_id>")
class ProductDetail(MethodView):
    @blp.response(200, ProductOut)
    @blp.alt_response(404, description="Không tìm thấy sản phẩm")
    def get(self, product_id):
        """Lấy một sản phẩm chưa bị xóa."""
        return product_service.get_product(product_id)

    @blp.arguments(ProductPatch(partial=True))
    @blp.response(200, ProductOut)
    @blp.alt_response(404, description="Không tìm thấy sản phẩm")
    @blp.alt_response(409, description="SKU đã tồn tại")
    def patch(self, data, product_id):
        """Chỉ cập nhật những field được gửi trong JSON."""
        return product_service.update_product(product_id, data)

    @blp.response(204)
    @blp.alt_response(404, description="Không tìm thấy sản phẩm")
    def delete(self, product_id):
        """Soft delete: đánh dấu archived, giữ lại lịch sử đơn hàng."""
        product_service.delete_product(product_id)


@blp.route("/<int:product_id>/reserve")
class ProductReserve(MethodView):
    @blp.arguments(ReserveIn)
    @blp.response(200, ProductOut)
    @blp.alt_response(404, description="Không tìm thấy sản phẩm")
    @blp.alt_response(409, description="Không đủ tồn kho")
    def post(self, data, product_id):
        """Đặt trước bằng cách giảm tồn kho."""
        return product_service.reserve_product(product_id, data["qty"])
