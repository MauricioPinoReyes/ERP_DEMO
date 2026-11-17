from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User, Role, UserRole

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username','email','first_name','last_name', 'is_staff','is_active')
    list_filter = ('is_staff', 'is_active','date_joined')
    search_fields = ('username','email','first_name','last_name')

    # Oculta los campos de permisos de Django (user_permissions y groups)
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        new_fieldsets = []
        for name, options in fieldsets:
            if 'fields' in options:
                fields = [f for f in options['fields'] 
                         if f not in ('user_permissions', 'groups')]
                if fields:
                    new_fieldsets.append((name, {**options, 'fields': fields}))
            else:
                new_fieldsets.append((name, options))
        return new_fieldsets


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name','customers','suppliers','materials','purchases','sales','inventory','accounting','reporting')
    list_filter = ('customers','suppliers','materials','purchases','sales','inventory','accounting','reporting')
    search_fields = ('role_name',)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user_id','role')
    list_filter = ('role',)
    search_fields = ('user_id__username','role__role_name')



# ============================================================================
# OCULTAR TABLAS DE DJANGO AUTH DEL ADMIN
# ============================================================================
# Estas tablas no se usan en el sistema de permisos personalizado del ERP.
# Se desregistran del admin para evitar confusión al administrador.
# Las tablas siguen existiendo en la BD (Django las requiere internamente),
# pero no se muestran en el panel de administración.
# ============================================================================

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass    


# ============================================================================
# ANÁLISIS Y MEJORAS FUTURAS - CustomUserAdmin
# ============================================================================
#  FORTALEZAS ACTUALES:
# - Hereda de UserAdmin (NO de ModelAdmin), lo cual es CRÍTICO para mantener
#   el hashing correcto de contraseñas y los formularios especializados de Django
# - list_display muestra información relevante sin saturar la vista
# - search_fields permite búsquedas eficientes por campos clave
#
# MEJORAS FUTURAS SUGERIDAS:
# - Agregar 'user_id' a search_fields para búsqueda por ID interno
# - Considerar agregar inlines para UserRole (ver UserRoleAdmin abajo)
# ============================================================================


# ============================================================================
# ANÁLISIS Y MEJORAS FUTURAS - RoleAdmin
# ============================================================================
# CUELLO DE BOTELLA DE UX ACTUAL:
# - list_display con 9 columnas hace la tabla extremadamente ancha
# - list_filter con 8 filtros satura la barra lateral del admin
# - Difícil de leer y navegar cuando hay muchos roles
#
# MEJORAS FUTURAS SUGERIDAS:
# 1. Crear un método personalizado que resuma los permisos en una sola columna:
#    @admin.display(description='Permisos')
#    def get_permissions_summary(self, obj):
#        permissions = []
#        if obj.customers >= 1: permissions.append("Clientes")
#        if obj.suppliers >= 1: permissions.append("Proveedores")
#        # ... etc
#        return ", ".join(permissions)
#
# 2. Simplificar list_filter a solo ('role_name',) o eliminarlo
# 3. Cambiar list_display a ('role_name', 'get_permissions_summary')
# ============================================================================


# ============================================================================
# ANÁLISIS Y MEJORAS FUTURAS - UserRoleAdmin
# ============================================================================
# FORTALEZAS ACTUALES:
# - Uso avanzado de 'user_id__username' y 'role__role_name' en search_fields
# - Permite búsquedas cruzadas (JOIN en SQL) de forma eficiente
#
# CUELLO DE BOTELLA DE UX ACTUAL:
# - Gestionar roles en tabla separada es tedioso
# - Para asignar 3 roles a un usuario, hay que crear 3 registros individuales
#
# MEJORAS FUTURAS SUGERIDAS:
# 1. Crear un Inline para UserRole dentro de CustomUserAdmin:
#    class UserRoleInline(admin.TabularInline):
#        model = UserRole
#        extra = 1
#        autocomplete_fields = ['role']
#
# 2. Agregar 'inlines = [UserRoleInline]' a CustomUserAdmin
#    Resultado: Los roles se asignan directamente desde la ficha del usuario
# ============================================================================