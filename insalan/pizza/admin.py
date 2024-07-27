"""This module contains the admin configuration for the Pizza app."""

from django.contrib import admin
from django.http import HttpResponse

from .models import Pizza, TimeSlot, Order, PizzaOrder, PizzaExport, PaymentMethod

class PizzaAdmin(admin.ModelAdmin):
    """Admin class for the Pizza model"""
    list_display = ("id", "name", "ingredients")
    search_fields = ["name", "ingredients", "allergens"]

admin.site.register(Pizza, PizzaAdmin)


class TimeSlotAdmin(admin.ModelAdmin):
    """Admin class for the TimeSlot model"""
    list_display = ("id", "delivery_time", "end", "pizza_max")
    search_fields = ["delivery_time", "end"]

admin.site.register(TimeSlot, TimeSlotAdmin)


class PizzaOrderInline(admin.TabularInline):
    """Admin class for the PizzaOrder model"""
    model = PizzaOrder
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    """Admin class for the Order model"""
    list_display = ("id", "get_username", "time_slot", "created_at")
    search_fields = ["user", "time_slot__delivery_time"]
    inlines = [PizzaOrderInline]

    # filter by time slot
    list_filter = ["time_slot"]

    # add an action to export orders
    actions = ["export"]

    def export(self, request, queryset):

        export = "pizza;prix;moyen de paiement;date créneau\n"

        for order in queryset:
            price = order.price / order.pizzaorder_set.count()
            payment_method = order.payment_method
            # Get the label of the payment method from the choices
            for choice in PaymentMethod.choices:
                if choice[0] == payment_method:
                    payment_method = choice[1]
                    break
            for pizza_order in order.pizzaorder_set.all():
                export += f"{pizza_order.pizza.name};{price};{payment_method};{order.time_slot.delivery_time}\n"

        response = HttpResponse(export, content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=export.csv"
        return response

    export.short_description = "Exporter un résumé des commandes"

admin.site.register(Order, OrderAdmin)

class ExportAdmin(admin.ModelAdmin):
    """Admin class for the Export model"""
    list_display = ("id", "time_slot", "created_at")
    search_fields = ["time_slot"]

admin.site.register(PizzaExport, ExportAdmin)
