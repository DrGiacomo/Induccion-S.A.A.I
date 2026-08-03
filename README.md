# S.A.A.I

**Sistema de Ayuda Automatizado para la Inducción.**

Un buscador privado del conocimiento de una empresa. Alguien recién llegado escribe una palabra
—incluida la jerga interna del área— y obtiene qué significa *en esta empresa*, quién la maneja y
dónde está documentada, **sin tener que interrumpir a un compañero**.

No es una plataforma de cursos. Es un buscador con permisos por área.

---

## Cómo levantarlo desde cero

Probado en Windows. En Linux o macOS cambia `venv\Scripts\` por `venv/bin/`.

### 1. Requisitos

| | Versión usada |
|---|---|
| Python | 3.14 |
| PostgreSQL | 17 |
| Node.js | ≥ 20.19 |

### 2. Base de datos

Con PostgreSQL instalado y corriendo:

```sql
CREATE DATABASE saai;
CREATE USER saai_user WITH PASSWORD 'la-que-tu-elijas';
GRANT ALL PRIVILEGES ON DATABASE saai TO saai_user;
ALTER DATABASE saai OWNER TO saai_user;
```

Y dentro de la base `saai`, las extensiones de búsqueda:

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;   -- que "logistica" encuentre "logística"
CREATE EXTENSION IF NOT EXISTS pg_trgm;    -- tolerancia a errores de tipeo
```

### 3. Backend

```bash
cd Backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
```

Abre `.env` y rellena los valores. Para generar tu clave:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Luego:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend en <http://localhost:8000> · panel de administración en `/admin/`.

### 4. Frontend

```bash
cd Frontend
npm install
npm run dev
```

Frontend en <http://localhost:5173>.

---

## Estructura

```
Backend/
  comun/           modelos abstractos compartidos (auditoría, estados)
  usuarios/        Usuario, Área, pertenencias, tipos de identificación
  contenido/       Término, Cargo, Documento, sinónimos, menciones
  busqueda/        historial personal y contadores anónimos
  reportes/        dashboard y certificados (Fase 5)
  induccion/       configuración del proyecto
Frontend/
  src/views/       pantallas
  src/api/         cliente HTTP
```

---

## Reglas del repositorio

**Solo se versiona código fuente.** Nunca entran a git:

- Secretos: `.env`, claves, contraseñas, certificados.
- Archivos subidos por los usuarios (`media/`, `repositorio/`).
- La documentación del proyecto (`Docs/`, `curva/`), que vive solo en el disco del autor.
- Material de otros proyectos o de terceros.

Ante la duda, no se sube. Revisa `git status` antes de cada commit.

---

## Documentación

La documentación completa está en `Docs/`, **fuera del control de versiones**:

| Archivo | Qué responde |
|---|---|
| `Docs/BIBLIA_PROYECTO.md` | Por qué existe. Manda sobre todo lo demás |
| `Docs/FEATURES.md` | Qué hay que construir y en qué estado está |
| `Docs/PLAN_PASO_A_PASO.md` | En qué orden. Empieza por el campo **Paso actual** |
| `Docs/avance/` | Qué se hizo en cada paso cerrado, con el código |
| `curva/` | Bitácora de aciertos y errores por jornada |
