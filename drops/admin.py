from django.contrib import admin

from .models import Drop, DropProduct


@admin.register(Drop)
class DropAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'launch_date', 'end_date', 'is_published', 'is_live', 'product_count')
    list_filter = ('status', 'is_published')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-launch_date',)
    readonly_fields = ('created_at', 'updated_at')

    def is_live(self, obj):
        return obj.is_live
    is_live.boolean = True
    is_live.short_description = 'Live'

    def product_count(self, obj):
        return obj.drop_products.count()
    product_count.short_description = 'Product count'


@admin.register(DropProduct)
class DropProductAdmin(admin.ModelAdmin):
    list_display = ('drop', 'product', 'drop_price_naira', 'quantity_limit', 'units_sold', 'is_sold_out', 'discount_percentage')
    list_filter = ('is_sold_out', 'drop')
    search_fields = ('product__name', 'drop__name')

    def drop_price_naira(self, obj):
        return obj.drop_price_naira
    drop_price_naira.short_description = 'Drop price (N)'

    def discount_percentage(self, obj):
        return obj.discount_percentage
    discount_percentage.short_description = 'Discount %'
