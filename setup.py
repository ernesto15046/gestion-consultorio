#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║   CONSULTORIO PEDIÁTRICO — Script de Configuración       ║
║   Ejecutar una sola vez después de instalar el sistema   ║
║   Uso: python setup.py                                   ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import sys
import secrets
import getpass
import subprocess
from pathlib import Path

# ── Colores para la consola ──────────────────────────────
class C:
    TEAL   = '\033[96m'
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    BOLD   = '\033[1m'
    END    = '\033[0m'

def ok(msg):   print(f"{C.GREEN}  ✓  {msg}{C.END}")
def info(msg): print(f"{C.TEAL}  ℹ  {msg}{C.END}")
def warn(msg): print(f"{C.YELLOW}  ⚠  {msg}{C.END}")
def err(msg):  print(f"{C.RED}  ✗  {msg}{C.END}")
def title(msg):print(f"\n{C.BOLD}{C.TEAL}{msg}{C.END}")

# ── Banner ───────────────────────────────────────────────
print(f"""
{C.BOLD}{C.TEAL}
╔══════════════════════════════════════════════════════════╗
║       SISTEMA DE GESTIÓN — CONSULTORIO PEDIÁTRICO        ║
║              Asistente de Configuración Inicial          ║
╚══════════════════════════════════════════════════════════╝
{C.END}""")

BASE_DIR = Path(__file__).parent

# ════════════════════════════════════════════════════════
#  PASO 1: Verificar Python
# ════════════════════════════════════════════════════════
title("PASO 1 — Verificando entorno")
if sys.version_info < (3, 10):
    err(f"Se requiere Python 3.10+. Versión actual: {sys.version}")
    sys.exit(1)
ok(f"Python {sys.version.split()[0]}")

# ════════════════════════════════════════════════════════
#  PASO 2: Datos del médico
# ════════════════════════════════════════════════════════
title("PASO 2 — Datos del Médico")
info("Estos datos aparecerán en todos los documentos generados.")

nombre   = input("  Nombre completo del médico [Dr. Juan Pérez]: ").strip() or "Dr. Juan Pérez"
esp      = input("  Especialidad [Cirugía Pediátrica]: ").strip() or "Cirugía Pediátrica"
cedula   = input("  Cédula médica / No. de licencia [00000]: ").strip() or "00000"
tel      = input("  Teléfono [809-000-0000]: ").strip() or "809-000-0000"
email    = input("  Email [medico@consultorio.com]: ").strip() or "medico@consultorio.com"
direccion= input("  Dirección del consultorio: ").strip() or "Consultorio Médico"

# ════════════════════════════════════════════════════════
#  PASO 3: Base de datos
# ════════════════════════════════════════════════════════
title("PASO 3 — Configuración de Base de Datos")
info("Configura la conexión a PostgreSQL.")

db_host  = input("  Host PostgreSQL [localhost]: ").strip() or "localhost"
db_port  = input("  Puerto [5432]: ").strip() or "5432"
db_name  = input("  Nombre de la BD [consultorio_db]: ").strip() or "consultorio_db"
db_user  = input("  Usuario [medico]: ").strip() or "medico"
db_pass  = getpass.getpass("  Contraseña de la BD: ") or "CambiarEstaPassword123!"

# ════════════════════════════════════════════════════════
#  PASO 4: Usuario administrador
# ════════════════════════════════════════════════════════
title("PASO 4 — Usuario Administrador del Sistema")
admin_email = input("  Email del médico/admin: ").strip() or email
admin_pass  = getpass.getpass("  Contraseña para el sistema (mínimo 8 caracteres): ")
if len(admin_pass) < 8:
    warn("Contraseña muy corta. Usando contraseña temporal: Consultorio2024!")
    admin_pass = "Consultorio2024!"

# ════════════════════════════════════════════════════════
#  PASO 5: Crear .env
# ════════════════════════════════════════════════════════
title("PASO 5 — Generando archivo de configuración (.env)")

secret_key = secrets.token_hex(32)
env_content = f"""# GENERADO AUTOMÁTICAMENTE POR setup.py — {__import__('datetime').date.today()}

# Base de datos
DB_HOST={db_host}
DB_PORT={db_port}
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_pass}
DATABASE_URL=postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}

# Seguridad JWT
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Datos del médico
MEDICO_NOMBRE={nombre}
MEDICO_ESPECIALIDAD={esp}
MEDICO_CEDULA={cedula}
MEDICO_TEL={tel}
MEDICO_EMAIL={email}
MEDICO_DIRECCION={direccion}

# API
API_PORT=8000
WEB_PORT=80
CORS_ORIGINS=http://localhost,http://localhost:80,http://127.0.0.1

# PgAdmin (opcional)
PGADMIN_EMAIL=admin@consultorio.com
PGADMIN_PASSWORD={secrets.token_urlsafe(12)}
PGADMIN_PORT=5050
"""

env_path = BASE_DIR / ".env"
env_path.write_text(env_content, encoding='utf-8')
ok(f"Archivo .env creado en {env_path}")

# ════════════════════════════════════════════════════════
#  PASO 6: Crear directorios necesarios
# ════════════════════════════════════════════════════════
title("PASO 6 — Creando estructura de directorios")

dirs = [
    "backend/storage/documentos",
    "backend/storage/logos",
    "backups",
    "nginx",
    "logs",
]
for d in dirs:
    Path(BASE_DIR / d).mkdir(parents=True, exist_ok=True)
    ok(f"Directorio: {d}/")

# ════════════════════════════════════════════════════════
#  PASO 7: Instalar dependencias Python
# ════════════════════════════════════════════════════════
title("PASO 7 — Instalando dependencias Python")
req_path = BASE_DIR / "backend" / "requirements.txt"

if req_path.exists():
    info("Instalando paquetes de requirements.txt...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path), "-q"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok("Dependencias instaladas correctamente")
    else:
        warn(f"Algunos paquetes no se instalaron: {result.stderr[:200]}")
else:
    warn("No se encontró requirements.txt")

# ════════════════════════════════════════════════════════
#  PASO 8: Verificar conexión BD y crear usuario
# ════════════════════════════════════════════════════════
title("PASO 8 — Inicializando base de datos")

try:
    import psycopg2
    from passlib.context import CryptContext

    info(f"Conectando a PostgreSQL en {db_host}:{db_port}...")
    conn = psycopg2.connect(
        host=db_host, port=db_port, dbname=db_name,
        user=db_user, password=db_pass
    )
    conn.autocommit = True
    cur = conn.cursor()
    ok("Conexión exitosa a la base de datos")

    # Verificar que el esquema existe
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    n_tables = cur.fetchone()[0]

    if n_tables < 10:
        info("Ejecutando esquema SQL...")
        schema_path = BASE_DIR / "database" / "schema.sql"
        if schema_path.exists():
            cur.execute(schema_path.read_text(encoding='utf-8'))
            ok("Esquema creado correctamente")
        else:
            warn("No se encontró database/schema.sql. Ejecuta el esquema manualmente.")
    else:
        ok(f"Base de datos ya inicializada ({n_tables} tablas)")

    # Crear usuario médico administrador
    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_ctx.hash(admin_pass)

    cur.execute("""
        INSERT INTO usuarios (nombre, email, password_hash, rol, activo)
        VALUES (%s, %s, %s, 'medico', true)
        ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
    """, (nombre, admin_email, hashed))

    ok(f"Usuario administrador creado: {admin_email}")
    cur.close()
    conn.close()

except ImportError:
    warn("psycopg2 o passlib no disponible. Verifica la instalación.")
    warn("El usuario administrador deberá crearse manualmente.")
except Exception as e:
    warn(f"No se pudo conectar a la BD: {e}")
    warn("Verifica que PostgreSQL esté corriendo y los datos sean correctos.")
    warn("Puedes correr el esquema manualmente: psql -U medico -d consultorio_db -f database/schema.sql")

# ════════════════════════════════════════════════════════
#  RESUMEN FINAL
# ════════════════════════════════════════════════════════
print(f"""
{C.BOLD}{C.GREEN}
╔══════════════════════════════════════════════════════════╗
║               ✅  CONFIGURACIÓN COMPLETADA               ║
╚══════════════════════════════════════════════════════════╝
{C.END}
{C.BOLD}PARA INICIAR EL SISTEMA:{C.END}

  Opción A — Sin Docker (desarrollo local):
  {C.TEAL}cd backend && uvicorn main:app --reload --port 8000{C.END}
  Luego abre: {C.TEAL}app/index.html{C.END} en el navegador

  Opción B — Con Docker (producción):
  {C.TEAL}docker-compose up -d{C.END}
  Luego abre: {C.TEAL}http://localhost{C.END}

{C.BOLD}CREDENCIALES DE ACCESO:{C.END}
  Email:     {C.TEAL}{admin_email}{C.END}
  Contraseña: (la que ingresaste)

{C.BOLD}MÓDULOS DISPONIBLES:{C.END}
  • Sistema principal:   app/index.html
  • Dashboard financiero: app/dashboard_financiero.html
  • Aseguradoras:        app/aseguradoras.html
  • Agenda:              app/agenda.html
  • Documentos clínicos: app/documentos.html
  • API Backend:         http://localhost:8000/docs

{C.YELLOW}IMPORTANTE: Guarda el archivo .env en lugar seguro.
Nunca lo compartas ni lo subas a Git.{C.END}
""")
