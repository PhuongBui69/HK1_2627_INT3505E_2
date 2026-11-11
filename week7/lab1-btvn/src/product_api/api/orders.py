from flask.views import MethodView
from flask_smorest import Blueprint

from ..schemas.common import PaginationIn
from ..schemas.orders import OrderIn, OrderOut, OrderPage
from ..services import orders as order_service

blp = Blueprint("orders", __name__, url_prefix="/api/v1/orders", description="Order và OrderItem")


@blp.route("")
class OrderList(MethodView):
    @blp.arguments(PaginationIn, location="query")
    @blp.response(200, OrderPage)
    def get(self, args):
        """Danh sách đơn kèm items và products, dùng eager loading."""
        return order_service.list_orders(**args)

    @blp.arguments(OrderIn)
    @blp.response(201, OrderOut)
    @blp.alt_response(404, description="Sản phẩm không tồn tại")
    @blp.alt_response(409, description="Không đủ tồn kho")
    def post(self, data):
        """Tạo đơn có nhiều OrderItem và trừ tồn kho trong một transaction."""
        return order_service.create_order(data["items"])


@blp.route("/<int:order_id>")
class OrderDetail(MethodView):
    @blp.response(200, OrderOut)
    @blp.alt_response(404, description="Không tìm thấy đơn hàng")
    def get(self, order_id):
        """Chi tiết đơn kèm items và products, dùng eager loading."""
        return order_service.get_order(order_id)
