from datetime import date

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView

from .forms import (
    AdministradorEditForm,
    AdministradorForm,
    BusquedaCentralForm,
    CompraInsumoForm,
    EjecutarPreventivoForm,
    EquipoForm,
    MantenimientoCorrectivoForm,
    MantenimientoPreventivoForm,
)
from .reportes_export import (
    exportar_reporte_equipos_excel,
    exportar_reporte_equipos_pdf,
    obtener_datos_reporte_equipos,
)
from .models import (
    CATEGORIA_EQUIPO_CHOICES,
    CompraInsumo,
    Equipo,
    MantenimientoCorrectivo,
    MantenimientoPreventivo,
)

Administrador = get_user_model()

MESES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def get_success_url(self):
        return reverse_lazy('dashboard-ui')


def _filtros_fecha(request, campo_preventivo='fecha_programada', campo_correctivo='fecha', campo_compra='fecha_compra'):
    anio = request.GET.get('anio')
    mes = request.GET.get('mes')
    equipo_id = request.GET.get('equipo')
    q = request.GET.get('q', '').strip()

    filtros = {}
    if anio:
        filtros['anio'] = int(anio)
    if mes:
        filtros['mes'] = int(mes)
    if equipo_id:
        filtros['equipo_id'] = int(equipo_id)
    if q:
        filtros['q'] = q
    return filtros


def _aplicar_filtro_fecha(qs, campo, anio=None, mes=None):
    if anio:
        qs = qs.filter(**{f'{campo}__year': anio})
    if mes:
        qs = qs.filter(**{f'{campo}__month': mes})
    return qs


def _contexto_filtros(request):
    hoy = date.today()
    return {
        'anio_seleccionado': request.GET.get('anio', hoy.year),
        'mes_seleccionado': request.GET.get('mes', ''),
        'equipo_seleccionado': request.GET.get('equipo', ''),
        'q': request.GET.get('q', ''),
        'anios_disponibles': list(range(hoy.year - 2, hoy.year + 3)),
        'meses_disponibles': MESES,
        'equipos_filtro': Equipo.objects.filter(activo=True),
    }


def _anio_filtro_listado(request):
    """Año activo en listados: actual al entrar; None si el usuario elige «Año» (todos)."""
    hoy = date.today()
    if 'anio' not in request.GET:
        return hoy.year
    anio = request.GET.get('anio', '')
    return int(anio) if anio else None


def actualizar_estados_vencidos():
    MantenimientoPreventivo.objects.filter(
        estado='pendiente',
        fecha_programada__lt=date.today(),
    ).update(estado='vencido')


# -------------------- EQUIPOS --------------------

def equipos_list(request):
    query = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '')
    equipos = Equipo.objects.all()

    if query:
        equipos = equipos.filter(
            Q(nombre__icontains=query) |
            Q(ubicacion__icontains=query) |
            Q(marca__icontains=query)
        )
    if categoria:
        equipos = equipos.filter(categoria=categoria)

    return render(request, 'core/equipos_list.html', {
        'equipos': equipos,
        'q': query,
        'categoria_seleccionada': categoria,
        'categorias_equipo': CATEGORIA_EQUIPO_CHOICES,
    })


def equipo_create(request):
    if request.method == 'POST':
        form = EquipoForm(request.POST)
        if form.is_valid():
            equipo = form.save()
            anio = date.today().year
            resultado = equipo.generar_cronograma_anual(anio)
            messages.success(
                request,
                f'Equipo registrado. Se generaron {resultado["creados"]} mantenimientos preventivos para {anio}.',
            )
            return redirect('equipos-list')
    else:
        form = EquipoForm()
    return render(request, 'core/equipo_form.html', {'form': form, 'titulo': 'Registrar equipo'})


def equipo_edit(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    if request.method == 'POST':
        form = EquipoForm(request.POST, instance=equipo)
        if form.is_valid():
            cambio_cronograma = (
                form.cleaned_data['frecuencia_preventiva'] != equipo.frecuencia_preventiva
                or form.cleaned_data['fecha_base_programacion'] != equipo.fecha_base_programacion
            )
            form.save()
            if cambio_cronograma:
                resultado = equipo.actualizar_cronograma_completo()
                messages.success(
                    request,
                    f'Equipo actualizado. Cronograma {resultado["anio_inicio"]}–{resultado["anio_fin"]} recalculado: '
                    f'{resultado["creados"]} fecha(s) nueva(s), '
                    f'{resultado["eliminados"]} obsoleta(s) eliminada(s).',
                )
            else:
                messages.success(request, 'Equipo actualizado correctamente.')
            return redirect('equipos-list')
    else:
        form = EquipoForm(instance=equipo)
    return render(request, 'core/equipo_form.html', {'form': form, 'titulo': 'Editar equipo', 'equipo': equipo})


def equipo_delete(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    equipo.delete()
    messages.success(request, 'Equipo eliminado.')
    return redirect('equipos-list')


def equipo_detalle(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    actualizar_estados_vencidos()
    hoy = date.today()
    anio = int(request.GET.get('anio', hoy.year))

    cronograma_anio = equipo.mantenimientos_preventivos.filter(fecha_programada__year=anio)
    preventivos = cronograma_anio.order_by('fecha_programada')
    correctivos = equipo.mantenimientos_correctivos.all()[:20]
    compras = equipo.compras.all()[:20]
    resumen_cronograma = {
        'pendiente': cronograma_anio.filter(estado='pendiente').count(),
        'ejecutado': cronograma_anio.filter(estado='ejecutado').count(),
        'vencido': cronograma_anio.filter(estado='vencido').count(),
        'total': cronograma_anio.count(),
    }

    return render(request, 'core/equipo_detalle.html', {
        'equipo': equipo,
        'preventivos': preventivos,
        'correctivos': correctivos,
        'compras': compras,
        'anio_seleccionado': anio,
        'anios_disponibles': Equipo.rango_anios_cronograma(hoy),
        'resumen_cronograma': resumen_cronograma,
    })


def generar_cronograma_equipo(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    anio_vista = int(request.GET.get('anio', date.today().year))
    resultado = equipo.actualizar_cronograma_completo()
    if resultado['creados'] or resultado['eliminados']:
        messages.success(
            request,
            f'Cronograma {resultado["anio_inicio"]}–{resultado["anio_fin"]} actualizado: '
            f'{resultado["creados"]} fecha(s) nueva(s), '
            f'{resultado["eliminados"]} obsoleta(s) eliminada(s).',
        )
    else:
        messages.info(
            request,
            f'El cronograma {resultado["anio_inicio"]}–{resultado["anio_fin"]} ya está al día '
            f'según la frecuencia y fecha base actuales.',
        )
    return redirect(f"{reverse('equipo-detalle', kwargs={'equipo_id': equipo.id})}?anio={anio_vista}")


# -------------------- PREVENTIVOS --------------------

def preventivos_list(request):
    actualizar_estados_vencidos()
    anio_filtro = _anio_filtro_listado(request)
    mes = request.GET.get('mes')
    equipo_id = request.GET.get('equipo')
    estado = request.GET.get('estado', '')

    preventivos = MantenimientoPreventivo.objects.select_related('equipo')

    if anio_filtro is not None:
        preventivos = preventivos.filter(fecha_programada__year=anio_filtro)
    if mes:
        preventivos = preventivos.filter(fecha_programada__month=int(mes))
    if equipo_id:
        preventivos = preventivos.filter(equipo_id=int(equipo_id))
    if estado:
        preventivos = preventivos.filter(estado=estado)

    preventivos = preventivos.order_by('fecha_programada')

    return render(request, 'core/preventivos_list.html', {
        'preventivos': preventivos,
        'estado_seleccionado': estado,
        **_contexto_filtros(request),
    })


def preventivo_create(request):
    if request.method == 'POST':
        form = MantenimientoPreventivoForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.registrado_por = request.user
            registro.save()
            messages.success(request, 'Mantenimiento preventivo registrado.')
            return redirect('preventivos-list')
    else:
        form = MantenimientoPreventivoForm()
    return render(request, 'core/preventivo_form.html', {'form': form, 'titulo': 'Registrar preventivo'})


def preventivo_edit(request, preventivo_id):
    preventivo = get_object_or_404(MantenimientoPreventivo, id=preventivo_id)
    if request.method == 'POST':
        form = MantenimientoPreventivoForm(request.POST, instance=preventivo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro actualizado.')
            return redirect('preventivos-list')
    else:
        form = MantenimientoPreventivoForm(instance=preventivo)
    return render(request, 'core/preventivo_form.html', {'form': form, 'titulo': 'Editar preventivo'})


def preventivo_ejecutar(request, preventivo_id):
    preventivo = get_object_or_404(MantenimientoPreventivo, id=preventivo_id)
    if request.method == 'POST':
        form = EjecutarPreventivoForm(request.POST)
        if form.is_valid():
            preventivo.marcar_ejecutado(
                fecha_ejecutada=form.cleaned_data['fecha_ejecutada'],
                descripcion=form.cleaned_data['descripcion'],
                costo=form.cleaned_data['costo'],
                tecnico=form.cleaned_data['tecnico_responsable'],
                observaciones=form.cleaned_data['observaciones'],
            )
            preventivo.registrado_por = request.user
            preventivo.save()
            messages.success(request, 'Mantenimiento marcado como ejecutado.')
            return redirect('preventivos-list')
    else:
        form = EjecutarPreventivoForm(initial={'fecha_ejecutada': date.today()})
    return render(request, 'core/preventivo_ejecutar.html', {'form': form, 'preventivo': preventivo})


def cronograma_preventivos(request):
    actualizar_estados_vencidos()
    anio = int(request.GET.get('anio', date.today().year))

    if request.method == 'POST':
        total_creados = total_eliminados = 0
        anios = Equipo.rango_anios_cronograma()
        for equipo in Equipo.objects.filter(activo=True):
            r = equipo.actualizar_cronograma_completo(anios)
            total_creados += r['creados']
            total_eliminados += r['eliminados']
        messages.success(
            request,
            f'Cronograma {anios[0]}–{anios[-1]} actualizado para todos los equipos: '
            f'{total_creados} fecha(s) nueva(s), {total_eliminados} obsoleta(s) eliminada(s).',
        )
        return redirect(f"{reverse('cronograma-preventivos')}?anio={anio}")

    preventivos = MantenimientoPreventivo.objects.filter(
        fecha_programada__year=anio,
    ).select_related('equipo').order_by('fecha_programada')

    resumen_mes = {}
    for num, nombre in MESES:
        qs = preventivos.filter(fecha_programada__month=num)
        resumen_mes[nombre] = {
            'pendiente': qs.filter(estado='pendiente').count(),
            'ejecutado': qs.filter(estado='ejecutado').count(),
            'vencido': qs.filter(estado='vencido').count(),
        }

    return render(request, 'core/cronograma_preventivos.html', {
        'preventivos': preventivos,
        'anio_seleccionado': anio,
        'anios_disponibles': list(range(date.today().year - 1, date.today().year + 3)),
        'resumen_mes': resumen_mes,
    })


# -------------------- CORRECTIVOS --------------------

def correctivos_list(request):
    anio_filtro = _anio_filtro_listado(request)
    mes = request.GET.get('mes')
    equipo_id = request.GET.get('equipo')
    estado = request.GET.get('estado', '')

    correctivos = MantenimientoCorrectivo.objects.select_related('equipo')

    if anio_filtro is not None:
        correctivos = correctivos.filter(fecha__year=anio_filtro)
    if mes:
        correctivos = correctivos.filter(fecha__month=int(mes))
    if equipo_id:
        correctivos = correctivos.filter(equipo_id=int(equipo_id))
    if estado:
        correctivos = correctivos.filter(estado=estado)

    correctivos = correctivos.order_by('-fecha')

    return render(request, 'core/correctivos_list.html', {
        'correctivos': correctivos,
        'estado_seleccionado': estado,
        **_contexto_filtros(request),
    })


def correctivo_create(request):
    if request.method == 'POST':
        form = MantenimientoCorrectivoForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.registrado_por = request.user
            registro.save()
            messages.success(request, 'Mantenimiento correctivo registrado.')
            return redirect('correctivos-list')
    else:
        form = MantenimientoCorrectivoForm(initial={'fecha': date.today()})
    return render(request, 'core/correctivo_form.html', {'form': form, 'titulo': 'Registrar correctivo'})


def correctivo_edit(request, correctivo_id):
    correctivo = get_object_or_404(MantenimientoCorrectivo, id=correctivo_id)
    if request.method == 'POST':
        form = MantenimientoCorrectivoForm(request.POST, instance=correctivo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro actualizado.')
            return redirect('correctivos-list')
    else:
        form = MantenimientoCorrectivoForm(instance=correctivo)
    return render(request, 'core/correctivo_form.html', {'form': form, 'titulo': 'Editar correctivo'})


def correctivo_delete(request, correctivo_id):
    correctivo = get_object_or_404(MantenimientoCorrectivo, id=correctivo_id)
    correctivo.delete()
    messages.success(request, 'Registro eliminado.')
    return redirect('correctivos-list')


# -------------------- COMPRAS --------------------

def compras_list(request):
    anio_filtro = _anio_filtro_listado(request)
    mes = request.GET.get('mes')
    equipo_id = request.GET.get('equipo')
    q = request.GET.get('q', '').strip()

    compras = CompraInsumo.objects.select_related('equipo')

    if anio_filtro is not None:
        compras = compras.filter(fecha_compra__year=anio_filtro)
    if mes:
        compras = compras.filter(fecha_compra__month=int(mes))
    if equipo_id:
        compras = compras.filter(equipo_id=int(equipo_id))
    if q:
        compras = compras.filter(
            Q(descripcion__icontains=q) |
            Q(proveedor__icontains=q) |
            Q(area__icontains=q) |
            Q(ubicacion_instalacion__icontains=q)
        )

    compras = compras.order_by('-fecha_compra')

    total = compras.aggregate(total=Sum('costo'))['total'] or 0

    return render(request, 'core/compras_list.html', {
        'compras': compras,
        'total_filtrado': total,
        **_contexto_filtros(request),
    })


def compra_create(request):
    if request.method == 'POST':
        form = CompraInsumoForm(request.POST)
        if form.is_valid():
            registro = form.save(commit=False)
            registro.registrado_por = request.user
            registro.save()
            messages.success(request, 'Compra registrada correctamente.')
            return redirect('compras-list')
    else:
        form = CompraInsumoForm(initial={'fecha_compra': date.today()})
    return render(request, 'core/compra_form.html', {'form': form, 'titulo': 'Registrar compra / insumo'})


def compra_edit(request, compra_id):
    compra = get_object_or_404(CompraInsumo, id=compra_id)
    if request.method == 'POST':
        form = CompraInsumoForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Compra actualizada.')
            return redirect('compras-list')
    else:
        form = CompraInsumoForm(instance=compra)
    return render(request, 'core/compra_form.html', {'form': form, 'titulo': 'Editar compra / insumo'})


def compra_delete(request, compra_id):
    compra = get_object_or_404(CompraInsumo, id=compra_id)
    compra.delete()
    messages.success(request, 'Compra eliminada.')
    return redirect('compras-list')


# -------------------- BÚSQUEDA CENTRAL --------------------

def busqueda_central(request):
    form = BusquedaCentralForm(request.GET or None)
    resultados = []

    if form.is_valid() and any(form.cleaned_data.values()):
        equipo = form.cleaned_data.get('equipo')
        mes = form.cleaned_data.get('mes')
        anio = form.cleaned_data.get('anio')
        anio = int(anio) if anio else None
        tipo = form.cleaned_data.get('tipo')

        if not tipo or tipo == 'preventivo':
            qs = MantenimientoPreventivo.objects.select_related('equipo')
            if equipo:
                qs = qs.filter(equipo=equipo)
            if anio:
                qs = qs.filter(fecha_programada__year=anio)
            if mes:
                qs = qs.filter(fecha_programada__month=int(mes))
            for item in qs[:50]:
                resultados.append({
                    'tipo': 'Preventivo',
                    'fecha': item.fecha_programada,
                    'referencia': str(item.equipo),
                    'descripcion': item.descripcion or item.get_estado_display(),
                    'costo': item.costo,
                    'estado': item.get_estado_display(),
                    'url': reverse_lazy('preventivos-list'),
                })

        if not tipo or tipo == 'correctivo':
            qs = MantenimientoCorrectivo.objects.select_related('equipo')
            if equipo:
                qs = qs.filter(equipo=equipo)
            if anio:
                qs = qs.filter(fecha__year=anio)
            if mes:
                qs = qs.filter(fecha__month=int(mes))
            for item in qs[:50]:
                ref = item.equipo.nombre if item.equipo else item.area
                resultados.append({
                    'tipo': 'Correctivo',
                    'fecha': item.fecha,
                    'referencia': ref,
                    'descripcion': item.descripcion[:120],
                    'costo': item.costo,
                    'estado': item.get_estado_display(),
                    'url': reverse_lazy('correctivos-list'),
                })

        if not tipo or tipo == 'compra':
            qs = CompraInsumo.objects.select_related('equipo')
            if equipo:
                qs = qs.filter(equipo=equipo)
            if anio:
                qs = qs.filter(fecha_compra__year=anio)
            if mes:
                qs = qs.filter(fecha_compra__month=int(mes))
            for item in qs[:50]:
                ref = item.equipo.nombre if item.equipo else item.area or 'General'
                resultados.append({
                    'tipo': 'Compra',
                    'fecha': item.fecha_compra,
                    'referencia': ref,
                    'descripcion': item.descripcion,
                    'costo': item.costo,
                    'estado': item.proveedor,
                    'url': reverse_lazy('compras-list'),
                })

        resultados.sort(key=lambda x: x['fecha'], reverse=True)

    return render(request, 'core/busqueda_central.html', {
        'form': form,
        'resultados': resultados,
    })


# -------------------- REPORTES --------------------

def reportes_equipos(request):
    anio = int(request.GET.get('anio', date.today().year))
    datos, totales = obtener_datos_reporte_equipos(anio)

    return render(request, 'core/reportes_equipos.html', {
        'datos': datos,
        'totales': totales,
        'anio_seleccionado': anio,
        'anios_disponibles': list(range(date.today().year - 2, date.today().year + 2)),
    })


def reportes_equipos_excel(request):
    anio = int(request.GET.get('anio', date.today().year))
    datos, totales = obtener_datos_reporte_equipos(anio)
    buffer = exportar_reporte_equipos_excel(anio, datos, totales)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="reporte_equipos_{anio}.xlsx"'
    return response


def reportes_equipos_pdf(request):
    anio = int(request.GET.get('anio', date.today().year))
    datos, totales = obtener_datos_reporte_equipos(anio)
    buffer = exportar_reporte_equipos_pdf(anio, datos, totales)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte_equipos_{anio}.pdf"'
    return response


# -------------------- ADMINISTRADORES --------------------

@login_required
def registrar_administrador(request):
    if request.method == 'POST':
        form = AdministradorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Administrador registrado correctamente.')
            return redirect('listar_administradores')
    else:
        form = AdministradorForm()
    return render(request, 'core/administrador_registro.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class ListadoAdministradoresView(ListView):
    model = Administrador
    template_name = 'core/administradores_list.html'
    context_object_name = 'administradores'


@login_required
def editar_administrador(request, admin_id):
    admin = get_object_or_404(Administrador, id=admin_id)
    if request.method == 'POST':
        form = AdministradorEditForm(request.POST, instance=admin)
        if form.is_valid():
            clave_cambiada = bool(form.cleaned_data.get('nueva_clave'))
            usuario_anterior = admin.username
            admin = form.save()
            if clave_cambiada and admin.id == request.user.id:
                update_session_auth_hash(request, admin)
            if admin.username != usuario_anterior and admin.id == request.user.id:
                messages.info(
                    request,
                    'Su nombre de usuario cambió. Use el nuevo usuario en su próximo inicio de sesión.',
                )
            messages.success(request, 'Administrador actualizado correctamente.')
            return redirect('listar_administradores')
    else:
        form = AdministradorEditForm(instance=admin)
    return render(request, 'core/administrador_edit.html', {'form': form, 'admin': admin})


@login_required
def eliminar_administrador(request, admin_id):
    admin = get_object_or_404(Administrador, id=admin_id)
    if admin.id == request.user.id:
        messages.error(request, 'No puede eliminar su propia cuenta.')
    elif admin.username == 'admin' and Administrador.objects.count() == 1:
        messages.error(request, 'No se puede eliminar el único administrador del sistema.')
    elif admin.username == 'admin':
        messages.error(request, 'No se puede eliminar el usuario principal del sistema.')
    else:
        admin.delete()
        messages.success(request, 'Administrador eliminado.')
    return redirect('listar_administradores')
