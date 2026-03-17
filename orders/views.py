from django.db import transaction
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.http import Http404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests

from users.models import Address
from products.models import ProductVariant
from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    PlaceOrderSerializer,
    OrderSerializer,
    OrderDetailSerializer,
)


class CartView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartView(generics.GenericAPIView):
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = serializer.validated_data['variant_id']
        quantity = serializer.validated_data['quantity']
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, defaults={'quantity': quantity})
        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > variant.stock_quantity:
                return Response({'detail': 'Requested quantity exceeds available stock.'}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_quantity
            cart_item.save()

        return Response(CartSerializer(cart).data)


class UpdateCartItemView(generics.GenericAPIView):
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]
    queryset = CartItem.objects.all()
    lookup_field = 'pk'

    def patch(self, request, *args, **kwargs):
        cart_item = self.get_object()
        if cart_item.cart.user != request.user:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        quantity = request.data.get('quantity')
        if quantity is None:
            return Response({'quantity': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)
        quantity = int(quantity)
        if quantity < 0:
            return Response({'quantity': 'Quantity must be 0 or greater.'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity > cart_item.variant.stock_quantity:
            return Response({'detail': 'Not enough stock.'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity == 0:
            cart_item.delete()
            cart = cart_item.cart
            return Response(CartSerializer(cart).data)
        cart_item.quantity = quantity
        cart_item.save()
        cart = cart_item.cart
        return Response(CartSerializer(cart).data)

    def delete(self, request, *args, **kwargs):
        cart_item = self.get_object()
        if cart_item.cart.user != request.user:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        cart = cart_item.cart
        cart_item.delete()
        return Response(CartSerializer(cart).data)


class ClearCartView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)


class PlaceOrderView(generics.GenericAPIView):
    serializer_class = PlaceOrderSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for item in cart.items.select_related('variant__product'):
                if item.quantity > item.variant.stock_quantity:
                    return Response({'detail': f'Insufficient stock for {item.variant.sku}.'}, status=status.HTTP_400_BAD_REQUEST)

            address = serializer.validated_data['shipping_address_id']
            notes = serializer.validated_data.get('notes', '')

            order = Order.objects.create(
                user=request.user,
                shipping_address=address,
                shipping_address_snapshot={
                    'street': address.street,
                    'city': address.city,
                    'state': address.state,
                    'country': address.country,
                },
                notes=notes,
                payment_status='unpaid',
                status='pending',
            )

            subtotal = 0
            for item in cart.items.select_related('variant__product'):
                variant = item.variant
                order_item = OrderItem.objects.create(
                    order=order,
                    variant=variant,
                    product_name=variant.product.name,
                    variant_info=f"{variant.size} / {variant.colour}",
                    sku=variant.sku,
                    quantity=item.quantity,
                    unit_price=variant.product.price,
                )
                subtotal += order_item.subtotal
                variant.stock_quantity -= item.quantity
                variant.save()

            order.subtotal = subtotal
            order.total = subtotal + order.shipping_fee
            order.save()
            cart.items.all().delete()

        return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class CancelOrderView(generics.GenericAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        if order.status != 'pending':
            return Response({'detail': 'Only pending orders can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order.status = 'cancelled'
            order.save()
            for item in order.items.select_related('variant'):
                if item.variant:
                    item.variant.stock_quantity += item.quantity
                    item.variant.save()

        return Response(OrderDetailSerializer(order).data)


class InitiatePaystackPaymentView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        if order.payment_status != 'unpaid':
            return Response({'detail': 'Order is already paid.'}, status=status.HTTP_400_BAD_REQUEST)

        paystack_secret = settings.PAYSTACK_SECRET_KEY
        if not paystack_secret:
            return Response({'detail': 'Paystack key not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            response = requests.post(
                'https://api.paystack.co/transaction/initialize',
                headers={'Authorization': f'Bearer {paystack_secret}'},
                json={
                    'email': request.user.email,
                    'amount': order.total,
                    'reference': order.order_number,
                    'callback_url': 'http://localhost:3000/order/verify',
                },
                timeout=20,
            )
            response_data = response.json()
            if response.status_code != 200 or not response_data.get('status'):
                return Response({'detail': 'Paystack initialization failed.', 'error': response_data}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'authorization_url': response_data['data']['authorization_url'], 'reference': response_data['data']['reference']})
        except requests.RequestException:
            return Response({'detail': 'Error communicating with Paystack.'}, status=status.HTTP_502_BAD_GATEWAY)


class VerifyPaystackPaymentView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, reference):
        paystack_secret = settings.PAYSTACK_SECRET_KEY
        if not paystack_secret:
            return Response({'detail': 'Paystack key not configured.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            response = requests.get(
                f'https://api.paystack.co/transaction/verify/{reference}',
                headers={'Authorization': f'Bearer {paystack_secret}'},
                timeout=20,
            )
            data = response.json()
            if response.status_code != 200 or not data.get('status'):
                return Response({'detail': 'Payment verification failed.', 'error': data}, status=status.HTTP_400_BAD_REQUEST)

            paystack_data = data.get('data', {})
            if paystack_data.get('status') == 'success':
                order = Order.objects.filter(order_number=reference).first()
                if not order:
                    order = Order.objects.filter(payment_reference=reference).first()
                if not order:
                    return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.payment_reference = reference
                order.save()
                return Response(OrderDetailSerializer(order).data)
            return Response({'detail': 'Payment not successful.'}, status=status.HTTP_400_BAD_REQUEST)
        except requests.RequestException:
            return Response({'detail': 'Error communicating with Paystack.'}, status=status.HTTP_502_BAD_GATEWAY)
