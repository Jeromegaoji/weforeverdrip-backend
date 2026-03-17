from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product-list-create'),
    path('featured/', views.FeaturedProductsView.as_view(), name='featured-products'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product-detail-update-delete'),
    path('variants/<int:pk>/', views.ProductVariantUpdateView.as_view(), name='product-variant-update'),
]
