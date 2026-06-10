import json
from datetime import date, timedelta

from django.db.models import Sum, Count, Q
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CompraInsumo,
    Equipo,
    MantenimientoCorrectivo,
    MantenimientoPreventivo,
)
from .views import actualizar_estados_vencidos

MESES = [
    (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
    (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
    (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
]


def calcular_cards(anio, mes):
    actualizar_estados_vencidos()

    total_equipos = Equipo.objects.filter(activo=True).count()

    preventivos_pendientes = MantenimientoPreventivo.objects.filter(
        estado='pendiente',
        fecha_programada__year=anio,
        fecha_programada__month=mes,
    ).count()

    preventivos_vencidos = MantenimientoPreventivo.objects.filter(
        estado='vencido',
        fecha_programada__year=anio,
    ).count()

    correctivos_mes = MantenimientoCorrectivo.objects.filter(
        fecha__year=anio,
        fecha__month=mes,
    ).count()

    gastos_mes = (
        MantenimientoPreventivo.objects.filter(
            estado='ejecutado',
            fecha_ejecutada__year=anio,
            fecha_ejecutada__month=mes,
        ).aggregate(t=Sum('costo'))['t'] or 0
    ) + (
        MantenimientoCorrectivo.objects.filter(
            fecha__year=anio,
            fecha__month=mes,
        ).aggregate(t=Sum('costo'))['t'] or 0
    ) + (
        CompraInsumo.objects.filter(
            fecha_compra__year=anio,
            fecha_compra__month=mes,
        ).aggregate(t=Sum('costo'))['t'] or 0
    )

    compras_mes = CompraInsumo.objects.filter(
        fecha_compra__year=anio,
        fecha_compra__month=mes,
    ).count()

    return {
        'total_equipos': total_equipos,
        'preventivos_pendientes': preventivos_pendientes,
        'preventivos_vencidos': preventivos_vencidos,
        'correctivos_mes': correctivos_mes,
        'gastos_mes': gastos_mes,
        'compras_mes': compras_mes,
    }


def calcular_grafico_gastos(anio):
    gastos_por_mes = []
    for num, nombre in MESES:
        total = (
            MantenimientoPreventivo.objects.filter(
                estado='ejecutado',
                fecha_ejecutada__year=anio,
                fecha_ejecutada__month=num,
            ).aggregate(t=Sum('costo'))['t'] or 0
        ) + (
            MantenimientoCorrectivo.objects.filter(
                fecha__year=anio,
                fecha__month=num,
            ).aggregate(t=Sum('costo'))['t'] or 0
        ) + (
            CompraInsumo.objects.filter(
                fecha_compra__year=anio,
                fecha_compra__month=num,
            ).aggregate(t=Sum('costo'))['t'] or 0
        )
        gastos_por_mes.append(float(total))

    return {
        'etiquetas_gastos_json': json.dumps([n for _, n in MESES]),
        'datos_gastos_json': json.dumps(gastos_por_mes),
    }


def obtener_tablas_dashboard(anio, mes):
    proximos = MantenimientoPreventivo.objects.filter(
        estado__in=['pendiente', 'vencido'],
        fecha_programada__gte=date.today(),
        fecha_programada__lte=date.today() + timedelta(days=30),
    ).select_related('equipo').order_by('fecha_programada')[:5]

    vencidos = MantenimientoPreventivo.objects.filter(
        estado='vencido',
    ).select_related('equipo').order_by('fecha_programada')[:5]

    equipos_costosos = Equipo.objects.filter(activo=True).annotate(
        num_correctivos=Count(
            'mantenimientos_correctivos',
            filter=Q(mantenimientos_correctivos__fecha__year=anio),
        ),
        total_gasto=Sum(
            'mantenimientos_correctivos__costo',
            filter=Q(mantenimientos_correctivos__fecha__year=anio),
        ),
    ).filter(num_correctivos__gt=0).order_by('-num_correctivos', '-total_gasto')[:5]

    return {
        'proximos_preventivos': proximos,
        'preventivos_vencidos_tabla': vencidos,
        'equipos_mas_correctivos': equipos_costosos,
    }


def dashboard_view(request):
    hoy = date.today()
    anio = int(request.GET.get('anio', hoy.year))
    mes = hoy.month

    cards = calcular_cards(anio, mes)
    grafico = calcular_grafico_gastos(anio)
    tablas = obtener_tablas_dashboard(anio, mes)

    return render(request, 'core/index.html', {
        **cards,
        **grafico,
        **tablas,
        'anio_seleccionado': anio,
        'anios_disponibles': list(range(hoy.year - 2, hoy.year + 3)),
    })


class AlertasMantenimientoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        actualizar_estados_vencidos()
        hoy = date.today()
        en_7_dias = hoy + timedelta(days=7)

        vencidos = MantenimientoPreventivo.objects.filter(
            estado='vencido',
        ).select_related('equipo')[:10]

        proximos = MantenimientoPreventivo.objects.filter(
            estado='pendiente',
            fecha_programada__range=[hoy, en_7_dias],
        ).select_related('equipo')

        alertas = []
        for m in vencidos:
            alertas.append({
                'tipo': 'vencido',
                'equipo': m.equipo.nombre,
                'fecha': m.fecha_programada.strftime('%d/%m/%Y'),
                'mensaje': 'Mantenimiento preventivo vencido',
            })
        for m in proximos:
            alertas.append({
                'tipo': 'proximo',
                'equipo': m.equipo.nombre,
                'fecha': m.fecha_programada.strftime('%d/%m/%Y'),
                'mensaje': 'Preventivo programado próximamente',
            })

        return Response({
            'cantidad': len(alertas),
            'alertas': alertas,
        })
