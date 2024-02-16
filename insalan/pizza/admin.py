from django.contrib import admin

from .models import Pizza, TimeSlot, Order, PizzaOrder, PizzaExport

class PizzaAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "ingredients")
    search_fields = ["name", "ingredients", "allergens"]

admin.site.register(Pizza, PizzaAdmin)


class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("id", "delivery_time", "end", "pizza_max")
    search_fields = ["delivery_time", "end"]

admin.site.register(TimeSlot, TimeSlotAdmin)


class PizzaOrderInline(admin.TabularInline):
    model = PizzaOrder
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "get_username", "time_slot", "created_at")
    search_fields = ["user", "time_slot__delivery_time"]
    inlines = [PizzaOrderInline]

admin.site.register(Order, OrderAdmin)

class ExportAdmin(admin.ModelAdmin):
    list_display = ("id", "time_slot", "created_at")
    search_fields = ["time_slot"]

admin.site.register(PizzaExport, ExportAdmin)
