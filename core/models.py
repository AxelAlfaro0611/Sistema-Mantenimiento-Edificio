from datetime import date

from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Sum


CATEGORIA_EQUIPO_CHOICES = [
    ('ascensor', 'Ascensores'),
    ('aire_acondicionado', 'Aire acondicionado'),
    ('seguridad', 'Sistemas de seguridad y control'),
    ('incendios', 'Sistema contra incendios'),
    ('electrico', 'Instalaciones eléctricas'),
    ('plomeria', 'Plomería y sanitarios'),
    ('generadores', 'Generadores y respaldo eléctrico'),
    ('otros', 'Otros'),
]

FRECUENCIA_CHOICES = [
    ('mensual', 'Mensual'),
    ('bimestral', 'Bimestral'),
    ('trimestral', 'Trimestral'),
    ('semestral', 'Semestral'),
    ('anual', 'Anual'),
]

FRECUENCIA_MESES = {
    'mensual': 1,
    'bimestral': 2,
    'trimestral': 3,
    'semestral': 6,
    'anual': 12,
}


def sumar_meses(fecha, meses):
    """Suma meses a una fecha manteniendo el día cuando es posible."""
    mes = fecha.month - 1 + meses
    anio = fecha.year + mes // 12
    mes = mes % 12 + 1
    dia = min(fecha.day, [31, 29 if anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0) else 28,
                          31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    return date(anio, mes, dia)


class Administrador(AbstractUser):
    pass


class Equipo(models.Model):
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_EQUIPO_CHOICES, default='otros')
    ubicacion = models.CharField(max_length=200)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    frecuencia_preventiva = models.CharField(max_length=20, choices=FRECUENCIA_CHOICES, default='mensual')
    fecha_base_programacion = models.DateField(help_text='Fecha de referencia para el cronograma anual')
    proveedor_servicio = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['categoria', 'nombre']
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'

    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"

    def _intervalo_meses(self):
        return FRECUENCIA_MESES.get(self.frecuencia_preventiva, 1)

    def calcular_fechas_cronograma_anual(self, anio):
        """Devuelve las fechas que deberían existir en un año según frecuencia y fecha base."""
        if anio < self.fecha_base_programacion.year:
            return []

        meses = self._intervalo_meses()
        inicio = date(anio, 1, 1)
        fin = date(anio, 12, 31)
        fecha = self.fecha_base_programacion

        while fecha.year < anio:
            fecha = sumar_meses(fecha, meses)
        while fecha.year > anio:
            fecha = sumar_meses(fecha, -meses)

        fechas = []
        while fecha <= fin:
            if fecha >= inicio and fecha >= self.fecha_base_programacion:
                fechas.append(fecha)
            fecha = sumar_meses(fecha, meses)
        return fechas

    def generar_cronograma_anual(self, anio, actualizar=False):
        """
        Genera las fechas programadas de mantenimiento preventivo para un año.
        Si actualizar=True, elimina pendientes/vencidos obsoletos (p. ej. tras cambiar
        frecuencia o fecha base) y recrea el cronograma. Los ejecutados se conservan.
        """
        fechas_esperadas = set(self.calcular_fechas_cronograma_anual(anio))
        eliminados = 0

        if actualizar:
            obsoletos = self.mantenimientos_preventivos.filter(
                fecha_programada__year=anio,
                estado__in=['pendiente', 'vencido'],
            ).exclude(fecha_programada__in=fechas_esperadas)
            eliminados = obsoletos.count()
            obsoletos.delete()

        creados = 0
        for fecha in sorted(fechas_esperadas):
            _, created = MantenimientoPreventivo.objects.get_or_create(
                equipo=self,
                fecha_programada=fecha,
                defaults={'estado': 'pendiente'},
            )
            if created:
                creados += 1

        return {'creados': creados, 'eliminados': eliminados, 'total': len(fechas_esperadas)}

    @classmethod
    def rango_anios_cronograma(cls, referencia=None):
        """Años que se planifican y actualizan con un solo clic."""
        hoy = referencia or date.today()
        return list(range(hoy.year - 1, hoy.year + 3))

    def actualizar_cronograma_completo(self, anios=None):
        """Recalcula el cronograma en todos los años del rango habitual."""
        anios = anios or self.rango_anios_cronograma()
        resumen = {'creados': 0, 'eliminados': 0, 'anios': len(anios), 'anio_inicio': anios[0], 'anio_fin': anios[-1]}
        for anio in anios:
            r = self.generar_cronograma_anual(anio, actualizar=True)
            resumen['creados'] += r['creados']
            resumen['eliminados'] += r['eliminados']
        return resumen

    @property
    def total_gastos_correctivos(self):
        return self.mantenimientos_correctivos.aggregate(total=Sum('costo'))['total'] or 0

    @property
    def total_gastos_preventivos(self):
        return self.mantenimientos_preventivos.filter(estado='ejecutado').aggregate(total=Sum('costo'))['total'] or 0

    @property
    def total_gastos_compras(self):
        return self.compras.aggregate(total=Sum('costo'))['total'] or 0

    @property
    def total_gastos(self):
        return self.total_gastos_correctivos + self.total_gastos_preventivos + self.total_gastos_compras

    @property
    def cantidad_correctivos(self):
        return self.mantenimientos_correctivos.count()


class MantenimientoPreventivo(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('ejecutado', 'Ejecutado'),
        ('vencido', 'Vencido'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='mantenimientos_preventivos')
    fecha_programada = models.DateField()
    fecha_ejecutada = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    descripcion = models.TextField(blank=True, verbose_name='Descripción del trabajo')
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tecnico_responsable = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_programada']
        verbose_name = 'Mantenimiento preventivo'
        verbose_name_plural = 'Mantenimientos preventivos'
        unique_together = ['equipo', 'fecha_programada']

    def __str__(self):
        return f"Preventivo {self.equipo.nombre} - {self.fecha_programada.strftime('%d/%m/%Y')}"

    def actualizar_estado_vencido(self):
        if self.estado == 'pendiente' and self.fecha_programada < date.today():
            self.estado = 'vencido'
            self.save(update_fields=['estado'])

    def marcar_ejecutado(self, fecha_ejecutada=None, descripcion='', costo=0, tecnico='', observaciones=''):
        self.estado = 'ejecutado'
        self.fecha_ejecutada = fecha_ejecutada or date.today()
        if descripcion:
            self.descripcion = descripcion
        self.costo = costo
        if tecnico:
            self.tecnico_responsable = tecnico
        if observaciones:
            self.observaciones = observaciones
        self.save()


class MantenimientoCorrectivo(models.Model):
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    ESTADO_CHOICES = [
        ('reportado', 'Reportado'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]

    equipo = models.ForeignKey(
        Equipo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='mantenimientos_correctivos'
    )
    area = models.CharField(max_length=200, help_text='Área o zona del edificio')
    ubicacion = models.CharField(max_length=200)
    fecha = models.DateField(default=date.today)
    descripcion = models.TextField()
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    proveedor = models.CharField(max_length=200, blank=True)
    prioridad = models.CharField(max_length=20, choices=PRIORIDAD_CHOICES, default='baja')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='reportado')
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Mantenimiento correctivo'
        verbose_name_plural = 'Mantenimientos correctivos'

    def __str__(self):
        ref = self.equipo.nombre if self.equipo else self.area
        return f"Correctivo {ref} - {self.fecha.strftime('%d/%m/%Y')}"


UNIDAD_COMPRA_CHOICES = [
    ('unidad', 'Unidad'),
    ('galon', 'Galón'),
    ('litro', 'Litro'),
    ('metro', 'Metro'),
    ('kilogramo', 'Kilogramo'),
    ('caja', 'Caja'),
    ('rollo', 'Rollo'),
    ('bolsa', 'Bolsa'),
    ('saco', 'Saco'),
    ('kit', 'Kit'),
    ('par', 'Par'),
]


class CompraInsumo(models.Model):
    descripcion = models.CharField(max_length=255)
    equipo = models.ForeignKey(
        Equipo, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras'
    )
    area = models.CharField(max_length=200, blank=True, help_text='Área destino si no hay equipo asociado')
    fecha_compra = models.DateField(default=date.today)
    proveedor = models.CharField(max_length=200)
    costo = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unidad = models.CharField(max_length=50, choices=UNIDAD_COMPRA_CHOICES, default='unidad')
    ubicacion_instalacion = models.CharField(max_length=200, blank=True)
    observaciones = models.TextField(blank=True)
    registrado_por = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_compra']
        verbose_name = 'Compra / Insumo'
        verbose_name_plural = 'Compras e insumos'

    def __str__(self):
        return f"{self.descripcion} - S/ {self.costo}"
