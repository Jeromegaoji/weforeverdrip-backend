from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.CartView.as_view(), name='cart-view'),
    path('cart/add/', views.AddToCartView.as_view(), name='cart-add'),
    path('cart/item/<int:pk>/', views.UpdateCartItemView.as_view(), name='cart-item-detail'),
    path('cart/clear/', views.ClearCartView.as_view(), name='cart-clear'),
    path('place/', views.PlaceOrderView.as_view(), name='place-order'),
    path('', views.OrderListView.as_view(), name='order-list'),
    path('<str:order_number>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('<str:order_number>/cancel/', views.CancelOrderView.as_view(), name='order-cancel'),
    path('<str:order_number>/pay/paystack/', views.InitiatePaystackPaymentView.as_view(), name='order-paystack'),
    path('verify/paystack/<str:reference>/', views.VerifyPaystackPaymentView.as_view(), name='order-paystack-verify'),
]
