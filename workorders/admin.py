from django.contrib import admin
from .models import (
    WorkOrderStatus, WorkOrder, WorkOrderMaterial,
    WorkOrderTask, WorkOrderAssignment,
    WorkOrderDailyConsumption, WorkOrderDailyLabor
)


@admin.register(WorkOrderStatus)
class WorkOrderStatusAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'description')
    search_fields = ('name', 'symbol')


class WorkOrderMaterialInline(admin.TabularInline):
    model = WorkOrderMaterial
    extra = 1


class WorkOrderTaskInline(admin.TabularInline):
    model = WorkOrderTask
    extra = 1


class WorkOrderAssignmentInline(admin.TabularInline):
    model = WorkOrderAssignment
    extra = 1


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        'work_order_number', 'customer', 'product_description',
        'commitment_date', 'status', 'estimated_cost', 'real_cost'
    )
    list_filter = ('status', 'commitment_date', 'customer')
    search_fields = ('work_order_number', 'customer__name', 'product_description')
    inlines = [WorkOrderMaterialInline, WorkOrderTaskInline, WorkOrderAssignmentInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'customer', 'status', 'location', 'created_by'
        )


@admin.register(WorkOrderDailyConsumption)
class WorkOrderDailyConsumptionAdmin(admin.ModelAdmin):
    list_display = (
        'work_order', 'consumption_date', 'material',
        'quantity_consumed', 'waste_quantity', 'unit_cost'
    )
    list_filter = ('consumption_date', 'material')
    search_fields = ('work_order__work_order_number', 'material__name')


@admin.register(WorkOrderDailyLabor)
class WorkOrderDailyLaborAdmin(admin.ModelAdmin):
    list_display = (
        'work_order', 'labor_date', 'worker',
        'regular_hours', 'overtime_hours', 'hourly_rate'
    )
    list_filter = ('labor_date', 'worker')
    search_fields = ('work_order__work_order_number', 'worker__username')