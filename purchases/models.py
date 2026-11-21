from django.db import models
from django.conf import settings
from suppliers.models import Supplier
from materials.models import Material, Unit
from core.models import Currency
from inventory.models import LocationInventory

class OrderStatus(models.Model):

    name = models.CharField(max_length=200, verbose_name="Name")
    # el modelo core.Currecy acepta vacios. Validar si afecta funcionalidad en caso de quedar vacío
    # desde core.Currency
    symbol = models.CharField(max_length=100, blank=True, verbose_name="Symbol")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Order Status"
        verbose_name_plural = "Order Status"

    def __str__(self):
        return self.symbol
    
class PurchaseOrder(models.Model):

    id_purchase_order = models.CharField(max_length=10, verbose_name="ID Purchase Order")
    id_supplier = models.ForeignKey(Supplier, default=1, on_delete=models.PROTECT, verbose_name="Supplier")
    issue_date = models.DateField(auto_now_add=True)
    estimated_delivery_date = models.DateField(verbose_name="Estimated delivery date")
    status = models.ForeignKey(OrderStatus, default=1, on_delete=models.PROTECT, verbose_name="Status")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"

    def __str__(self):
        return self.id_purchase_order

class LinesPurchaseOrder(models.Model):

    id_purchase_order_line = models.CharField(max_length=10, verbose_name="ID Purchase Order Line")
    id_purchase_order = models.ForeignKey(PurchaseOrder, default=1, on_delete=models.PROTECT, verbose_name="Purchase Order")
    id_material = models.ForeignKey(Material, default=1, on_delete=models.PROTECT, verbose_name="Material", related_name="id_material_1")
    position = models.IntegerField(default=1, verbose_name="Position")
    quantity = models.IntegerField(default=0, verbose_name="Quantity")
    unit_material = models.ForeignKey(Unit, on_delete=models.PROTECT, verbose_name="Unit")
    price = models.FloatField(verbose_name="Price")
    currency_supplier = models.ForeignKey(Currency, on_delete=models.PROTECT, verbose_name="Currency")
    received_quantity = models.IntegerField(verbose_name="Received Quantity")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Lines Purchase Order"
        verbose_name_plural = "Lines Purchase Orders"

    def __str__(self):
        return self.id_purchase_order_line

class GoodsReceiptStatus(models.Model):

    name = models.CharField(max_length=200, verbose_name="Name")
    # el modelo core.Currecy acepta vacios. Validar si afecta funcionalidad en caso de quedar vacío
    # desde core.Currency
    symbol = models.CharField(max_length=100, blank=True, verbose_name="Symbol")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Goods Receipt Status"
        verbose_name_plural = "Goods Receipt Status"

    def __str__(self):
        return self.symbol


class GoodsReceipt(models.Model):

    id_goods_receipt = models.CharField(max_length=10, verbose_name='ID Goods Receipt')
    id_purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, verbose_name='ID Purchase Order')
    receipt_date = models.DateField(verbose_name="Receipt Date")
    supplier_delivery_note = models.CharField(max_length=50, blank=True, null=True, verbose_name='Supplier Delivery Note Ref')

    status = models.ForeignKey(GoodsReceiptStatus, default=1, on_delete=models.PROTECT, verbose_name="Status")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Goods Receipt"
        verbose_name_plural = "Goods Receipts"

    def __str__(self):
        return self.id_goods_receipt


class LinesGoodsReceipt(models.Model):

    id_goods_receipt_line = models.CharField(max_length=10, verbose_name="ID Goods Receipt Line")
    id_goods_receipt = models.ForeignKey(GoodsReceipt, default=1, on_delete=models.PROTECT, verbose_name="Goods Receipt", related_name='lines')
    id_purchase_order_line = models.ForeignKey(LinesPurchaseOrder, on_delete=models.PROTECT, verbose_name="Purchase Order Line")
    id_material = models.ForeignKey(Material, default=1, on_delete=models.PROTECT, verbose_name="Material")
    received_quantity = models.IntegerField(default=0, verbose_name="Received Quantity")
    unit_material = models.ForeignKey(Unit, on_delete=models.PROTECT, verbose_name="Unit")
    id_location = models.ForeignKey(LocationInventory, on_delete=models.PROTECT, verbose_name="Destination Location")
    inventory_movement_ref = models.CharField(max_length=10, blank=True, null=True, verbose_name="Inventory Movement ID")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name = "Lines Goods Receipt"
        verbose_name_plural = "Lines Goods Receipts"

    def __str__(self):
        return self.id_goods_receipt_line







# ============================================================================
# OBSERVACIONES Y ANOTACIONES DEL MODELO PURCHASE ORDER
# ============================================================================
# 1. LLAVE PRIMARIA (id_purchase_order): 
#    El campo está definido como CharField(max_length=10) pero no tiene el 
#    atributo primary_key=True. Django creará automáticamente un campo 'id' 
#    numérico. Si se desea usar el ID personalizado como en otros modelos, 
#    agregar primary_key=True.
#
# 2. FECHA DE EMISIÓN (issue_date):
#    Tiene auto_now_add=True, lo que significa que no se puede modificar manualmente.
#    Si en el futuro se necesita registrar una orden con fecha pasada o futura 
#    (ej. carga de datos históricos), este atributo deberá cambiarse por default=timezone.now.
#
# 3. FECHA DE ENTREGA ESTIMADA (estimated_delivery_date):
#    Es un campo obligatorio (no tiene null=True ni blank=True). El usuario
#    deberá ingresar una fecha obligatoriamente al crear la orden.
#
# 4. VALORES POR DEFECTO (id_supplier y status):
#    Ambos tienen default=1. Esto asume que siempre existirá un registro con ID 1 
#    en las tablas 'Supplier' y 'OrderStatus'. Si esa fila se elimina, dará error.
#    (Aunque el on_delete=PROTECT ayuda a prevenirlo).
# ============================================================================


# ============================================================================
# OBSERVACIONES Y MEJORAS PARA MODELS.PY (APP PURCHASES - LinesPurchaseOrder)
# ============================================================================
# 1. LLAVE PRIMARIA (id_purchase_order_line):
#    El campo está definido como CharField(max_length=10) pero no tiene primary_key=True.
#    Django creará automáticamente un campo 'id' numérico como llave primaria. 
#    Si en el futuro se necesita que el ID de la línea (ej: "1-001") sea la llave primaria,
#    se deberá agregar el atributo primary_key=True al campo.
#
# 2. TIPO DE DATO PARA EL PRECIO (price):
#    Se está usando models.FloatField. Para aplicaciones financieras o contables (ERP), 
#    los precios NUNCA deben guardarse como Float, ya que pueden generar errores de 
#    redondeo (ej: 0.1 + 0.2 = 0.30000000000000004). Lo ideal es usar models.DecimalField
#    con max_digits y decimal_places.
#
# 3. CANTIDAD RECIBIDA (received_quantity):
#    Actualmente no tiene un valor por defecto (default=0). Al crear una línea, la vista
#    se lo asigna manualmente, pero sería más seguro que el modelo tenga default=0 por
#    si se crea una línea desde otro lugar (ej: el admin o un script).
#
# 4. RELACIÓN CON EL MATERIAL (related_name):
#    El campo id_material tiene un related_name="id_material_1". Esto es un poco confuso
#    y no sigue las convenciones de Django (que sugiere plurales, como "purchase_order_lines").
#    Si se consulta desde el modelo Material, sería `material.id_material_1.all()`.
#
# 5. CAMPOS DE AUDITORÍA (created_at, updated_at, created_by):
#    Excelente práctica incluirlos. Sin embargo, en el modelo de líneas de detalle, a veces
#    se omite el created_by porque ya se sabe quién creó la orden padre. No es un error,
#    pero es redundante.
#
# 6. BORRADO EN CASCADA (on_delete=models.PROTECT):
#    El id_purchase_order tiene on_delete=PROTECT. Esto significa que si se intenta 
#    eliminar una PurchaseOrder que tiene líneas asociadas, Django lanzará un error
#    (ProtectedError). Es una decisión de diseño, pero para líneas de detalle, normalmente
#    se usa on_delete=models.CASCADE (si se borra la orden, se borran sus líneas).
# ============================================================================


# ============================================================================
# OBSERVACIÓN: ESTADO POR DEFECTO (OrderStatus)
# ============================================================================
# Actualmente, al crear una orden se asigna el estado buscando por `pk=2`:
#   status = get_object_or_404(OrderStatus, pk=2)
#
# Debido a cómo se cargaron los datos de prueba, el ID 2 corresponde a "Closed" 
# en lugar de "Draft". Esto significa que todas las órdenes nuevas se crearán 
# como "Cerradas" por defecto.
#
# MEJORA FUTURA:
# Para evitar que esto se rompa si los IDs cambian (por ejemplo, al recrear la 
# base de datos), lo ideal es buscar el estado por su símbolo:
#   status = get_object_or_404(OrderStatus, symbol='DRAFT')
# ============================================================================