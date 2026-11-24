from django import forms
from .models import (
    WorkOrder, WorkOrderMaterial, WorkOrderTask,
    WorkOrderAssignment, WorkOrderDailyConsumption, WorkOrderDailyLabor
)


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'work_order_number', 'customer', 'product_description', 'quantity',
            'commitment_date', 'estimated_cost', 'status', 'location', 'notes'
        ]
        widgets = {
            'commitment_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class WorkOrderMaterialForm(forms.ModelForm):
    class Meta:
        model = WorkOrderMaterial
        fields = ['material', 'estimated_quantity', 'unit_cost']


class WorkOrderTaskForm(forms.ModelForm):
    class Meta:
        model = WorkOrderTask
        fields = ['task_name', 'description', 'estimated_hours', 'position']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }


class WorkOrderAssignmentForm(forms.ModelForm):
    class Meta:
        model = WorkOrderAssignment
        fields = ['worker', 'task']


class WorkOrderDailyConsumptionForm(forms.ModelForm):
    class Meta:
        model = WorkOrderDailyConsumption
        fields = ['consumption_date', 'material', 'quantity_consumed', 'unit_cost', 'waste_quantity', 'notes']
        widgets = {
            'consumption_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class WorkOrderDailyLaborForm(forms.ModelForm):
    class Meta:
        model = WorkOrderDailyLabor
        fields = ['labor_date', 'worker', 'regular_hours', 'overtime_hours', 'hourly_rate']
        widgets = {
            'labor_date': forms.DateInput(attrs={'type': 'date'}),
        }