from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Administrador,
    CompraInsumo,
    Equipo,
    MantenimientoCorrectivo,
    MantenimientoPreventivo,
)


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'ubicacion', 'frecuencia_preventiva', 'activo')
    list_filter = ('categoria', 'frecuencia_preventiva', 'activo')
    search_fields = ('nombre', 'ubicacion', 'marca', 'numero_serie')


@admin.register(MantenimientoPreventivo)
class MantenimientoPreventivoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'fecha_programada', 'estado', 'fecha_ejecutada', 'costo')
    list_filter = ('estado', 'fecha_programada')
    search_fields = ('equipo__nombre', 'descripcion', 'tecnico_responsable')


@admin.register(MantenimientoCorrectivo)
class MantenimientoCorrectivoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'area', 'fecha', 'prioridad', 'estado', 'costo')
    list_filter = ('prioridad', 'estado', 'fecha')
    search_fields = ('descripcion', 'area', 'proveedor', 'equipo__nombre')


@admin.register(CompraInsumo)
class CompraInsumoAdmin(admin.ModelAdmin):
    list_display = ('descripcion', 'equipo', 'fecha_compra', 'proveedor', 'costo')
    list_filter = ('fecha_compra',)
    search_fields = ('descripcion', 'proveedor', 'area', 'equipo__nombre')


@admin.register(Administrador)
class AdministradorAdmin(UserAdmin):
    pass
