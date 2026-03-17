from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Drop, DropProduct
from .serializers import (
    AddProductToDropSerializer,
    DropDetailSerializer,
    DropSerializer,
    DropWriteSerializer,
)


class DropListView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        drops = Drop.objects.filter(is_published=True).exclude(status__in=['draft', 'cancelled']).order_by('-launch_date')
        serializer = DropSerializer(drops, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DropWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        drop = serializer.save()
        return Response(DropDetailSerializer(drop).data, status=status.HTTP_201_CREATED)


class DropDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request, slug):
        drop = get_object_or_404(Drop, slug=slug, is_published=True)
        serializer = DropDetailSerializer(drop)
        return Response(serializer.data)

    def patch(self, request, slug):
        drop = get_object_or_404(Drop, slug=slug)
        if not request.user.is_staff:
            return Response({'detail': 'Admin privileges required.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = DropWriteSerializer(drop, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        drop = serializer.save()
        return Response(DropDetailSerializer(drop).data)


class LiveDropsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        drops = Drop.objects.filter(status='live', is_published=True).order_by('-launch_date')
        serializer = DropSerializer(drops, many=True)
        return Response(serializer.data)


class UpcomingDropsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        now = timezone.now()
        drops = Drop.objects.filter(
            status='scheduled',
            is_published=True,
            launch_date__gt=now,
        ).order_by('launch_date')
        serializer = DropSerializer(drops, many=True)
        return Response(serializer.data)


class DropCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = DropWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        drop = serializer.save()
        detail = DropDetailSerializer(drop)
        return Response(detail.data, status=status.HTTP_201_CREATED)


class DropActivateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, slug):
        drop = get_object_or_404(Drop, slug=slug)
        if drop.status in ['live', 'ended', 'cancelled']:
            return Response(
                {'detail': 'Cannot activate drop in its current status.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        drop.activate()
        return Response(DropDetailSerializer(drop).data)


class AddProductToDropView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, slug):
        drop = get_object_or_404(Drop, slug=slug)
        serializer = AddProductToDropSerializer(data=request.data, context={'drop': drop})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        DropProduct.objects.create(
            drop=drop,
            product=data['product'],
            drop_price=data['drop_price'],
            quantity_limit=data.get('quantity_limit'),
        )
        return Response(DropDetailSerializer(drop).data, status=status.HTTP_201_CREATED)


class RemoveProductFromDropView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, slug, pk):
        drop = get_object_or_404(Drop, slug=slug)
        drop_product = get_object_or_404(DropProduct, drop=drop, product_id=pk)
        drop_product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
