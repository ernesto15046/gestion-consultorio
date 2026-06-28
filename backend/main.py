"""
═══════════════════════════════════════════════════════════════════════════
SISTEMA DE GESTIÓN — CONSULTORIO MÉDICO QUIRÚRGICO PEDIÁTRICO
Backend FastAPI + PostgreSQL
Versión: 1.0 — Mayo 2026
═══════════════════════════════════════════════════════════════════════════

Instalación:
    pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose
                passlib python-multipart aiofiles jinja2 weasyprint reportlab

Uso:
    uvicorn main:app --reload --port 8000

API Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os, uvicorn, json

# ─── Configuración ────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/consultorio_pediatrico")
SECRET_KEY   = os.getenv("SECRET_KEY", "CAMBIAR_ESTA_CLAVE_EN_PRODUCCION_2026")
ALGORITHM    = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas

engine  = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(
    title="MediConsult Pediátrico API",
    description="Sistema de Gestión para Consultorio Médico Quirúrgico Pediátrico",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ─── DB Dependency ────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── Auth ─────────────────────────────────────────────────────
def verify_password(plain, hashed): return pwd_ctx.verify(plain, hashed)
def hash_password(password): return pwd_ctx.hash(password)

def create_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id: raise HTTPException(status_code=401, detail="Token inválido")
        result = db.execute(text("SELECT * FROM usuarios WHERE id_usuario = :id"), {"id": int(user_id)}).fetchone()
        if not result: raise HTTPException(status_code=401, detail="Usuario no encontrado")
        return dict(result._mapping)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado o inválido")

# ═══════════════════════════════════════════════════════════════
# SCHEMAS PYDANTIC
# ═══════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: str
    password: str

class PacienteCreate(BaseModel):
    nombre_completo: str
    fecha_nacimiento: date
    sexo: str
    tutor_nombre: str
    tutor_relacion: Optional[str] = None
    telefono_tutor: Optional[str] = None
    telefono_alterno: Optional[str] = None
    correo_tutor: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    id_aseguradora: Optional[int] = None
    numero_poliza: Optional[str] = None
    contacto_emergencia_nombre: Optional[str] = None
    contacto_emergencia_telefono: Optional[str] = None
    referido_por: Optional[str] = None
    notas_internas: Optional[str] = None

class PacienteUpdate(PacienteCreate):
    pass

class HistorialClinicoUpdate(BaseModel):
    antecedentes_personales: Optional[str] = None
    antecedentes_quirurgicos: Optional[str] = None
    antecedentes_familiares: Optional[str] = None
    antecedentes_perinatales: Optional[str] = None
    alergias: Optional[list] = []
    medicamentos_cronicos: Optional[list] = []
    enfermedades_cronicas: Optional[list] = []
    vacunas: Optional[dict] = {}
    grupo_sanguineo: Optional[str] = None
    factor_rh: Optional[str] = None
    desarrollo_psicomotor: Optional[str] = None

class ConsultaCreate(BaseModel):
    id_paciente: int
    fecha_consulta: Optional[datetime] = None
    tipo_consulta: Optional[str] = "consulta"
    temperatura_c: Optional[float] = None
    frecuencia_cardiaca: Optional[int] = None
    frecuencia_respiratoria: Optional[int] = None
    saturacion_o2: Optional[float] = None
    tension_sistolica: Optional[int] = None
    tension_diastolica: Optional[int] = None
    peso_kg: Optional[float] = None
    talla_cm: Optional[float] = None
    motivo_consulta: str
    historia_actual: Optional[str] = None
    revision_sistemas: Optional[str] = None
    examen_fisico: Optional[str] = None
    diagnostico_principal_cie10: Optional[str] = None
    diagnostico_principal_texto: Optional[str] = None
    diagnosticos_secundarios: Optional[list] = []
    plan_terapeutico: Optional[str] = None
    indicaciones: Optional[str] = None
    examenes_solicitados: Optional[str] = None
    proxima_cita: Optional[date] = None
    notas_privadas: Optional[str] = None

class RecetaCreate(BaseModel):
    id_paciente: int
    id_consulta: Optional[int] = None
    fecha_emision: Optional[date] = None
    peso_usado_kg: Optional[float] = None
    medicamentos: list
    instrucciones_generales: Optional[str] = None

class CirugiaCreate(BaseModel):
    id_paciente: int
    id_plantilla: Optional[int] = None
    fecha_cirugia: date
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    procedimiento: str
    codigo_cpt: Optional[str] = None
    diagnostico_quirurgico: Optional[str] = None
    tipo_cirugia: Optional[str] = "electiva"
    anestesiologo: Optional[str] = None
    tipo_anestesia: Optional[str] = "general"
    ayudante_1: Optional[str] = None
    ayudante_2: Optional[str] = None
    hospital: Optional[str] = None
    sala_quirurgica: Optional[str] = None
    descripcion_quirurgica: Optional[str] = None
    hallazgos_intraop: Optional[str] = None
    materiales_utilizados: Optional[list] = []
    complicaciones: Optional[str] = None
    estado: Optional[str] = "programada"

class CitaCreate(BaseModel):
    id_paciente: int
    fecha_hora_inicio: datetime
    fecha_hora_fin: Optional[datetime] = None
    duracion_min: Optional[int] = 30
    tipo_cita: Optional[str] = "consulta"
    id_cirugia: Optional[int] = None
    motivo_consulta_previo: Optional[str] = None
    notas: Optional[str] = None

class PagoCreate(BaseModel):
    id_paciente: int
    id_consulta: Optional[int] = None
    id_cirugia: Optional[int] = None
    concepto: str
    tipo_servicio: Optional[str] = "consulta"
    monto_total: float
    descuento: Optional[float] = 0
    metodo_pago: Optional[str] = "efectivo"
    estado: Optional[str] = "pagado"
    id_aseguradora: Optional[int] = None
    numero_autorizacion_seguro: Optional[str] = None
    monto_cubierto_seguro: Optional[float] = 0
    fecha_pago: Optional[date] = None
    notas: Optional[str] = None

class SolicitudCreate(BaseModel):
    id_paciente: int
    id_aseguradora: int
    id_cirugia: Optional[int] = None
    id_consulta: Optional[int] = None
    tipo_solicitud: Optional[str] = "quirurgica"
    fecha_solicitud: Optional[date] = None
    diagnostico_texto: Optional[str] = None
    diagnostico_cie10: Optional[str] = None
    procedimiento_texto: Optional[str] = None
    justificacion_medica: str

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════

@app.post("/api/auth/login", tags=["Autenticación"])
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Iniciar sesión y obtener token JWT"""
    user = db.execute(text("SELECT * FROM usuarios WHERE email = :email AND activo = TRUE"),
                      {"email": req.email}).fetchone()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    token = create_token({"sub": str(user.id_usuario), "rol": user.rol, "nombre": user.nombre_completo})
    db.execute(text("UPDATE usuarios SET ultimo_acceso = NOW() WHERE id_usuario = :id"), {"id": user.id_usuario})
    db.commit()
    return {"access_token": token, "token_type": "bearer", "rol": user.rol, "nombre": user.nombre_completo}

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — PACIENTES
# ═══════════════════════════════════════════════════════════════

@app.get("/api/pacientes", tags=["Pacientes"])
def listar_pacientes(q: Optional[str] = None, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """Listar pacientes con búsqueda opcional"""
    if q:
        sql = text("""SELECT * FROM v_pacientes WHERE nombre_completo ILIKE :q
                      OR numero_expediente ILIKE :q OR telefono_tutor LIKE :q
                      ORDER BY created_at DESC LIMIT :limit OFFSET :offset""")
        rows = db.execute(sql, {"q": f"%{q}%", "limit": limit, "offset": offset}).fetchall()
    else:
        sql = text("SELECT * FROM v_pacientes WHERE activo = TRUE ORDER BY created_at DESC LIMIT :limit OFFSET :offset")
        rows = db.execute(sql, {"limit": limit, "offset": offset}).fetchall()
    return [dict(r._mapping) for r in rows]

@app.post("/api/pacientes", tags=["Pacientes"], status_code=201)
def crear_paciente(data: PacienteCreate, db: Session = Depends(get_db)):
    """Registrar nuevo paciente"""
    row = db.execute(text("""
        INSERT INTO pacientes (nombre_completo, fecha_nacimiento, sexo, tutor_nombre, tutor_relacion,
            telefono_tutor, telefono_alterno, correo_tutor, direccion, ciudad,
            id_aseguradora, numero_poliza,
            contacto_emergencia_nombre, contacto_emergencia_telefono,
            referido_por, notas_internas)
        VALUES (:nombre_completo, :fecha_nacimiento, :sexo, :tutor_nombre, :tutor_relacion,
            :telefono_tutor, :telefono_alterno, :correo_tutor, :direccion, :ciudad,
            :id_aseguradora, :numero_poliza,
            :contacto_emergencia_nombre, :contacto_emergencia_telefono,
            :referido_por, :notas_internas)
        RETURNING *"""), data.dict()).fetchone()
    db.commit()
    # Crear historial clínico vacío
    db.execute(text("INSERT INTO historial_clinico (id_paciente) VALUES (:id)"), {"id": row.id_paciente})
    db.commit()
    return dict(row._mapping)

@app.get("/api/pacientes/{id}", tags=["Pacientes"])
def obtener_paciente(id: int, db: Session = Depends(get_db)):
    """Obtener expediente completo de un paciente"""
    pac = db.execute(text("SELECT * FROM v_pacientes WHERE id_paciente = :id"), {"id": id}).fetchone()
    if not pac: raise HTTPException(404, "Paciente no encontrado")
    hist = db.execute(text("SELECT * FROM historial_clinico WHERE id_paciente = :id"), {"id": id}).fetchone()
    consultas = db.execute(text("SELECT * FROM consultas WHERE id_paciente = :id ORDER BY fecha_consulta DESC LIMIT 10"), {"id": id}).fetchall()
    cirugias  = db.execute(text("SELECT * FROM cirugias  WHERE id_paciente = :id ORDER BY fecha_cirugia  DESC"), {"id": id}).fetchall()
    recetas   = db.execute(text("SELECT * FROM recetas   WHERE id_paciente = :id ORDER BY fecha_emision  DESC LIMIT 5"), {"id": id}).fetchall()
    return {
        "paciente": dict(pac._mapping),
        "historial": dict(hist._mapping) if hist else {},
        "consultas": [dict(r._mapping) for r in consultas],
        "cirugias":  [dict(r._mapping) for r in cirugias],
        "recetas":   [dict(r._mapping) for r in recetas],
    }

@app.put("/api/pacientes/{id}", tags=["Pacientes"])
def actualizar_paciente(id: int, data: PacienteUpdate, db: Session = Depends(get_db)):
    """Actualizar datos de un paciente"""
    d = data.dict()
    d["id"] = id
    db.execute(text("""UPDATE pacientes SET nombre_completo=:nombre_completo, fecha_nacimiento=:fecha_nacimiento,
        sexo=:sexo, tutor_nombre=:tutor_nombre, tutor_relacion=:tutor_relacion,
        telefono_tutor=:telefono_tutor, correo_tutor=:correo_tutor, direccion=:direccion, ciudad=:ciudad,
        id_aseguradora=:id_aseguradora, numero_poliza=:numero_poliza,
        referido_por=:referido_por, notas_internas=:notas_internas
        WHERE id_paciente = :id"""), d)
    db.commit()
    return {"ok": True}

@app.put("/api/pacientes/{id}/historial", tags=["Pacientes"])
def actualizar_historial(id: int, data: HistorialClinicoUpdate, db: Session = Depends(get_db)):
    """Actualizar historial clínico de un paciente"""
    d = data.dict()
    d["id"] = id
    d["alergias"] = json.dumps(d.get("alergias", []))
    d["medicamentos_cronicos"] = json.dumps(d.get("medicamentos_cronicos", []))
    d["enfermedades_cronicas"] = json.dumps(d.get("enfermedades_cronicas", []))
    d["vacunas"] = json.dumps(d.get("vacunas", {}))
    db.execute(text("""UPDATE historial_clinico SET
        antecedentes_personales=:antecedentes_personales,
        antecedentes_quirurgicos=:antecedentes_quirurgicos,
        antecedentes_familiares=:antecedentes_familiares,
        alergias=:alergias::jsonb, medicamentos_cronicos=:medicamentos_cronicos::jsonb,
        enfermedades_cronicas=:enfermedades_cronicas::jsonb, vacunas=:vacunas::jsonb,
        grupo_sanguineo=:grupo_sanguineo, factor_rh=:factor_rh,
        ultima_actualizacion=NOW() WHERE id_paciente = :id"""), d)
    db.commit()
    return {"ok": True}

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — CONSULTAS
# ═══════════════════════════════════════════════════════════════

@app.post("/api/consultas", tags=["Consultas"], status_code=201)
def crear_consulta(data: ConsultaCreate, db: Session = Depends(get_db)):
    """Registrar nueva consulta médica"""
    d = data.dict()
    d["diagnosticos_secundarios"] = json.dumps(d.get("diagnosticos_secundarios", []))
    if not d.get("fecha_consulta"): d["fecha_consulta"] = datetime.utcnow()
    row = db.execute(text("""
        INSERT INTO consultas (id_paciente, id_medico, fecha_consulta, tipo_consulta,
            temperatura_c, frecuencia_cardiaca, frecuencia_respiratoria, saturacion_o2,
            tension_sistolica, tension_diastolica, peso_kg, talla_cm,
            motivo_consulta, historia_actual, revision_sistemas, examen_fisico,
            diagnostico_principal_cie10, diagnostico_principal_texto, diagnosticos_secundarios,
            plan_terapeutico, indicaciones, examenes_solicitados, proxima_cita, notas_privadas)
        VALUES (:id_paciente, 1, :fecha_consulta, :tipo_consulta,
            :temperatura_c, :frecuencia_cardiaca, :frecuencia_respiratoria, :saturacion_o2,
            :tension_sistolica, :tension_diastolica, :peso_kg, :talla_cm,
            :motivo_consulta, :historia_actual, :revision_sistemas, :examen_fisico,
            :diagnostico_principal_cie10, :diagnostico_principal_texto, :diagnosticos_secundarios::jsonb,
            :plan_terapeutico, :indicaciones, :examenes_solicitados, :proxima_cita, :notas_privadas)
        RETURNING *"""), d).fetchone()
    # Actualizar peso en medidas antropométricas si se indicó
    if data.peso_kg:
        db.execute(text("""INSERT INTO medidas_antropometricas (id_paciente, peso_kg, talla_cm, fecha_medida)
                           VALUES (:pac, :peso, :talla, CURRENT_DATE)"""),
                   {"pac": data.id_paciente, "peso": data.peso_kg, "talla": data.talla_cm})
    db.commit()
    return dict(row._mapping)

@app.get("/api/consultas/paciente/{id_paciente}", tags=["Consultas"])
def consultas_paciente(id_paciente: int, db: Session = Depends(get_db)):
    """Listar consultas de un paciente"""
    rows = db.execute(text("SELECT * FROM consultas WHERE id_paciente = :id ORDER BY fecha_consulta DESC"),
                      {"id": id_paciente}).fetchall()
    return [dict(r._mapping) for r in rows]

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — RECETAS
# ═══════════════════════════════════════════════════════════════

@app.post("/api/recetas", tags=["Recetas"], status_code=201)
def crear_receta(data: RecetaCreate, db: Session = Depends(get_db)):
    """Crear nueva receta médica"""
    d = data.dict()
    d["medicamentos"] = json.dumps(d.get("medicamentos", []))
    if not d.get("fecha_emision"): d["fecha_emision"] = date.today()
    row = db.execute(text("""
        INSERT INTO recetas (id_paciente, id_medico, id_consulta, fecha_emision,
            peso_usado_kg, medicamentos, instrucciones_generales)
        VALUES (:id_paciente, 1, :id_consulta, :fecha_emision,
            :peso_usado_kg, :medicamentos::jsonb, :instrucciones_generales)
        RETURNING *"""), d).fetchone()
    db.commit()
    return dict(row._mapping)

@app.get("/api/recetas/{id}", tags=["Recetas"])
def obtener_receta(id: int, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT * FROM recetas WHERE id_receta = :id"), {"id": id}).fetchone()
    if not row: raise HTTPException(404, "Receta no encontrada")
    return dict(row._mapping)

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — CIRUGIAS
# ═══════════════════════════════════════════════════════════════

@app.post("/api/cirugias", tags=["Cirugías"], status_code=201)
def crear_cirugia(data: CirugiaCreate, db: Session = Depends(get_db)):
    """Registrar nueva cirugía"""
    d = data.dict()
    d["materiales_utilizados"] = json.dumps(d.get("materiales_utilizados", []))
    row = db.execute(text("""
        INSERT INTO cirugias (id_paciente, id_medico, id_plantilla, fecha_cirugia,
            procedimiento, codigo_cpt, diagnostico_quirurgico, tipo_cirugia,
            anestesiologo, tipo_anestesia, ayudante_1, ayudante_2,
            hospital, sala_quirurgica, descripcion_quirurgica, hallazgos_intraop,
            materiales_utilizados, complicaciones, estado)
        VALUES (:id_paciente, 1, :id_plantilla, :fecha_cirugia,
            :procedimiento, :codigo_cpt, :diagnostico_quirurgico, :tipo_cirugia,
            :anestesiologo, :tipo_anestesia, :ayudante_1, :ayudante_2,
            :hospital, :sala_quirurgica, :descripcion_quirurgica, :hallazgos_intraop,
            :materiales_utilizados::jsonb, :complicaciones, :estado)
        RETURNING *"""), d).fetchone()
    db.commit()
    return dict(row._mapping)

@app.put("/api/cirugias/{id}/estado", tags=["Cirugías"])
def cambiar_estado_cirugia(id: int, estado: str, db: Session = Depends(get_db)):
    db.execute(text("UPDATE cirugias SET estado = :estado WHERE id_cirugia = :id"), {"estado": estado, "id": id})
    db.commit()
    return {"ok": True}

@app.get("/api/cirugias/plantillas", tags=["Cirugías"])
def listar_plantillas(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM plantillas_quirurgicas WHERE activa = TRUE ORDER BY nombre_procedimiento")).fetchall()
    return [dict(r._mapping) for r in rows]

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — CITAS
# ═══════════════════════════════════════════════════════════════

@app.get("/api/citas/hoy", tags=["Agenda"])
def citas_hoy(db: Session = Depends(get_db)):
    """Agenda del día con datos del paciente"""
    rows = db.execute(text("SELECT * FROM v_agenda_hoy")).fetchall()
    return [dict(r._mapping) for r in rows]

@app.get("/api/citas", tags=["Agenda"])
def listar_citas(desde: Optional[date] = None, hasta: Optional[date] = None, db: Session = Depends(get_db)):
    d = desde or date.today()
    h = hasta or d + timedelta(days=7)
    rows = db.execute(text("""
        SELECT c.*, p.nombre_completo, p.telefono_tutor
        FROM citas c JOIN pacientes p ON c.id_paciente = p.id_paciente
        WHERE c.fecha_hora_inicio::DATE BETWEEN :desde AND :hasta
        ORDER BY c.fecha_hora_inicio"""), {"desde": d, "hasta": h}).fetchall()
    return [dict(r._mapping) for r in rows]

@app.post("/api/citas", tags=["Agenda"], status_code=201)
def crear_cita(data: CitaCreate, db: Session = Depends(get_db)):
    d = data.dict()
    row = db.execute(text("""
        INSERT INTO citas (id_paciente, id_medico, fecha_hora_inicio, fecha_hora_fin,
            duracion_min, tipo_cita, id_cirugia, motivo_consulta_previo, notas)
        VALUES (:id_paciente, 1, :fecha_hora_inicio, :fecha_hora_fin,
            :duracion_min, :tipo_cita, :id_cirugia, :motivo_consulta_previo, :notas)
        RETURNING *"""), d).fetchone()
    db.commit()
    return dict(row._mapping)

@app.put("/api/citas/{id}/estado", tags=["Agenda"])
def cambiar_estado_cita(id: int, estado: str, db: Session = Depends(get_db)):
    db.execute(text("UPDATE citas SET estado = :estado WHERE id_cita = :id"), {"estado": estado, "id": id})
    db.commit()
    return {"ok": True}

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — PAGOS Y FINANZAS
# ═══════════════════════════════════════════════════════════════

@app.post("/api/pagos", tags=["Finanzas"], status_code=201)
def registrar_pago(data: PagoCreate, db: Session = Depends(get_db)):
    d = data.dict()
    if not d.get("fecha_pago"): d["fecha_pago"] = date.today()
    row = db.execute(text("""
        INSERT INTO pagos (id_paciente, id_consulta, id_cirugia, concepto, tipo_servicio,
            monto_total, descuento, metodo_pago, estado,
            id_aseguradora, numero_autorizacion_seguro, monto_cubierto_seguro,
            fecha_pago, notas, registrado_por)
        VALUES (:id_paciente, :id_consulta, :id_cirugia, :concepto, :tipo_servicio,
            :monto_total, :descuento, :metodo_pago, :estado,
            :id_aseguradora, :numero_autorizacion_seguro, :monto_cubierto_seguro,
            :fecha_pago, :notas, 1)
        RETURNING *"""), d).fetchone()
    db.commit()
    return dict(row._mapping)

@app.get("/api/finanzas/resumen", tags=["Finanzas"])
def resumen_financiero(db: Session = Depends(get_db)):
    """Dashboard financiero completo"""
    hoy = db.execute(text("""SELECT COALESCE(SUM(monto_neto), 0) FROM pagos
                              WHERE fecha_pago = CURRENT_DATE AND estado IN ('pagado','parcial')""")).scalar()
    mes = db.execute(text("""SELECT COALESCE(SUM(monto_neto), 0) FROM pagos
                              WHERE DATE_TRUNC('month', fecha_pago) = DATE_TRUNC('month', CURRENT_DATE)
                              AND estado IN ('pagado','parcial')""")).scalar()
    pendiente = db.execute(text("""SELECT COALESCE(SUM(monto_neto), 0) FROM pagos WHERE estado = 'pendiente'""")).scalar()
    por_mes   = db.execute(text("SELECT * FROM v_resumen_financiero_mensual LIMIT 6")).fetchall()
    return {
        "ingresos_hoy": float(hoy),
        "ingresos_mes": float(mes),
        "pendiente_cobro": float(pendiente),
        "por_mes": [dict(r._mapping) for r in por_mes]
    }

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — SOLICITUDES ASEGURADORAS
# ═══════════════════════════════════════════════════════════════

@app.post("/api/solicitudes", tags=["Aseguradoras"], status_code=201)
def crear_solicitud(data: SolicitudCreate, db: Session = Depends(get_db)):
    d = data.dict()
    if not d.get("fecha_solicitud"): d["fecha_solicitud"] = date.today()
    row = db.execute(text("""
        INSERT INTO solicitudes_aseguradoras
            (id_paciente, id_aseguradora, id_medico, id_cirugia, id_consulta,
             tipo_solicitud, fecha_solicitud, diagnostico_texto, diagnostico_cie10,
             procedimiento_texto, justificacion_medica)
        VALUES
            (:id_paciente, :id_aseguradora, 1, :id_cirugia, :id_consulta,
             :tipo_solicitud, :fecha_solicitud, :diagnostico_texto, :diagnostico_cie10,
             :procedimiento_texto, :justificacion_medica)
        RETURNING *"""), d).fetchone()
    db.commit()
    return dict(row._mapping)

@app.get("/api/solicitudes", tags=["Aseguradoras"])
def listar_solicitudes(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT s.*, p.nombre_completo, a.nombre AS aseguradora_nombre
        FROM solicitudes_aseguradoras s
        JOIN pacientes p ON s.id_paciente = p.id_paciente
        JOIN aseguradoras a ON s.id_aseguradora = a.id_aseguradora
        ORDER BY s.created_at DESC""")).fetchall()
    return [dict(r._mapping) for r in rows]

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — CATÁLOGOS
# ═══════════════════════════════════════════════════════════════

@app.get("/api/catalogos/medicamentos", tags=["Catálogos"])
def medicamentos(q: Optional[str] = None, db: Session = Depends(get_db)):
    if q:
        rows = db.execute(text("SELECT * FROM medicamentos_catalogo WHERE nombre_generico ILIKE :q AND activo = TRUE LIMIT 20"),
                          {"q": f"%{q}%"}).fetchall()
    else:
        rows = db.execute(text("SELECT * FROM medicamentos_catalogo WHERE activo = TRUE ORDER BY nombre_generico")).fetchall()
    return [dict(r._mapping) for r in rows]

@app.get("/api/catalogos/cie10", tags=["Catálogos"])
def diagnosticos_cie10(q: Optional[str] = None, db: Session = Depends(get_db)):
    if q:
        rows = db.execute(text("SELECT * FROM diagnosticos_cie10 WHERE descripcion ILIKE :q OR codigo ILIKE :q LIMIT 20"),
                          {"q": f"%{q}%"}).fetchall()
    else:
        rows = db.execute(text("SELECT * FROM diagnosticos_cie10 WHERE frecuente_pediatria = TRUE")).fetchall()
    return [dict(r._mapping) for r in rows]

@app.get("/api/catalogos/aseguradoras", tags=["Catálogos"])
def aseguradoras(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM aseguradoras WHERE activa = TRUE ORDER BY nombre")).fetchall()
    return [dict(r._mapping) for r in rows]

# ═══════════════════════════════════════════════════════════════
# ENDPOINTS — ESTADÍSTICAS Y REPORTES
# ═══════════════════════════════════════════════════════════════

@app.get("/api/estadisticas/dashboard", tags=["Estadísticas"])
def dashboard_stats(db: Session = Depends(get_db)):
    """Estadísticas para el dashboard principal"""
    pac_stats  = db.execute(text("SELECT * FROM v_estadisticas_pacientes")).fetchone()
    citas_hoy  = db.execute(text("SELECT COUNT(*) FROM citas WHERE fecha_hora_inicio::DATE = CURRENT_DATE")).scalar()
    qx_mes     = db.execute(text("SELECT COUNT(*) FROM cirugias WHERE estado='realizada' AND DATE_TRUNC('month',fecha_cirugia)=DATE_TRUNC('month',CURRENT_DATE)")).scalar()
    pendientes = db.execute(text("SELECT COUNT(*) FROM v_seguimiento_pendiente")).scalar()
    return {
        "pacientes": dict(pac_stats._mapping) if pac_stats else {},
        "citas_hoy": int(citas_hoy),
        "cirugias_mes": int(qx_mes),
        "seguimientos_pendientes": int(pendientes),
    }

@app.get("/api/estadisticas/diagnosticos", tags=["Estadísticas"])
def top_diagnosticos(db: Session = Depends(get_db)):
    """Diagnósticos más frecuentes"""
    rows = db.execute(text("""
        SELECT diagnostico_principal_texto, COUNT(*) as casos
        FROM consultas WHERE diagnostico_principal_texto IS NOT NULL
        GROUP BY diagnostico_principal_texto ORDER BY casos DESC LIMIT 10""")).fetchall()
    return [dict(r._mapping) for r in rows]

# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@app.get("/api/health", tags=["Sistema"])
def health():
    return {"status": "ok", "version": "1.0.0", "sistema": "MediConsult Pediátrico"}

@app.get("/", tags=["Sistema"])
def root():
    return {"mensaje": "API MediConsult Pediátrico v1.0 — Documentación en /docs"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
