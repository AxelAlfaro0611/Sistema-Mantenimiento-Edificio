# Sistema de Mantenimiento de Edificio

Aplicación web para gestionar el mantenimiento preventivo y correctivo de equipos de un edificio, compras de insumos, cronogramas anuales, alertas y reportes de gastos.

**Stack:** Django 5, SQLite, plantilla SB Admin 2, autenticación con modelo `Administrador`.

**Zona horaria:** Perú (`America/Lima`).

---

## Módulos del sistema

| Módulo | Descripción |
|--------|-------------|
| **Equipos** | Registro de ascensores, A/C, seguridad, incendios, etc. con frecuencia preventiva y fecha base |
| **Preventivos** | Cronograma automático, listado, ejecución y estados (pendiente / ejecutado / vencido) |
| **Correctivos** | Reparaciones por falla, prioridad, costo y proveedor |
| **Compras e insumos** | Materiales y repuestos asociados a equipos o áreas |
| **Búsqueda central** | Filtro unificado por equipo, mes, año y tipo de registro |
| **Reportes** | Gastos y cantidad de correctivos por equipo y año |
| **Dashboard** | Resumen y alertas de mantenimientos próximos o vencidos |

---

## Requisitos

- Python 3.10 o superior
- pip

Dependencias en `requirements.txt`.

---

## Instalación

```bash
# 1. Clonar o abrir el proyecto
cd MANTENIMIENTO_DE_EDIFICIO

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate  # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate

# 5. Crear usuario administrador
python manage.py createsuperuser
```

También puede usar el usuario de prueba si ya fue creado:

- **Usuario:** `admin`
- **Contraseña:** `admin123`

---

## Ejecutar el proyecto

```bash
python manage.py runserver
```

Abrir en el navegador: **http://127.0.0.1:8000/**

La pantalla de inicio redirige al login. Tras iniciar sesión, accede al dashboard.

---

## Datos de demostración (opcional)

Para cargar equipos y registros de ejemplo:

```bash
python manage.py cargar_datos_demo
```

Para vaciar y volver a cargar:

```bash
python manage.py cargar_datos_demo --limpiar
```

---

## Guía de uso rápida

### 1. Registrar equipos

1. Menú **Equipos → Registrar equipo**
2. Complete nombre, categoría, ubicación, **frecuencia preventiva** y **fecha base**
3. Al guardar, el sistema genera el cronograma del año actual

### 2. Cronograma preventivo

- En el detalle del equipo use **Actualizar cronograma (todos los años)** para generar/ajustar fechas del rango planificado
- **Cronograma anual** muestra todos los equipos por mes
- **Listado preventivos** permite filtrar por año, mes y equipo; marque como ejecutado con el botón ✓

### 3. Correctivos y compras

- Registre averías en **Correctivos → Registrar**
- Registre insumos en **Compras → Registrar**
- Asocie el registro a un equipo cuando corresponda

### 4. Consultas y reportes

- **Búsqueda central:** filtros por equipo, mes, año y tipo
- **Reportes por equipo:** gastos del año seleccionado (correctivos, preventivos ejecutados y compras)

### 5. Fecha y hora

Todas las fechas del sistema usan la zona horaria de **Perú (UTC-5)**. Los mantenimientos vencidos se actualizan automáticamente al consultar listados.

---

## Estructura principal

```
MANTENIMIENTO_DE_EDIFICIO/
├── academia/          # Configuración Django (settings, urls)
├── core/              # App principal
│   ├── models.py      # Equipo, Preventivo, Correctivo, Compra
│   ├── views.py       # Vistas del sistema
│   ├── forms.py       # Formularios
│   ├── templates/     # Plantillas HTML
│   └── static/        # CSS, JS, SB Admin 2
├── db.sqlite3         # Base de datos (desarrollo)
├── manage.py
└── requirements.txt
```

---

## Comandos útiles

```bash
python manage.py migrate          # Aplicar migraciones
python manage.py runserver        # Servidor de desarrollo
python manage.py createsuperuser  # Nuevo administrador
python manage.py check            # Verificar configuración
```

---

## Notas

- Proyecto configurado para **desarrollo local** (`DEBUG = True`). Para producción, revise `SECRET_KEY`, `ALLOWED_HOSTS` y el servidor WSGI.
- La base de datos por defecto es **SQLite**. Para entornos grandes puede migrarse a PostgreSQL o MySQL.
- Interfaz con tipografía compacta y barra lateral ajustada (`core/static/css/mantenimiento.css`).

---

## Licencia del tema

La plantilla visual [SB Admin 2](https://startbootstrap.com/theme/sb-admin-2/) de Start Bootstrap se distribuye bajo licencia MIT.
