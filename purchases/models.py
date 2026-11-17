from django.db import models
from django.conf import settings
from suppliers.models import Supplier
from materials.models import Material, Unit
from core.models import Currency

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