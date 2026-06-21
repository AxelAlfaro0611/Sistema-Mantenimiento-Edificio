# Despliegue en PythonAnywhere

Guía rápida para publicar cambios del proyecto en la nube.

**Sitio:** https://mantenimientodeedificio.pythonanywhere.com  
**Proyecto en el servidor:** `~/Sistema-Mantenimiento-Edificio`  
**Entorno virtual:** `mantenimiento-env`

---

## 1. En tu PC (siempre)

```bash
git add .
git commit -m "Descripción breve del cambio"
git push origin main
```

---

## 2. En PythonAnywhere → Consoles → Bash

Entra al proyecto:

```bash
cd ~/Sistema-Mantenimiento-Edificio
workon mantenimiento-env
```

Descarga cambios (con respaldo de la base de datos):

```bash
cp db.sqlite3 ~/db_backup.sqlite3
git checkout -- db.sqlite3
git pull origin main
cp ~/db_backup.sqlite3 db.sqlite3
```

> Si `git pull` falla solo por `requirements.txt`:
> `git checkout -- requirements.txt` y vuelve a hacer `git pull`.

---

## 3. Comandos según el tipo de cambio

| Cambiaste… | Ejecuta |
|------------|---------|
| Modelos / migraciones en `core/migrations/` | `python manage.py migrate` |
| CSS o JS en `core/static/` | `python manage.py collectstatic --noinput` |
| Solo plantillas HTML o Python (views, forms) | Nada extra |

Ejemplos:

```bash
# Si hay migraciones nuevas
python manage.py migrate

# Si tocaste mantenimiento.css u otros estáticos
python manage.py collectstatic --noinput
```

---

## 4. Recargar la aplicación (siempre)

1. Pestaña **Web** en PythonAnywhere.
2. Botón verde **Reload**.
3. Esperar 5–10 segundos.

Probar en **ventana de incógnito** o con Ctrl+Shift+R si no ves cambios (caché del navegador).

---

## Checklist completo (copiar y pegar)

```bash
cd ~/Sistema-Mantenimiento-Edificio
workon mantenimiento-env
cp db.sqlite3 ~/db_backup.sqlite3
git checkout -- db.sqlite3
git pull origin main
cp ~/db_backup.sqlite3 db.sqlite3
python manage.py migrate
python manage.py collectstatic --noinput
```

Luego: **Web → Reload**.

> Omite `migrate` si no hubo cambios en modelos.  
> Omite `collectstatic` si no hubo cambios en CSS/JS estáticos.

---

## Errores frecuentes

| Error | Solución |
|-------|----------|
| `fatal: not a git repository` | Estás en `~`. Ejecuta `cd ~/Sistema-Mantenimiento-Edificio` primero. |
| `db.sqlite3 would be overwritten` | Usa el bloque con `cp`, `git checkout -- db.sqlite3` y `git pull`. |
| Cambios no se ven en la web | **Reload** en Web + probar en incógnito. |
| CSS no actualiza | Falta `collectstatic --noinput`. |
| Categorías / campos nuevos no aparecen | Falta `migrate` o el `git pull` no terminó (revisar que no diga `Aborting`). |

---

## Usuario de prueba (local / demo)

- **Usuario:** `admin`
- **Contraseña:** `admin123`

En producción puede ser distinto si creaste otro administrador.
