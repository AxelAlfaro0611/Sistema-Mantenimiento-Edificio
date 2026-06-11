from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password

from .models import (
    Administrador,
    Equipo,
    MantenimientoPreventivo,
    MantenimientoCorrectivo,
    CompraInsumo,
)


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = [
            'nombre', 'categoria', 'ubicacion', 'marca', 'modelo', 'numero_serie',
            'frecuencia_preventiva', 'fecha_base_programacion', 'proveedor_servicio',
            'observaciones', 'activo',
        ]
        widgets = {
            'fecha_base_programacion': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
        self.fields['categoria'].widget.attrs['class'] = 'form-control'
        self.fields['frecuencia_preventiva'].widget.attrs['class'] = 'form-control'
        self.fields['activo'].widget.attrs['class'] = 'form-check-input'


class MantenimientoPreventivoForm(forms.ModelForm):
    class Meta:
        model = MantenimientoPreventivo
        fields = [
            'equipo', 'fecha_programada', 'fecha_ejecutada', 'estado',
            'descripcion', 'costo', 'tecnico_responsable', 'observaciones',
        ]
        widgets = {
            'fecha_programada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_ejecutada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('descripcion', 'observaciones', 'fecha_programada', 'fecha_ejecutada'):
                field.widget.attrs['class'] = 'form-control'
        self.fields['equipo'].queryset = Equipo.objects.filter(activo=True)


class EjecutarPreventivoForm(forms.Form):
    fecha_ejecutada = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de ejecución',
    )
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        label='Descripción del trabajo',
    )
    costo = forms.DecimalField(
        max_digits=10, decimal_places=2, initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='Costo (S/)',
    )
    tecnico_responsable = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Técnico / responsable',
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        label='Observaciones',
    )


class MantenimientoCorrectivoForm(forms.ModelForm):
    class Meta:
        model = MantenimientoCorrectivo
        fields = [
            'equipo', 'area', 'ubicacion', 'fecha', 'descripcion', 'costo',
            'proveedor', 'prioridad', 'estado', 'observaciones',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('descripcion', 'observaciones', 'fecha'):
                field.widget.attrs['class'] = 'form-control'
        self.fields['equipo'].queryset = Equipo.objects.filter(activo=True)
        self.fields['equipo'].required = False
        if not self.instance.pk:
            self.fields['prioridad'].initial = 'baja'


class CompraInsumoForm(forms.ModelForm):
    class Meta:
        model = CompraInsumo
        fields = [
            'descripcion', 'equipo', 'area', 'fecha_compra', 'proveedor',
            'costo', 'cantidad', 'unidad', 'ubicacion_instalacion', 'observaciones',
        ]
        widgets = {
            'fecha_compra': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'unidad': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('observaciones', 'fecha_compra', 'unidad'):
                field.widget.attrs['class'] = 'form-control'
        self.fields['equipo'].queryset = Equipo.objects.filter(activo=True)
        self.fields['equipo'].required = False


class AdministradorForm(UserCreationForm):
    class Meta:
        model = Administrador
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'


class AdministradorEditForm(forms.ModelForm):
    nueva_clave = forms.CharField(
        required=False,
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text='Opcional. Déjela en blanco si no desea cambiarla.',
    )
    confirmar_clave = forms.CharField(
        required=False,
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = Administrador
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = Administrador.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean(self):
        cleaned = super().clean()
        clave = cleaned.get('nueva_clave')
        confirmar = cleaned.get('confirmar_clave')
        if clave or confirmar:
            if clave != confirmar:
                self.add_error('confirmar_clave', 'Las contraseñas no coinciden.')
            elif clave:
                validate_password(clave, self.instance)
        return cleaned

    def save(self, commit=True):
        admin = super().save(commit=False)
        clave = self.cleaned_data.get('nueva_clave')
        if clave:
            admin.set_password(clave)
        if commit:
            admin.save()
        return admin


def _opciones_anio_busqueda():
    hoy = date.today()
    return [('', '---------')] + [
        (str(y), str(y)) for y in range(hoy.year - 2, hoy.year + 3)
    ]


class BusquedaCentralForm(forms.Form):
    equipo = forms.ModelChoiceField(
        queryset=Equipo.objects.filter(activo=True),
        required=False,
        label='Equipo',
        empty_label='---------',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    mes = forms.ChoiceField(
        required=False,
        label='Mes',
        choices=[('', 'Todos')] + [
            (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
            (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
            (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    anio = forms.ChoiceField(
        required=False,
        label='Año',
        choices=[('', '---------')],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    tipo = forms.ChoiceField(
        required=False,
        label='Tipo de registro',
        choices=[
            ('', 'Todos'),
            ('preventivo', 'Preventivos'),
            ('correctivo', 'Correctivos'),
            ('compra', 'Compras e insumos'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        anio_choices = _opciones_anio_busqueda()
        if self.data:
            anio_val = self.data.get('anio', '').strip()
            if anio_val and anio_val not in dict(anio_choices):
                anio_choices.insert(1, (anio_val, anio_val))
        self.fields['anio'].choices = anio_choices
