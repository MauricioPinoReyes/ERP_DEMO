from decimal import Decimal
from django.db import models
from django.conf import settings
from customers.models import Customer
from materials.models import Material
from inventory.models import LocationInventory


class WorkOrderStatus(models.Model):
    """Estados de Orden de Trabajo"""
    name = models.CharField(max_length=50, unique=True, verbose_name="Status Name")
    symbol = models.CharField(max_length=20, unique=True, verbose_name="Symbol")
    description = models.TextField(blank=True, verbose_name="Description")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='wo_statuses_created'
    )
    
    class Meta:
        verbose_name = "Work Order Status"
        verbose_name_plural = "Work Order Statuses"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class WorkOrder(models.Model):
    """Orden de Trabajo - Cabecera"""
    
    work_order_number = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="OT Number"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        verbose_name="Customer",
        related_name='work_orders'
    )
    product_description = models.CharField(
        max_length=200,
        verbose_name="Product Description"
    )
    quantity = models.IntegerField(verbose_name="Quantity")
    
    issue_date = models.DateField(auto_now_add=True, verbose_name="Issue Date")
    commitment_date = models.DateField(verbose_name="Commitment Date")
    closing_date = models.DateField(null=True, blank=True, verbose_name="Closing Date")
    
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        verbose_name="Estimated Cost"
    )
    real_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0.00,
        verbose_name="Real Cost"
    )
    
    status = models.ForeignKey(
        WorkOrderStatus,
        on_delete=models.PROTECT,
        default=1,
        verbose_name="Status"
    )
    location = models.ForeignKey(
        LocationInventory,
        on_delete=models.PROTECT,
        verbose_name="Production Location"
    )
    
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='workorders_created'
    )
    
    class Meta:
        verbose_name = "Work Order"
        verbose_name_plural = "Work Orders"
        ordering = ['-issue_date', 'work_order_number']
    
    def __str__(self):
        return f"{self.work_order_number} - {self.customer.name}"
    
    def calculate_deviation_percentage(self):
        """Calcula desviación entre costo estimado y real"""
        if self.estimated_cost == 0:
            return 0
        return ((self.real_cost - self.estimated_cost) / self.estimated_cost) * 100
    
    def has_cost_deviation_alert(self):
        """Retorna True si desviación > 15%"""
        return abs(self.calculate_deviation_percentage()) > 15
    
    def calculate_real_cost(self):
        """Calcula costo real sumando consumos y mano de obra"""
        material_cost = sum(
            consumption.total_cost() 
            for consumption in self.daily_consumptions.all()
        )
        labor_cost = sum(
            labor.total_cost() 
            for labor in self.daily_labor.all()
        )
        return material_cost + labor_cost


class WorkOrderMaterial(models.Model):
    """Materiales estimados para la OT"""
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='estimated_materials'
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name="Material"
    )
    estimated_quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Estimated Quantity"
    )
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Unit Cost"
    )
    
    class Meta:
        verbose_name = "Work Order Material"
        verbose_name_plural = "Work Order Materials"
        unique_together = ['work_order', 'material']
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.material.name}"
    
    def total_cost(self):
        return self.estimated_quantity * self.unit_cost


class WorkOrderTask(models.Model):
    """Tareas/Operaciones de la OT"""
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    task_name = models.CharField(max_length=100, verbose_name="Task Name")
    description = models.TextField(blank=True, verbose_name="Description")
    estimated_hours = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        verbose_name="Estimated Hours"
    )
    position = models.IntegerField(default=1, verbose_name="Position")
    
    class Meta:
        verbose_name = "Work Order Task"
        verbose_name_plural = "Work Order Tasks"
        ordering = ['position']
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.task_name}"


class WorkOrderAssignment(models.Model):
    """Personal asignado a la OT"""
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Worker"
    )
    task = models.ForeignKey(
        WorkOrderTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Assigned Task"
    )
    assigned_date = models.DateField(auto_now_add=True, verbose_name="Assigned Date")
    
    class Meta:
        verbose_name = "Work Order Assignment"
        verbose_name_plural = "Work Order Assignments"
        unique_together = ['work_order', 'worker', 'assigned_date']
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.worker.username}"


class WorkOrderDailyConsumption(models.Model):
    """Consumo diario de materiales (RF02)"""
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='daily_consumptions'
    )
    consumption_date = models.DateField(verbose_name="Consumption Date")
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        verbose_name="Material"
    )
    quantity_consumed = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Quantity Consumed"
    )
    unit_cost = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Unit Cost"
    )
    waste_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        verbose_name="Waste/Merma Quantity"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='wo_consumptions_created'
    )
    
    class Meta:
        verbose_name = "Work Order Daily Consumption"
        verbose_name_plural = "Work Order Daily Consumptions"
        unique_together = ['work_order', 'consumption_date', 'material']
        ordering = ['-consumption_date']
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.consumption_date} - {self.material.name}"
    
    def total_cost(self):
        return (self.quantity_consumed + self.waste_quantity) * self.unit_cost


class WorkOrderDailyLabor(models.Model):
    """Horas trabajadas diarias"""
    
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='daily_labor'
    )
    labor_date = models.DateField(verbose_name="Labor Date")
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name="Worker"
    )
    regular_hours = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        verbose_name="Regular Hours"
    )
    overtime_hours = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        verbose_name="Overtime Hours"
    )
    hourly_rate = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name="Hourly Rate"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='wo_labor_created'
    )
    
    class Meta:
        verbose_name = "Work Order Daily Labor"
        verbose_name_plural = "Work Order Daily Labor Records"
        unique_together = ['work_order', 'labor_date', 'worker']
        ordering = ['-labor_date']
    
    def __str__(self):
        return f"{self.work_order.work_order_number} - {self.labor_date} - {self.worker.username}"
    
    def total_hours(self):
        return self.regular_hours + self.overtime_hours
    
    def total_cost(self):
        """
        Costo total de mano de obra (con recargo por horas extra).
        Cumple con CA08.1: horas trabajadas + horas extra.
        """
        regular_cost = self.regular_hours * self.hourly_rate
        overtime_cost = self.overtime_hours * (self.hourly_rate * Decimal('1.5'))
        return regular_cost + overtime_cost
