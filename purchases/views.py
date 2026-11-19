import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.db import transaction
from django.db.models import Max
from .models import PurchaseOrder, LinesPurchaseOrder, OrderStatus
from suppliers.models import Supplier
from materials.models import Material, Unit
from core.models import Currency


def get_supplier_details(request, supplier_id):
    supplier = get_object_or_404(Supplier, id_supplier=supplier_id)

    data = {
        'id_supplier': supplier.id_supplier,
        'name': supplier.name,
        'legal_name': supplier.legal_name,
        'tax_id': supplier.tax_id,
        'address': supplier.address,
        'city': supplier.city,
        'state_province': supplier.state_province,
        'country': supplier.country.name,
        'zip_code': supplier.zip_code,
        'phone': supplier.phone,
        'email': supplier.email,
        'contact_name': supplier.contact_name,
        'payment_terms': supplier.payment_terms,
        'currency': supplier.currency.symbol,
    }

    return JsonResponse(data)


def get_material_details(request, material_id):
    material = get_object_or_404(Material, id_material=material_id)

    data = {
        'id_material': material.id_material,
        'unit': material.unit.symbol,
        'description': material.description,
    }

    return JsonResponse(data)

def purchase_order_form(request):
    
    context = {
        'title': 'Create New Purchase Order'
    }

    return render(request, 'purchases/purchase_order_create.html', context)


@csrf_exempt
@require_POST
@transaction.atomic
def create_purchase_order(request):
    
    try:
        data = json.loads(request.body)
        
        supplier_id_str = data.get('id_supplier')
        estimated_delivery_date = data.get('estimated_delivery_date')
        lines_data = data.get('lines', [])

        if not supplier_id_str or not estimated_delivery_date or not lines_data:
            return JsonResponse({'error': 'Missing required fields (Supplier ID, Delivery Date, or Line Items).'}, status=400)
            
        try:
            supplier_id_value = supplier_id_str
            supplier = get_object_or_404(Supplier, id_supplier=supplier_id_value)
            status = get_object_or_404(OrderStatus, pk=2)
        except Exception:
            return JsonResponse({'error': 'Invalid Supplier ID or default Order Status not found.'}, status=400)

        max_id_result = PurchaseOrder.objects.aggregate(max_id=Max('id_purchase_order'))
        last_id_str = max_id_result.get('max_id')

        next_po_number = 1
        if last_id_str:
            try:
                next_po_number = int(last_id_str) + 1
            except ValueError:
                print(f"Warning: The last ID '{last_id_str}' is not a number.")
                next_po_number = 1

        next_po_id = str(next_po_number)

        purchase_order = PurchaseOrder.objects.create(
            id_purchase_order = next_po_id,
            id_supplier = supplier,
            estimated_delivery_date = estimated_delivery_date,
            status = status,
            created_by = request.user,
        )

        for i, line_data in enumerate(lines_data, start=1):
            material_id = line_data.get('id_material')
            unit_symbol = line_data.get('unit_material')
            currency_symbol = line_data.get('currency_supplier')
            quantity = line_data.get('quantity')
            price = line_data.get('price')
            position = line_data.get('position', i)

            try:
                material = get_object_or_404(Material, id_material=material_id)
                unit_obj = get_object_or_404(Unit, symbol=unit_symbol)
                #currency_obj = get_object_or_404(Currency, symbol=currency_symbol)
                currency_obj = Currency.objects.filter(symbol=currency_symbol).first()
            except Material.DoesNotExist:
                raise ValueError(f"Material ID '{material_id}' not found for line {i}.")
            except Unit.DoesNotExist:
                raise ValueError(f"Unit symbol '{unit_symbol}' not found for line {i}.")
            except Currency.DoesNotExist:
                raise ValueError(f"Currency symbol '{currency_symbol}' not found for line {i}.")

            line_po_id = f"{next_po_id}-{str(position).zfill(3)}"

            LinesPurchaseOrder.objects.create(
                id_purchase_order_line = line_po_id,
                id_purchase_order = purchase_order,
                id_material = material,
                position = position,
                quantity = quantity,
                unit_material = unit_obj,
                price = price,
                currency_supplier = currency_obj,
                received_quantity = 0,
                created_by = request.user
            )

        response_data = {
            'success': True,
            'id_purchase_order': next_po_id,
            'message': f"Purchase Order {next_po_id} created successfully.",
            'redirect_url': '/purchases/list/'
        }
        return JsonResponse(response_data, status=201)

    except ValueError as e:
        return JsonResponse({'error': f'Validation Error: {str(e)}'}, 
                            status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format in request body.'}, 
                            status=400)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return JsonResponse({'error': f'An unexpected server error occurred: {str(e)}'}, status=500)


# http://127.0.0.1:8000/purchases/create
# http://127.0.0.1:8000/purchases/api/supplier/details/SUP-CL-002/
# http://127.0.0.1:8000/purchases/api/material/details/MAT-PAP-001/

# ============================================================================
# OBSERVACIONES Y MEJORAS PARA VIEWS.PY (APP PURCHASES)
# ============================================================================
# 1. ESTADO POR DEFECTO (OrderStatus):
#    En la vista create_purchase_order se usa `get_object_or_404(OrderStatus, pk=2)`.
#    Esto asume que el estado con ID 2 siempre será el "Borrador" (Draft). Si en el 
#    futuro se borra o se recrea la tabla, los IDs cambiarán. Lo ideal sería buscarlo
#    por su nombre: `OrderStatus.objects.get(name='Draft')`.
#
# 2. MANEJO DE ERRORES (get_object_or_404):
#    En los bloques `try...except` internos de la vista create_purchase_order, se captura
#    `Material.DoesNotExist`, `Unit.DoesNotExist`, etc. Sin embargo, `get_object_or_404` 
#    lanza un `Http404` en lugar de `DoesNotExist`. En la práctica, el código funciona porque
#    el `except Exception` de más abajo atrapa el Http404, pero técnicamente esos `except` 
#    específicos nunca se ejecutan. Para que funcionen, debería usarse `Material.objects.get()`.
#
# 3. GENERACIÓN DEL ID DE ORDEN:
#    El código actual usa `PurchaseOrder.objects.aggregate(Max('id_purchase_order'))` y le 
#    suma 1. Si hay muchas órdenes simultáneas, podría haber duplicados (Race Condition). 
#    Para un entorno de producción, se recomienda usar un AutoField o un secuenciador a nivel 
#    de base de datos.
#
# 4. SEGURIDAD DEL CSRF:
#    El decorador `@csrf_exempt` desactiva la protección CSRF. Para una API pública es útil,
#    pero para un formulario web privado, es más seguro enviar el token CSRF desde el 
#    JavaScript (usando `getCookie('csrftoken')`) en lugar de desactivarlo.
#
# 5. FALTA CONTROL DE PERMISOS (UserRole):
#    A diferencia de las vistas de suppliers y materials, estas vistas de purchases no 
#    validan si el usuario tiene permisos (role__purchases). Cualquier usuario logueado
#    podría crear órdenes de compra. Se debería agregar la validación que se usó en las 
#    otras apps.
#
# 6. REDIRECT_URL HARDCODEADA:
#    En la respuesta exitosa, la `redirect_url` está escrita directamente como 
#    `'/purchases/list/'`. Es mejor usar `reverse('purchases:list')` para que no se rompa 
#    si cambias las rutas en el futuro.
# ============================================================================
    

# ============================================================================
# OBSERVACIÓN: BÚSQUEDA DE MONEDA POR SÍMBOLO
# ============================================================================
# En la vista create_purchase_order se busca la moneda por su símbolo:
#   currency_obj = get_object_or_404(Currency, symbol=currency_symbol)
#
# ERROR: Múltiples monedas comparten el mismo símbolo (ej: 7 monedas usan "$").
# Esto lanza el error "get() returned more than one Currency". LINEA 112 currency_obj = get_object_or_404(Currency, symbol=currency_symbol)
#
# SOLUCIÓN ACTUAL: Se cambió a .filter().first() para evitar el crash.
#
# MEJORA FUTURA:
# El API get_supplier_details debería devolver `currency.iso_code` en lugar de 
# `currency.symbol`, y la vista debería buscar por `iso_code=currency_symbol`.
# ============================================================================    