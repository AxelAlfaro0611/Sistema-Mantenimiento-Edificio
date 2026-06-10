from rest_framework import serializers

from .models import Equipo, MantenimientoPreventivo, MantenimientoCorrectivo, CompraInsumo


class EquipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipo
        fields = '__all__'


class MantenimientoPreventivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MantenimientoPreventivo
        fields = '__all__'


class MantenimientoCorrectivoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MantenimientoCorrectivo
        fields = '__all__'


class CompraInsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompraInsumo
        fields = '__all__'
