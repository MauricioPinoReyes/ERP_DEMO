from django.contrib import admin
from .models import Unit, MaterialType, Material

@admin.register(Unit)
class UnitMeasureAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')
    search_fields = ('name', 'symbol')

@admin.register(MaterialType) 
class MaterialTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')
    search_fields = ('name',)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    # Columnas que se ven en la lista general
    list_display = (
        'id_material', 
        'name', 
        'material_type', 
        'unit', 
        'current_stock', 
        'min_stock', 
        'status'
    )
    
    # Filtros laterales para buscar rápido
    list_filter = ('material_type', 'status')
    
    # Barra de búsqueda
    search_fields = ('id_material', 'name', 'description')
    
    # Campos de solo lectura (auditoría)
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    
    # Organización del formulario de edición en secciones
    fieldsets = (
        ('Información Básica', {
            'fields': ('id_material', 'name', 'description', 'status')
        }),
        ('Clasificación', {
            'fields': ('material_type', 'unit')
        }),
        ('Control de Stock', {
            'fields': ('current_stock', 'min_stock'),
            'description': '⚠️ Configura estos valores para las alertas y validaciones de consumo en Órdenes de Trabajo.'
        }),
        ('Auditoría', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',) # Sección colapsable para no saturar la vista
        }),
    )