from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from orders.models import Orders
from app.permission import IsAdminUser, IsVendorUser
from app.utils.response import APIResponse

class GetMyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Orders.objects.filter(user=request.user)

        return APIResponse.success(data= orders, message="Get my orders")

class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        order = Orders.objects.get(id=id, user=request.user)
        if order.status != 'pending':
            return APIResponse.error(message= "Only pending orders can be canceled.")
        order.status = 'canceled'
        order.save()
        return APIResponse.success(message= "Order canceled successfully!")

class GetVendorOrdersView(APIView):
    permission_classes = [IsVendorUser]

    def get(self, request):
        orders = Orders.objects.filter(order_items__shop=request.user.shop)

        return APIResponse.success(data= orders, message="Get shop's all orders")

class UpdateOrderStatusView(APIView):
    permission_classes = [IsVendorUser] 

    def patch(self, request, id):
        order = Orders.objects.get(id=id)
        order.status = request.data.get('status', order.status)
        order.save()
        return APIResponse.success(message= "Order status updated.")

class GetAllOrdersForAdminView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        orders = Orders.objects.all()
        
        return APIResponse.success(data= orders, message="Retrived all orders")
