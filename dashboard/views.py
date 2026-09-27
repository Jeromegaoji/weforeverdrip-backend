"""
Admin dashboard API views for analytics and management.
All views require IsStaffOrAdmin permission.
"""
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Sum, F, Q, Avg, Case, When, DecimalField
from django.db.models.functions import TruncDate, Coalesce
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter

from .permissions import IsStaffOrAdmin
from .serializers import (
    DashboardStatsSerializer,
    RecentOrderSerializer,
    LowStockSerializer,
    TopProductSerializer,
    OrderStatusBreakdownSerializer,
    RevenueByDaySerializer,
    CustomerSerializer,
    AdminOrderDetailSerializer,
)
from orders.models import Order, OrderItem, Cart
from products.models import ProductVariant, Product
from drops.models import Drop
from users.models import User


class StandardPagination(PageNumberPagination):
    """Standard pagination for admin list views."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DashboardStatsView(APIView):
    """
    GET: Return dashboard statistics and key metrics.
    Includes orders, revenue, customers, products, and drops info.
    """
    permission_classes = [IsStaffOrAdmin]
    
    def get(self, request):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Orders
        total_orders_today = Order.objects.filter(
            created_at__gte=today_start
        ).count()
        
        total_orders_this_week = Order.objects.filter(
            created_at__gte=week_start
        ).count()
        
        total_orders_this_month = Order.objects.filter(
            created_at__gte=month_start
        ).count()
        
        # Revenue (paid orders only)
        revenue_today = Order.objects.filter(
            created_at__gte=today_start,
            payment_status='paid'
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        revenue_this_week = Order.objects.filter(
            created_at__gte=week_start,
            payment_status='paid'
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        revenue_this_month = Order.objects.filter(
            created_at__gte=month_start,
            payment_status='paid'
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        # Customers
        total_customers = User.objects.filter(is_staff=False).count()
        new_customers_this_month = User.objects.filter(
            is_staff=False,
            date_joined__gte=month_start
        ).count()
        
        # Products
        total_products = Product.objects.count()
        low_stock_count = ProductVariant.objects.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=5
        ).count()
        out_of_stock_count = ProductVariant.objects.filter(
            stock_quantity=0
        ).count()
        
        # Orders status
        pending_orders = Order.objects.filter(status='pending').count()
        
        # Drops
        active_drops = Drop.objects.filter(
            status='live',
            is_published=True
        ).count()
        
        stats_data = {
            'total_orders_today': total_orders_today,
            'total_orders_this_week': total_orders_this_week,
            'total_orders_this_month': total_orders_this_month,
            'revenue_today': revenue_today,
            'revenue_today_naira': revenue_today / 100,
            'revenue_this_week': revenue_this_week,
            'revenue_this_week_naira': revenue_this_week / 100,
            'revenue_this_month': revenue_this_month,
            'revenue_this_month_naira': revenue_this_month / 100,
            'total_customers': total_customers,
            'new_customers_this_month': new_customers_this_month,
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'pending_orders': pending_orders,
            'active_drops': active_drops,
        }
        
        serializer = DashboardStatsSerializer(stats_data)
        return Response(serializer.data)


class RecentOrdersView(ListAPIView):
    """
    GET: Return the 10 most recent orders.
    """
    permission_classes = [IsStaffOrAdmin]
    serializer_class = RecentOrderSerializer
    
    def get_queryset(self):
        return Order.objects.select_related('user').order_by('-created_at')[:10]


class LowStockView(ListAPIView):
    """
    GET: Return all product variants with stock <= 10.
    Ordered by stock quantity ascending (most critical first).
    """
    permission_classes = [IsStaffOrAdmin]
    serializer_class = LowStockSerializer
    pagination_class = StandardPagination
    
    def get_queryset(self):
        return ProductVariant.objects.select_related('product').filter(
            stock_quantity__lte=10
        ).order_by('stock_quantity')


class TopProductsView(APIView):
    """
    GET: Return the top 10 best-selling products.
    Includes total units sold and total revenue per product.
    """
    permission_classes = [IsStaffOrAdmin]
    
    def get(self, request):
        top_products = OrderItem.objects.values('product_name').annotate(
            total_units_sold=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('unit_price'), output_field=DecimalField())
        ).order_by('-total_units_sold')[:10]
        
        data = []
        for item in top_products:
            product_name = item['product_name']
            try:
                product = Product.objects.get(name=product_name)
                slug = product.slug
            except Product.DoesNotExist:
                slug = None
            
            total_revenue = int(item['total_revenue'] or 0)
            data.append({
                'product_name': product_name,
                'product_slug': slug,
                'total_units_sold': item['total_units_sold'],
                'total_revenue': total_revenue,
                'total_revenue_naira': total_revenue / 100,
            })
        
        page = StandardPagination()
        page.page_size = 10
        paginated_data = page.paginate_queryset(data, request)
        serializer = TopProductSerializer(paginated_data, many=True)
        return page.get_paginated_response(serializer.data)


class OrderStatusBreakdownView(APIView):
    """
    GET: Return order count and total value for each order status.
    """
    permission_classes = [IsStaffOrAdmin]
    
    def get(self, request):
        breakdown = Order.objects.values('status').annotate(
            count=Count('id'),
            total_value=Sum('total')
        ).order_by('status')
        
        data = [
            {
                'status': item['status'],
                'count': item['count'],
                'total_value': item['total_value'] or 0,
                'total_value_naira': (item['total_value'] or 0) / 100,
            }
            for item in breakdown
        ]
        
        serializer = OrderStatusBreakdownSerializer(data, many=True)
        return Response(serializer.data)


class RevenueByDayView(APIView):
    """
    GET: Return daily revenue for the last 30 days.
    Only counts paid orders.
    """
    permission_classes = [IsStaffOrAdmin]
    
    def get(self, request):
        now = timezone.now()
        start_date = (now - timedelta(days=30)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        daily_revenue = Order.objects.filter(
            created_at__gte=start_date,
            payment_status='paid'
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            order_count=Count('id'),
            revenue=Sum('total')
        ).order_by('date')
        
        data = [
            {
                'date': item['date'],
                'order_count': item['order_count'],
                'revenue': item['revenue'] or 0,
                'revenue_naira': (item['revenue'] or 0) / 100,
            }
            for item in daily_revenue
        ]
        
        serializer = RevenueByDaySerializer(data, many=True)
        return Response(serializer.data)


class AdminOrderListView(ListAPIView):
    """
    GET: Return all orders (admin can see all orders, not filtered by user).
    Supports filtering by status, payment_status, and date range.
    Paginated (20 per page).
    """
    permission_classes = [IsStaffOrAdmin]
    serializer_class = RecentOrderSerializer
    pagination_class = StandardPagination
    filter_backends = [OrderingFilter]
    
    def get_queryset(self):
        queryset = Order.objects.select_related('user').order_by('-created_at')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by payment_status
        payment_status_filter = self.request.query_params.get('payment_status')
        if payment_status_filter:
            queryset = queryset.filter(payment_status=payment_status_filter)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__gte=date_from_obj)
            except (ValueError, TypeError):
                pass
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
                date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
                queryset = queryset.filter(created_at__lte=date_to_obj)
            except (ValueError, TypeError):
                pass
        
        return queryset


class AdminOrderDetailView(RetrieveAPIView):
    """
    GET: Return full order detail by order_number.
    Admin can view any order.
    """
    permission_classes = [IsStaffOrAdmin]
    serializer_class = AdminOrderDetailSerializer
    lookup_field = 'order_number'
    
    def get_queryset(self):
        return Order.objects.select_related('user')


class AdminUpdateOrderStatusView(UpdateAPIView):
    """
    PATCH: Update order status by order_number.
    Allowed transitions: pending → confirmed → shipped → delivered
    Any status → cancelled (but restore stock if cancelling).
    """
    permission_classes = [IsStaffOrAdmin]
    serializer_class = AdminOrderDetailSerializer
    lookup_field = 'order_number'
    http_method_names = ['patch']
    
    def get_queryset(self):
        return Order.objects.select_related('user')
    
    def get_object(self):
        queryset = self.get_queryset()
        order_number = self.kwargs.get('order_number')
        return queryset.get(order_number=order_number)
    
    def patch(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate transitions
        allowed_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        if new_status not in allowed_statuses:
            return Response(
                {'error': f'Invalid status. Allowed: {", ".join(allowed_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate transition logic
        current_status = order.status
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['shipped', 'cancelled'],
            'shipped': ['delivered', 'cancelled'],
            'delivered': ['cancelled'],
            'cancelled': [],
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            return Response(
                {'error': f'Cannot transition from {current_status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If cancelling, restore stock using the FK on each OrderItem.
        # item.variant is the exact variant that was purchased — size, colour,
        # everything. This is the correct approach. The previous code used
        # product__name + .first() which would restore stock to the wrong
        # variant whenever a product has multiple sizes or colours.
        if new_status == 'cancelled':
            from django.db import transaction as db_transaction
            with db_transaction.atomic():
                for item in order.items.select_related('variant').select_for_update():
                    if item.variant is not None:
                        item.variant.stock_quantity += item.quantity
                        item.variant.save(update_fields=['stock_quantity'])
        
        order.status = new_status
        order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)


class AdminInventoryView(ListAPIView):
    """
    GET: Return all product variants with stock info.
    Supports filtering by ?low_stock=true (stock <= 10).
    Paginated.
    """
    permission_classes = [IsStaffOrAdmin]
    serializer_class = LowStockSerializer
    pagination_class = StandardPagination
    
    def get_queryset(self):
        queryset = ProductVariant.objects.select_related('product').order_by('stock_quantity')
        
        # Filter by low stock
        low_stock_filter = self.request.query_params.get('low_stock')
        if low_stock_filter and low_stock_filter.lower() == 'true':
            queryset = queryset.filter(stock_quantity__lte=10)
        
        return queryset


class AdminInventoryUpdateView(UpdateAPIView):
    """
    PATCH: Update product variant stock by variant pk.
    """
    permission_classes = [IsStaffOrAdmin]
    serializer_class = LowStockSerializer
    queryset = ProductVariant.objects.select_related('product')
    http_method_names = ['patch']
    
    def patch(self, request, *args, **kwargs):
        variant = self.get_object()
        new_stock = request.data.get('stock_quantity')
        
        if new_stock is None:
            return Response(
                {'error': 'stock_quantity field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_stock = int(new_stock)
            if new_stock < 0:
                return Response(
                    {'error': 'stock_quantity must be >= 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'stock_quantity must be an integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        variant.stock_quantity = new_stock
        variant.save()
        
        serializer = self.get_serializer(variant)
        return Response(serializer.data)


class AdminCustomerListView(ListAPIView):
    """
    GET: Return all customers (non-staff users).
    Annotate with total_orders and total_spent.
    Supports search by email, first_name, last_name.
    Paginated.
    """
    permission_classes = [IsStaffOrAdmin]
    serializer_class = CustomerSerializer
    pagination_class = StandardPagination
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name']
    ordering_fields = ['date_joined']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        queryset = User.objects.filter(is_staff=False).annotate(
            total_orders=Count(
                'orders',
                filter=Q(orders__isnull=False),
                distinct=True
            ),
            total_spent=Coalesce(
                Sum(
                    'orders__total',
                    filter=Q(orders__payment_status='paid')
                ),
                0
            )
        ).order_by('-date_joined')
        
        return queryset


class AdminCustomerDetailView(APIView):
    """
    GET: Return customer profile + their last 5 orders.
    """
    permission_classes = [IsStaffOrAdmin]
    
    def get(self, request, pk):
        try:
            customer = User.objects.get(pk=pk, is_staff=False)
        except User.DoesNotExist:
            return Response(
                {'error': 'Customer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Annotate customer with aggregates
        customer = User.objects.filter(pk=pk).annotate(
            total_orders=Count('orders', distinct=True),
            total_spent=Coalesce(
                Sum('orders__total', filter=Q(orders__payment_status='paid')),
                0
            )
        ).first()
        
        # Get last 5 orders
        recent_orders = customer.orders.select_related('user').order_by('-created_at')[:5]
        
        customer_serializer = CustomerSerializer(customer)
        orders_serializer = RecentOrderSerializer(recent_orders, many=True)
        
        data = {
            'customer': customer_serializer.data,
            'recent_orders': orders_serializer.data,
        }
        
        return Response(data)


class ConfirmPaymentView(APIView):
    """
    POST: Admin confirms that a bank transfer has been received for an order.
    Called after the customer sends WhatsApp proof of payment.
    Sets payment_status → 'paid' and order status → 'confirmed'.

    Endpoint: POST /api/v1/admin/orders/{order_number}/confirm-payment/
    Permission: IsStaffOrAdmin
    """
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)

        if order.status == 'cancelled':
            return Response(
                {'detail': 'Cannot confirm payment for a cancelled order.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if order.payment_status == 'paid':
            return Response(
                {'detail': f'Order {order_number} is already marked as paid.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save(update_fields=['payment_status', 'status', 'updated_at'])

        return Response({
            'message': f'Payment confirmed for order {order_number}.',
            'order': AdminOrderDetailSerializer(order).data,
        })
