"""
URL configuration for dashboard admin API endpoints.
All endpoints require IsStaffOrAdmin permission.
"""
from django.urls import path
from .views import (
    DashboardStatsView,
    RecentOrdersView,
    LowStockView,
    TopProductsView,
    OrderStatusBreakdownView,
    RevenueByDayView,
    AdminOrderListView,
    AdminOrderDetailView,
    AdminUpdateOrderStatusView,
    AdminInventoryView,
    AdminInventoryUpdateView,
    AdminCustomerListView,
    AdminCustomerDetailView,
)

urlpatterns = [
    # Dashboard stats and analytics
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/orders/recent/', RecentOrdersView.as_view(), name='dashboard-recent-orders'),
    path('dashboard/low-stock/', LowStockView.as_view(), name='dashboard-low-stock'),
    path('dashboard/top-products/', TopProductsView.as_view(), name='dashboard-top-products'),
    path('dashboard/order-breakdown/', OrderStatusBreakdownView.as_view(), name='dashboard-order-breakdown'),
    path('dashboard/revenue/', RevenueByDayView.as_view(), name='dashboard-revenue'),
    
    # Admin orders management
    path('orders/', AdminOrderListView.as_view(), name='admin-orders-list'),
    path('orders/<str:order_number>/', AdminOrderDetailView.as_view(), name='admin-orders-detail'),
    path('orders/<str:order_number>/status/', AdminUpdateOrderStatusView.as_view(), name='admin-orders-update-status'),
    
    # Admin inventory management
    path('inventory/', AdminInventoryView.as_view(), name='admin-inventory-list'),
    path('inventory/<int:pk>/', AdminInventoryUpdateView.as_view(), name='admin-inventory-update'),
    
    # Admin customer management
    path('customers/', AdminCustomerListView.as_view(), name='admin-customers-list'),
    path('customers/<int:pk>/', AdminCustomerDetailView.as_view(), name='admin-customers-detail'),
]
