from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.models import ProductVariant
from .models import Cart, CartItem, Order, OrderItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    PlaceOrderSerializer,
    OrderSerializer,
    OrderDetailSerializer,
)


# ──────────────────────────────────────────────────────────────
# Cart views
# ──────────────────────────────────────────────────────────────

class CartView(generics.RetrieveAPIView):
    """GET the current user's cart."""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart


class AddToCartView(generics.GenericAPIView):
    """POST to add a product variant to the cart."""
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        variant = serializer.validated_data['variant_id']
        quantity = serializer.validated_data['quantity']

        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={'quantity': quantity}
        )
        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > variant.stock_quantity:
                return Response(
                    {'detail': 'Requested quantity exceeds available stock.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()

        return Response(CartSerializer(cart).data)


class UpdateCartItemView(generics.GenericAPIView):
    """PATCH to update quantity. DELETE to remove item."""
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
            cart = cart_item.cart
            cart_item.delete()
            return Response(CartSerializer(cart).data)

        cart_item.quantity = quantity
        cart_item.save()
        return Response(CartSerializer(cart_item.cart).data)

    def delete(self, request, *args, **kwargs):
        cart_item = self.get_object()
        if cart_item.cart.user != request.user:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        cart = cart_item.cart
        cart_item.delete()
        return Response(CartSerializer(cart).data)


class ClearCartView(generics.DestroyAPIView):
    """DELETE to empty the entire cart."""
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)


# ──────────────────────────────────────────────────────────────
# Order views
# ──────────────────────────────────────────────────────────────

class PlaceOrderView(generics.GenericAPIView):
    """
    POST to place an order from the current cart.
    Returns order details + bank transfer instructions.
    Stock is deducted atomically with row-level locking to prevent
    overselling under concurrent requests.
    """
    serializer_class = PlaceOrderSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        cart, _ = Cart.objects.get_or_create(user=request.user)
        if not cart.items.exists():
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Lock all variants in one query before reading stock levels.
            # Any concurrent request trying to touch these rows will wait
            # until this transaction commits or rolls back.
            variant_ids = list(cart.items.values_list('variant_id', flat=True))
            locked_variants = {
                v.pk: v
                for v in ProductVariant.objects.select_for_update().filter(pk__in=variant_ids)
            }

            # Stock validation using the locked rows
            for item in cart.items.select_related('variant__product'):
                variant = locked_variants[item.variant.pk]
                if item.quantity > variant.stock_quantity:
                    return Response(
                        {'detail': f'Insufficient stock for {item.variant.product.name}.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            address = serializer.validated_data['shipping_address_id']
            notes = serializer.validated_data.get('notes', '')

            order = Order.objects.create(
                user=request.user,
                shipping_address=address,
                shipping_address_snapshot={
                    'street':  address.street,
                    'city':    address.city,
                    'state':   address.state,
                    'country': address.country,
                },
                notes=notes,
                payment_status='unpaid',
                status='pending',
                shipping_fee=settings.SHIPPING_FEE_KOBO,
            )

            subtotal = 0
            for item in cart.items.select_related('variant__product'):
                variant = locked_variants[item.variant.pk]
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

        # Attach bank transfer instructions to the response so the
        # frontend can display them immediately after checkout.
        response_data = OrderDetailSerializer(order).data
        response_data['payment_instructions'] = _build_transfer_instructions(order)
        return Response(response_data, status=status.HTTP_201_CREATED)


class BankTransferInfoView(APIView):
    """
    GET: Return bank transfer details for a specific unpaid order.
    Useful if the customer navigates away and needs the account number again.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        if order.payment_status != 'unpaid':
            return Response(
                {'detail': 'This order has already been paid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(_build_transfer_instructions(order))


class OrderListView(generics.ListAPIView):
    """GET list of the current user's orders."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class OrderDetailView(generics.RetrieveAPIView):
    """GET a single order by order_number."""
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class CancelOrderView(generics.GenericAPIView):
    """POST to cancel a pending order and restore stock."""
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
        if order.status != 'pending':
            return Response(
                {'detail': 'Only pending orders can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        with transaction.atomic():
            order.status = 'cancelled'
            order.save()
            for item in order.items.select_related('variant'):
                if item.variant:
                    item.variant.stock_quantity += item.quantity
                    item.variant.save()

        return Response(OrderDetailSerializer(order).data)


# ──────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────

def _build_transfer_instructions(order):
    """Build the bank transfer payload included in order responses."""
    bank = getattr(settings, 'BANK_TRANSFER_DETAILS', {})
    amount_naira = order.total / 100
    return {
        'bank_name':       bank.get('bank_name', ''),
        'account_name':    bank.get('account_name', ''),
        'account_number':  bank.get('account_number', ''),
        'whatsapp_number': bank.get('whatsapp_number', ''),
        'amount':          order.total,
        'amount_naira':    amount_naira,
        'reference':       order.order_number,
        'note': (
            f"Transfer \u20a6{amount_naira:,.0f} to the account above. "
            f"Use {order.order_number} as your payment reference, "
            f"then send proof of payment to our WhatsApp."
        ),
    }