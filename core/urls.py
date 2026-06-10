from django.urls import path
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect

from .views import CustomLoginView
from .views import (
    busqueda_central,
    compra_create,
    compra_delete,
    compra_edit,
    compras_list,
    correctivo_create,
    correctivo_delete,
    correctivo_edit,
    correctivos_list,
    cronograma_preventivos,
    editar_administrador,
    eliminar_administrador,
    equipo_create,
    equipo_delete,
    equipo_detalle,
    equipo_edit,
    equipos_list,
    generar_cronograma_equipo,
    ListadoAdministradoresView,
    preventivo_create,
    preventivo_edit,
    preventivo_ejecutar,
    preventivos_list,
    registrar_administrador,
    reportes_equipos,
    reportes_equipos_excel,
    reportes_equipos_pdf,
)
from .views_dashboard import AlertasMantenimientoView, dashboard_view


def redirect_to_login(request):
    return redirect('login')


urlpatterns = [
    path('', redirect_to_login),
    path('dashboard-ui/', dashboard_view, name='dashboard-ui'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('dashboard/alertas/', AlertasMantenimientoView.as_view(), name='alertas-mantenimiento'),

    # Equipos
    path('equipos/', equipos_list, name='equipos-list'),
    path('equipos/registrar/', equipo_create, name='equipo-create'),
    path('equipos/editar/<int:equipo_id>/', equipo_edit, name='equipo-edit'),
    path('equipos/eliminar/<int:equipo_id>/', equipo_delete, name='equipo-delete'),
    path('equipos/<int:equipo_id>/', equipo_detalle, name='equipo-detalle'),
    path('equipos/<int:equipo_id>/generar-cronograma/', generar_cronograma_equipo, name='generar-cronograma-equipo'),

    # Preventivos
    path('preventivos/', preventivos_list, name='preventivos-list'),
    path('preventivos/registrar/', preventivo_create, name='preventivo-create'),
    path('preventivos/editar/<int:preventivo_id>/', preventivo_edit, name='preventivo-edit'),
    path('preventivos/ejecutar/<int:preventivo_id>/', preventivo_ejecutar, name='preventivo-ejecutar'),
    path('preventivos/cronograma/', cronograma_preventivos, name='cronograma-preventivos'),

    # Correctivos
    path('correctivos/', correctivos_list, name='correctivos-list'),
    path('correctivos/registrar/', correctivo_create, name='correctivo-create'),
    path('correctivos/editar/<int:correctivo_id>/', correctivo_edit, name='correctivo-edit'),
    path('correctivos/eliminar/<int:correctivo_id>/', correctivo_delete, name='correctivo-delete'),

    # Compras
    path('compras/', compras_list, name='compras-list'),
    path('compras/registrar/', compra_create, name='compra-create'),
    path('compras/editar/<int:compra_id>/', compra_edit, name='compra-edit'),
    path('compras/eliminar/<int:compra_id>/', compra_delete, name='compra-delete'),

    # Búsqueda y reportes
    path('busqueda/', busqueda_central, name='busqueda-central'),
    path('reportes/equipos/', reportes_equipos, name='reportes-equipos'),
    path('reportes/equipos/excel/', reportes_equipos_excel, name='reportes-equipos-excel'),
    path('reportes/equipos/pdf/', reportes_equipos_pdf, name='reportes-equipos-pdf'),

    # Administradores
    path('administradores/registrar/', registrar_administrador, name='registrar_administrador'),
    path('administradores/listar/', ListadoAdministradoresView.as_view(), name='listar_administradores'),
    path('administradores/<int:admin_id>/editar/', editar_administrador, name='editar_administrador'),
    path('administradores/<int:admin_id>/eliminar/', eliminar_administrador, name='eliminar_administrador'),
]
