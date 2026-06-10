from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    CompraInsumo,
    Equipo,
    MantenimientoCorrectivo,
    MantenimientoPreventivo,
)


EQUIPOS_DEMO = [
    {
        'nombre': 'Ascensor principal - Torre A',
        'categoria': 'ascensor',
        'ubicacion': 'Torre A - Shaft central',
        'marca': 'Otis',
        'modelo': 'Gen2',
        'numero_serie': 'OT-2021-0045',
        'frecuencia_preventiva': 'mensual',
        'fecha_base_programacion': date(2026, 1, 5),
        'proveedor_servicio': 'Ascensores del Sur S.A.C.',
    },
    {
        'nombre': 'Ascensor de servicio - Torre B',
        'categoria': 'ascensor',
        'ubicacion': 'Torre B - Acceso estacionamiento',
        'marca': 'Schindler',
        'modelo': '3300',
        'numero_serie': 'SC-2019-1120',
        'frecuencia_preventiva': 'mensual',
        'fecha_base_programacion': date(2026, 1, 10),
        'proveedor_servicio': 'Ascensores del Sur S.A.C.',
    },
    {
        'nombre': 'Chiller central planta 1',
        'categoria': 'aire_acondicionado',
        'ubicacion': 'Azotea - Planta de frío',
        'marca': 'Carrier',
        'modelo': '30XW',
        'numero_serie': 'CR-30XW-8871',
        'frecuencia_preventiva': 'trimestral',
        'fecha_base_programacion': date(2026, 1, 15),
        'proveedor_servicio': 'Clima Total EIRL',
    },
    {
        'nombre': 'Split lobby principal',
        'categoria': 'aire_acondicionado',
        'ubicacion': 'Primer piso - Lobby',
        'marca': 'Daikin',
        'modelo': 'FTXM35',
        'numero_serie': 'DK-FTXM-2234',
        'frecuencia_preventiva': 'bimestral',
        'fecha_base_programacion': date(2026, 2, 1),
        'proveedor_servicio': 'Clima Total EIRL',
    },
    {
        'nombre': 'CCTV y control de acceso',
        'categoria': 'seguridad',
        'ubicacion': 'Todo el edificio',
        'marca': 'Hikvision',
        'modelo': 'Sistema integrado',
        'numero_serie': 'HK-CCTV-001',
        'frecuencia_preventiva': 'trimestral',
        'fecha_base_programacion': date(2026, 1, 20),
        'proveedor_servicio': 'Seguridad Integral SAC',
    },
    {
        'nombre': 'Sistema de detección y extinción',
        'categoria': 'incendios',
        'ubicacion': 'Sótanos y niveles 1-12',
        'marca': 'Notifier',
        'modelo': 'NFS2-3030',
        'numero_serie': 'NF-3030-556',
        'frecuencia_preventiva': 'semestral',
        'fecha_base_programacion': date(2026, 3, 1),
        'proveedor_servicio': 'Protección Contra Incendios SAC',
    },
    {
        'nombre': 'Tablero general BT',
        'categoria': 'electrico',
        'ubicacion': 'Sótano 2 - Cuarto eléctrico',
        'marca': 'ABB',
        'modelo': 'Tmax XT4',
        'numero_serie': 'ABB-TG-9901',
        'frecuencia_preventiva': 'semestral',
        'fecha_base_programacion': date(2026, 4, 1),
        'proveedor_servicio': 'Electro Mantenimiento EIRL',
    },
    {
        'nombre': 'Bomba de presión de agua',
        'categoria': 'plomeria',
        'ubicacion': 'Sótano 1 - Cisterna',
        'marca': 'Grundfos',
        'modelo': 'CR 32-4',
        'numero_serie': 'GR-CR32-778',
        'frecuencia_preventiva': 'bimestral',
        'fecha_base_programacion': date(2026, 1, 8),
        'proveedor_servicio': 'Plomería Express SAC',
    },
    {
        'nombre': 'Generador de emergencia 250 KVA',
        'categoria': 'generadores',
        'ubicacion': 'Azotea - Casa de máquinas',
        'marca': 'Cummins',
        'modelo': 'C250 D5',
        'numero_serie': 'CM-C250-4412',
        'frecuencia_preventiva': 'mensual',
        'fecha_base_programacion': date(2026, 1, 3),
        'proveedor_servicio': 'PowerGen Servicios SAC',
    },
    {
        'nombre': 'Portón vehicular automático',
        'categoria': 'otros',
        'ubicacion': 'Estacionamiento - Acceso principal',
        'marca': 'Nice',
        'modelo': 'Robus 600',
        'numero_serie': 'NC-RB600-88',
        'frecuencia_preventiva': 'trimestral',
        'fecha_base_programacion': date(2026, 2, 15),
        'proveedor_servicio': 'Automatización Lima SAC',
    },
]


class Command(BaseCommand):
    help = 'Carga equipos, mantenimientos y compras de demostración para probar el sistema.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina datos demo existentes antes de cargar.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['limpiar']:
            CompraInsumo.objects.all().delete()
            MantenimientoCorrectivo.objects.all().delete()
            MantenimientoPreventivo.objects.all().delete()
            Equipo.objects.all().delete()
            self.stdout.write('Datos anteriores eliminados.')

        if Equipo.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Ya existen equipos registrados. Use --limpiar para reemplazar los datos demo.'
            ))
            return

        anio = date.today().year
        equipos = {}

        for datos in EQUIPOS_DEMO:
            equipo = Equipo.objects.create(**datos)
            equipo.generar_cronograma_anual(anio)
            equipos[equipo.nombre] = equipo
            self.stdout.write(f'  + Equipo: {equipo.nombre}')

        asc_a = equipos['Ascensor principal - Torre A']
        asc_b = equipos['Ascensor de servicio - Torre B']
        chiller = equipos['Chiller central planta 1']
        bomba = equipos['Bomba de presión de agua']
        generador = equipos['Generador de emergencia 250 KVA']
        porton = equipos['Portón vehicular automático']

        hoy = date.today()

        preventivos_ejecutados = [
            (asc_a, hoy - timedelta(days=45), 'Revisión mensual: lubricación, limpieza foso y prueba de frenos.', Decimal('380.00'), 'J. Mendoza'),
            (asc_a, hoy - timedelta(days=15), 'Mantenimiento mensual programado.', Decimal('380.00'), 'J. Mendoza'),
            (generador, hoy - timedelta(days=30), 'Prueba en carga, cambio de filtros y revisión de batería.', Decimal('520.00'), 'R. Vargas'),
            (generador, hoy - timedelta(days=5), 'Mantenimiento mensual: niveles, correas y arranque automático.', Decimal('520.00'), 'R. Vargas'),
            (bomba, hoy - timedelta(days=60), 'Limpieza de impulsor y verificación de presión.', Decimal('220.00'), 'L. Quispe'),
            (chiller, hoy - timedelta(days=20), 'Revisión trimestral: condensador, refrigerante y alarmas.', Decimal('1450.00'), 'M. Rojas'),
        ]

        for equipo, fecha_ejec, desc, costo, tecnico in preventivos_ejecutados:
            preventivo = MantenimientoPreventivo.objects.filter(
                equipo=equipo,
                fecha_programada__lte=fecha_ejec,
                estado__in=['pendiente', 'vencido'],
            ).order_by('-fecha_programada').first()
            if preventivo:
                preventivo.marcar_ejecutado(
                    fecha_ejecutada=fecha_ejec,
                    descripcion=desc,
                    costo=costo,
                    tecnico=tecnico,
                )

        correctivos = [
            {
                'equipo': asc_b,
                'area': 'Torre B',
                'ubicacion': 'Ascensor de servicio',
                'fecha': hoy - timedelta(days=12),
                'descripcion': 'Puerta del ascensor no cerraba correctamente. Se ajustó sensor y rieles.',
                'costo': Decimal('650.00'),
                'proveedor': 'Ascensores del Sur S.A.C.',
                'prioridad': 'alta',
                'estado': 'completado',
            },
            {
                'equipo': asc_b,
                'area': 'Torre B',
                'ubicacion': 'Cabina ascensor servicio',
                'fecha': hoy - timedelta(days=90),
                'descripcion': 'Ruido anormal en motor. Reemplazo de rodamiento auxiliar.',
                'costo': Decimal('1200.00'),
                'proveedor': 'Ascensores del Sur S.A.C.',
                'prioridad': 'urgente',
                'estado': 'completado',
            },
            {
                'equipo': porton,
                'area': 'Estacionamiento',
                'ubicacion': 'Acceso vehicular',
                'fecha': hoy - timedelta(days=8),
                'descripcion': 'Portón quedó trabado en apertura. Cambio de fin de carrera y recableado.',
                'costo': Decimal('480.00'),
                'proveedor': 'Automatización Lima SAC',
                'prioridad': 'alta',
                'estado': 'completado',
            },
            {
                'equipo': None,
                'area': 'Piso 7 - Hall',
                'ubicacion': 'Iluminación pasillo norte',
                'fecha': hoy - timedelta(days=25),
                'descripcion': 'Corte de luz en luminarias del hall. Reparación de circuito derivado.',
                'costo': Decimal('180.00'),
                'proveedor': 'Electro Mantenimiento EIRL',
                'prioridad': 'media',
                'estado': 'completado',
            },
            {
                'equipo': bomba,
                'area': 'Sótano 1',
                'ubicacion': 'Cisterna',
                'fecha': hoy - timedelta(days=3),
                'descripcion': 'Fuga menor en empaque de bomba. Cambio de sello mecánico.',
                'costo': Decimal('340.00'),
                'proveedor': 'Plomería Express SAC',
                'prioridad': 'alta',
                'estado': 'en_proceso',
            },
        ]

        for c in correctivos:
            MantenimientoCorrectivo.objects.create(**c)

        compras = [
            {
                'descripcion': 'Filtros de aire para chiller',
                'equipo': chiller,
                'area': '',
                'fecha_compra': hoy - timedelta(days=22),
                'proveedor': 'Repuestos HVAC SAC',
                'costo': Decimal('420.00'),
                'cantidad': Decimal('4'),
                'unidad': 'unidad',
                'ubicacion_instalacion': 'Azotea - Planta de frío',
            },
            {
                'descripcion': 'Lubricante para ascensores',
                'equipo': asc_a,
                'area': '',
                'fecha_compra': hoy - timedelta(days=18),
                'proveedor': 'Ascensores del Sur S.A.C.',
                'costo': Decimal('95.00'),
                'cantidad': Decimal('2'),
                'unidad': 'galon',
                'ubicacion_instalacion': 'Torre A y Torre B',
            },
            {
                'descripcion': 'Sello mecánico bomba Grundfos',
                'equipo': bomba,
                'area': '',
                'fecha_compra': hoy - timedelta(days=4),
                'proveedor': 'Plomería Express SAC',
                'costo': Decimal('185.00'),
                'cantidad': Decimal('1'),
                'unidad': 'unidad',
                'ubicacion_instalacion': 'Sótano 1 - Cisterna',
            },
            {
                'descripcion': 'Lámparas LED 18W',
                'equipo': None,
                'area': 'Piso 7 - Hall',
                'fecha_compra': hoy - timedelta(days=26),
                'proveedor': 'Electro Sur EIRL',
                'costo': Decimal('156.00'),
                'cantidad': Decimal('12'),
                'unidad': 'unidad',
                'ubicacion_instalacion': 'Pasillo norte piso 7',
            },
            {
                'descripcion': 'Aceite motor generador Cummins',
                'equipo': generador,
                'area': '',
                'fecha_compra': hoy - timedelta(days=32),
                'proveedor': 'PowerGen Servicios SAC',
                'costo': Decimal('280.00'),
                'cantidad': Decimal('20'),
                'unidad': 'litro',
                'ubicacion_instalacion': 'Azotea - Generador',
            },
            {
                'descripcion': 'Fin de carrera para portón Nice',
                'equipo': porton,
                'area': '',
                'fecha_compra': hoy - timedelta(days=9),
                'proveedor': 'Automatización Lima SAC',
                'costo': Decimal('75.00'),
                'cantidad': Decimal('2'),
                'unidad': 'unidad',
                'ubicacion_instalacion': 'Estacionamiento acceso principal',
            },
        ]

        for c in compras:
            CompraInsumo.objects.create(**c)

        total_preventivos = MantenimientoPreventivo.objects.count()
        total_correctivos = MantenimientoCorrectivo.objects.count()
        total_compras = CompraInsumo.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'\nDatos demo cargados correctamente:\n'
            f'  - {len(EQUIPOS_DEMO)} equipos\n'
            f'  - {total_preventivos} registros preventivos (cronograma {anio})\n'
            f'  - {total_correctivos} correctivos\n'
            f'  - {total_compras} compras/insumos\n'
        ))
