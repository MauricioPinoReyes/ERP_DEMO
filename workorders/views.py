from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db import models
from django.forms import inlineformset_factory
from django.utils import timezone  # ✅ AGREGADO: Faltaba esta importación
import csv

from users.models import UserRole
from .models import (
    WorkOrder, WorkOrderMaterial, WorkOrderTask,
    WorkOrderAssignment, WorkOrderDailyConsumption, WorkOrderDailyLabor,
    WorkOrderStatus  # ✅ Ya está importado aquí, no hace falta importarlo dentro de la vista
)
from .forms import (
    WorkOrderForm, WorkOrderMaterialForm, WorkOrderTaskForm,
    WorkOrderAssignmentForm, WorkOrderDailyConsumptionForm, WorkOrderDailyLaborForm
)


@login_required
def work_order_list(request):
    """Lista de órdenes de trabajo"""
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__workorders')
    )['max_permission'] or 0
    
    if max_permission == 0:
        return redirect('dashboard')
    
    work_orders = WorkOrder.objects.select_related('customer', 'status').all()
    
    customer = request.GET.get('customer')
    status = request.GET.get('status')
    
    if customer:
        work_orders = work_orders.filter(customer__name__icontains=customer)
    if status:
        work_orders = work_orders.filter(status__name__iexact=status)
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="work_orders.csv"'
        response.write('\ufeff'.encode('utf-8'))
        writer = csv.writer(response)
        writer.writerow(['OT Number', 'Customer', 'Product', 'Commitment Date', 'Status', 'Estimated Cost', 'Real Cost'])
        
        for wo in work_orders:
            writer.writerow([
                wo.work_order_number,
                wo.customer.name,
                wo.product_description,
                wo.commitment_date,
                wo.status.name,
                wo.estimated_cost,
                wo.real_cost
            ])
        return response
    
    paginator = Paginator(work_orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    return render(request, 'workorders/work_order_list.html', {
        'page_obj': page_obj,
        'can_edit': max_permission == 2
    })


@login_required
def work_order_create(request):
    """Crear nueva orden de trabajo"""
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__workorders')
    )['max_permission'] or 0
    
    if max_permission < 2:
        return redirect('workorders:work_order_list')
    
    MaterialFormSet = inlineformset_factory(
        WorkOrder, WorkOrderMaterial,
        form=WorkOrderMaterialForm,
        extra=3, can_delete=True
    )
    
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        formset = MaterialFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            work_order = form.save(commit=False)
            work_order.created_by = request.user
            work_order.save()
            
            formset.instance = work_order
            formset.save()
            
            messages.success(request, f'OT {work_order.work_order_number} creada exitosamente')
            return redirect('workorders:work_order_detail', pk=work_order.pk)
    else:
        form = WorkOrderForm()
        formset = MaterialFormSet()
    
    return render(request, 'workorders/work_order_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Crear Orden de Trabajo'
    })


@login_required
def work_order_detail(request, pk):
    """Detalle de orden de trabajo"""
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__workorders')
    )['max_permission'] or 0
    
    if max_permission == 0:
        return redirect('dashboard')
    
    work_order = get_object_or_404(
        WorkOrder.objects.select_related('customer', 'status', 'location'),
        pk=pk
    )
    
    return render(request, 'workorders/work_order_detail.html', {
        'work_order': work_order,
        'materials': work_order.estimated_materials.select_related('material').all(),
        'tasks': work_order.tasks.all(),
        'assignments': work_order.assignments.select_related('worker', 'task').all(),
        'consumptions': work_order.daily_consumptions.select_related('material').all(),
        'labor_records': work_order.daily_labor.select_related('worker').all(),
        'can_edit': max_permission == 2,
        'deviation': work_order.calculate_deviation_percentage(),
        'has_alert': work_order.has_cost_deviation_alert()
    })


@login_required
def work_order_edit(request, pk):
    """Editar orden de trabajo"""
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__workorders')
    )['max_permission'] or 0
    
    if max_permission < 2:
        return redirect('workorders:work_order_list')
    
    work_order = get_object_or_404(WorkOrder, pk=pk)
    
    MaterialFormSet = inlineformset_factory(
        WorkOrder, WorkOrderMaterial,
        form=WorkOrderMaterialForm,
        extra=1, can_delete=True
    )
    
    if request.method == 'POST':
        form = WorkOrderForm(request.POST, instance=work_order)
        formset = MaterialFormSet(request.POST, instance=work_order)
        
        if form.is_valid() and formset.is_valid():
            work_order = form.save()
            formset.save()
            
            messages.success(request, f'OT {work_order.work_order_number} actualizada')
            return redirect('workorders:work_order_detail', pk=work_order.pk)
    else:
        form = WorkOrderForm(instance=work_order)
        formset = MaterialFormSet(instance=work_order)
    
    return render(request, 'workorders/work_order_form.html', {
        'form': form,
        'formset': formset,
        'work_order': work_order,
        'title': 'Editar Orden de Trabajo'
    })


@login_required
def work_order_close(request, pk):
    """Cerrar orden de trabajo (RF08, RF09)"""
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__workorders')
    )['max_permission'] or 0
    
    if max_permission < 2:
        return redirect('workorders:work_order_list')
    
    work_order = get_object_or_404(WorkOrder, pk=pk)
    
    if request.method == 'POST':
        # Calcular costo real
        real_cost = work_order.calculate_real_cost()
        work_order.real_cost = real_cost
        work_order.closing_date = timezone.now().date()  # ✅ Ahora timezone está importado
        
        # Cambiar estado a "Completed"
        completed_status = get_object_or_404(WorkOrderStatus, symbol='COMPLETED')
        work_order.status = completed_status
        work_order.save()
        
        # Alerta de desviación (CA09.2)
        if work_order.has_cost_deviation_alert():
            deviation = work_order.calculate_deviation_percentage()
            messages.warning(
                request,
                f'Alerta: OT {work_order.work_order_number} tiene desviación de {deviation:.2f}% (>{15}%)'
            )
        else:
            messages.success(request, f'OT {work_order.work_order_number} cerrada exitosamente')
        
        return redirect('workorders:work_order_detail', pk=work_order.pk)
    
    return redirect('workorders:work_order_detail', pk=work_order.pk)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from inventory.models import MovementType, InventoryMovements
from core.models import Currency
# ... (mantén el resto de tus imports) ...

@login_required
def daily_consumption_create(request, work_order_pk):
    """Registrar consumo diario de materiales (RF02, CA02.1 a CA02.5, CA03.1)"""
    
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__workorders')
    )['max_permission'] or 0
    
    if max_permission < 2:
        return redirect('workorders:work_order_detail', pk=work_order_pk)
    
    work_order = get_object_or_404(WorkOrder, pk=work_order_pk)
    
    if request.method == 'POST':
        form = WorkOrderDailyConsumptionForm(request.POST)
        if form.is_valid():
            material = form.cleaned_data['material']
            quantity = form.cleaned_data['quantity_consumed']
            waste = form.cleaned_data['waste_quantity']
            total_deduction = quantity + waste
            
            # ✅ CA02.3: Validar stock suficiente antes de guardar
            if material.current_stock < total_deduction:
                messages.error(
                    request, 
                    f"❌ Stock insuficiente para '{material.name}'. "
                    f"Disponible: {material.current_stock}, Solicitado: {total_deduction}"
                )
                return redirect('workorders:daily_consumption_create', work_order_pk=work_order_pk)
            
            # 1. Guardar el consumo en la OT
            consumption = form.save(commit=False)
            consumption.work_order = work_order
            consumption.created_by = request.user
            consumption.save()
            
            # 2. Actualizar el costo real de la OT en tiempo real
            work_order.real_cost = work_order.calculate_real_cost()
            work_order.save()
            
            # ✅ CA02.2: Descontar automáticamente del stock del material
            material.current_stock -= total_deduction
            material.save()
            
            # ✅ CA02.2: Generar movimiento de inventario tipo "Salida" vinculado a la OT
            # Nota: Asegúrate de tener un MovementType con symbol 'SALIDA' o 'OUT' en tu BD
            try:
               movement_type = MovementType.objects.get(symbol__iexact='WO_CONS')
            except MovementType.DoesNotExist:
                # Fallback: usa el primer tipo de movimiento si no existe 'SALIDA' (créalo en el admin después)
                movement_type = MovementType.objects.get(symbol__iexact='INT_USE')
            
            # Obtener una moneda por defecto si el material no tiene una asignada directamente
            default_currency = Currency.objects.first()
            
            movement_id = f"WO-{consumption.pk:06d}"

            InventoryMovements.objects.create(
                id_inventory_movement=movement_id,  
                id_location=work_order.location,
                id_material=material,
                quantity=total_deduction,
                unit_type=material.unit,
                price=form.cleaned_data['unit_cost'],
                currency=default_currency,
                movement_type=movement_type,
                created_by=request.user
            )
            
            # ✅ CA03.1: Alerta visual si el stock cae por debajo del mínimo
            if material.current_stock <= material.min_stock:
                messages.warning(
                    request, 
                    f"⚠️ ALERTA DE STOCK: El material '{material.name}' ha caído por debajo del nivel mínimo "
                    f"({material.min_stock}). Stock actual: {material.current_stock}"
                )
            
            messages.success(request, '✅ Consumo registrado y stock actualizado exitosamente')
            return redirect('workorders:work_order_detail', pk=work_order_pk)
    else:
        form = WorkOrderDailyConsumptionForm()
    
    return render(request, 'workorders/consumption_form.html', {
        'form': form,
        'work_order': work_order,
        'title': 'Registrar Consumo Diario'
    })


@login_required
def daily_labor_create(request, work_order_pk):
    """Registrar horas trabajadas"""
    max_permission = UserRole.objects.filter(user_id=request.user).aggregate(
        max_permission=models.Max('role__workorders')
    )['max_permission'] or 0
    
    if max_permission < 2:
        return redirect('workorders:work_order_detail', pk=work_order_pk)
    
    work_order = get_object_or_404(WorkOrder, pk=work_order_pk)
    
    if request.method == 'POST':
        form = WorkOrderDailyLaborForm(request.POST)
        if form.is_valid():
            labor = form.save(commit=False)
            labor.work_order = work_order
            labor.created_by = request.user
            labor.save()

            # ✅ OPTIMIZACIÓN: Usamos la variable work_order que ya tenemos
            work_order.real_cost = work_order.calculate_real_cost()
            work_order.save()
            
            messages.success(request, 'Horas registradas exitosamente')
            return redirect('workorders:work_order_detail', pk=work_order_pk)
    else:
        form = WorkOrderDailyLaborForm()
    
    return render(request, 'workorders/labor_form.html', {
        'form': form,
        'work_order': work_order,
        'title': 'Registrar Horas Trabajadas'
    })