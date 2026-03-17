from django.urls import path
from .views import (
    AddProductToDropView,
    DropActivateView,
    DropDetailView,
    DropListView,
    LiveDropsView,
    UpcomingDropsView,
    RemoveProductFromDropView,
)

urlpatterns = [
    path('', DropListView.as_view(), name='drop-list'),
    path('live/', LiveDropsView.as_view(), name='drop-live-list'),
    path('upcoming/', UpcomingDropsView.as_view(), name='drop-upcoming-list'),
    path('<slug:slug>/', DropDetailView.as_view(), name='drop-detail'),
    path('<slug:slug>/activate/', DropActivateView.as_view(), name='drop-activate'),
    path('<slug:slug>/products/', AddProductToDropView.as_view(), name='drop-add-product'),
    path('<slug:slug>/products/<int:pk>/', RemoveProductFromDropView.as_view(), name='drop-remove-product'),
]
