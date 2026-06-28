-- ============================================================
-- SISTEMA DE GESTIÓN — CONSULTORIO MÉDICO QUIRÚRGICO PEDIÁTRICO
-- Base de datos PostgreSQL 16
-- Versión: 1.0 — Mayo 2026
-- ============================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";   -- para búsqueda rápida de texto

-- ============================================================
-- SECUENCIAS Y ENUMERADOS
-- ============================================================

CREATE TYPE sexo_enum          AS ENUM ('M', 'F');
CREATE TYPE estado_cita_enum   AS ENUM ('pendiente', 'confirmada', 'cancelada', 'completada', 'no_asistio');
CREATE TYPE tipo_cita_enum     AS ENUM ('consulta', 'seguimiento', 'cirugia', 'urgencia', 'postoperatorio');
CREATE TYPE estado_cirugia_enum AS ENUM ('programada', 'realizada', 'cancelada', 'postoperatorio');
CREATE TYPE metodo_pago_enum   AS ENUM ('efectivo', 'tarjeta_credito', 'tarjeta_debito', 'transferencia', 'seguro', 'mixto');
CREATE TYPE estado_pago_enum   AS ENUM ('pagado', 'pendiente', 'parcial', 'anulado');
CREATE TYPE rol_enum           AS ENUM ('medico', 'asistente', 'recepcionista', 'contador');
CREATE TYPE tipo_doc_enum      AS ENUM ('receta', 'consentimiento', 'descripcion_quirurgica',
                                        'nota_preoperatoria', 'nota_postoperatoria', 'epicrisis',
                                        'indicaciones_postop', 'solicitud_aseguradora',
                                        'certificado_medico', 'carta_referencia', 'otro');

-- ============================================================
-- TABLA 1: USUARIOS DEL SISTEMA
-- ============================================================
CREATE TABLE usuarios (
    id_usuario          SERIAL PRIMARY KEY,
    nombre_completo     VARCHAR(200)    NOT NULL,
    email               VARCHAR(150)    NOT NULL UNIQUE,
    password_hash       VARCHAR(255)    NOT NULL,
    rol                 rol_enum        NOT NULL DEFAULT 'recepcionista',
    cedula_medica       VARCHAR(50),                    -- Solo para rol médico
    especialidad        VARCHAR(100),
    firma_url           VARCHAR(500),                   -- Imagen de la firma digital
    telefono            VARCHAR(20),
    activo              BOOLEAN         NOT NULL DEFAULT TRUE,
    ultimo_acceso       TIMESTAMP,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA 2: ASEGURADORAS
-- ============================================================
CREATE TABLE aseguradoras (
    id_aseguradora      SERIAL PRIMARY KEY,
    nombre              VARCHAR(150)    NOT NULL,
    codigo              VARCHAR(20),
    email_autorizaciones VARCHAR(150),
    telefono            VARCHAR(30),
    contacto_nombre     VARCHAR(150),
    activa              BOOLEAN         NOT NULL DEFAULT TRUE,
    notas               TEXT,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA 3: PACIENTES
-- ============================================================
CREATE TABLE pacientes (
    id_paciente         SERIAL PRIMARY KEY,
    numero_expediente   VARCHAR(20)     NOT NULL UNIQUE,   -- Generado automáticamente: PED-00001
    nombre_completo     VARCHAR(200)    NOT NULL,
    fecha_nacimiento    DATE            NOT NULL,
    sexo                sexo_enum       NOT NULL,
    -- Dirección
    direccion           TEXT,
    ciudad              VARCHAR(100),
    pais                VARCHAR(100)    DEFAULT 'Venezuela',
    -- Contacto
    telefono_tutor      VARCHAR(20),
    telefono_alterno    VARCHAR(20),
    correo_tutor        VARCHAR(150),
    -- Tutor
    tutor_nombre        VARCHAR(200)    NOT NULL,
    tutor_relacion      VARCHAR(50),                       -- padre, madre, abuela, etc.
    tutor_cedula        VARCHAR(20),
    -- Seguro médico
    id_aseguradora      INTEGER         REFERENCES aseguradoras(id_aseguradora),
    numero_poliza       VARCHAR(80),
    vencimiento_poliza  DATE,
    -- Emergencia
    contacto_emergencia_nombre   VARCHAR(200),
    contacto_emergencia_telefono VARCHAR(20),
    -- Referencias
    referido_por        VARCHAR(200),                      -- Médico o paciente que refirió
    medico_referente    VARCHAR(200),
    -- Foto
    foto_url            VARCHAR(500),
    -- Control
    medico_id           INTEGER         REFERENCES usuarios(id_usuario),
    activo              BOOLEAN         NOT NULL DEFAULT TRUE,
    notas_internas      TEXT,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- Índice para búsqueda por nombre (trigram para búsqueda parcial)
CREATE INDEX idx_pacientes_nombre ON pacientes USING GIN (nombre_completo gin_trgm_ops);
CREATE INDEX idx_pacientes_expediente ON pacientes (numero_expediente);
CREATE INDEX idx_pacientes_telefono ON pacientes (telefono_tutor);

-- Vista: edad calculada automáticamente
CREATE OR REPLACE VIEW v_pacientes AS
SELECT
    p.*,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.fecha_nacimiento))::INTEGER AS edad_anios,
    CASE
        WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.fecha_nacimiento)) < 2
        THEN EXTRACT(MONTH FROM AGE(CURRENT_DATE, p.fecha_nacimiento))::INTEGER
        ELSE NULL
    END AS edad_meses,
    a.nombre AS aseguradora_nombre
FROM pacientes p
LEFT JOIN aseguradoras a ON p.id_aseguradora = a.id_aseguradora;

-- ============================================================
-- TABLA 4: HISTORIAL CLÍNICO (1:1 con pacientes)
-- ============================================================
CREATE TABLE historial_clinico (
    id_historial            SERIAL PRIMARY KEY,
    id_paciente             INTEGER         NOT NULL UNIQUE REFERENCES pacientes(id_paciente) ON DELETE CASCADE,
    -- Antecedentes
    antecedentes_personales TEXT,
    antecedentes_quirurgicos TEXT,
    antecedentes_familiares TEXT,
    antecedentes_perinatales TEXT,           -- Embarazo, parto, APGAR
    -- Alergias (JSON para flexibilidad)
    alergias                JSONB           DEFAULT '[]'::JSONB,
    -- Ejemplo: [{"tipo": "medicamento", "nombre": "penicilina", "reaccion": "anafilaxia"}]
    -- Medicamentos crónicos
    medicamentos_cronicos   JSONB           DEFAULT '[]'::JSONB,
    -- Ejemplo: [{"nombre": "omeprazol", "dosis": "20mg", "frecuencia": "diario"}]
    -- Enfermedades crónicas
    enfermedades_cronicas   JSONB           DEFAULT '[]'::JSONB,
    -- Vacunas
    vacunas                 JSONB           DEFAULT '{}'::JSONB,
    -- Esquema: {"BCG": true, "Hepatitis_B": true, "DPT": "completo", ...}
    -- Grupo sanguíneo
    grupo_sanguineo         VARCHAR(5),
    factor_rh               VARCHAR(3),
    -- Desarrollo
    desarrollo_psicomotor   TEXT,
    alimentacion            TEXT,
    -- Actualización
    ultima_actualizacion    TIMESTAMP       NOT NULL DEFAULT NOW(),
    actualizado_por         INTEGER         REFERENCES usuarios(id_usuario)
);

-- ============================================================
-- TABLA 5: MEDIDAS ANTROPOMÉTRICAS (historial de peso/talla)
-- ============================================================
CREATE TABLE medidas_antropometricas (
    id_medida           SERIAL PRIMARY KEY,
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente) ON DELETE CASCADE,
    fecha_medida        DATE            NOT NULL DEFAULT CURRENT_DATE,
    peso_kg             DECIMAL(5,2),
    talla_cm            DECIMAL(5,2),
    perimetro_cefalico  DECIMAL(5,1),
    imc                 DECIMAL(5,2) GENERATED ALWAYS AS
                        (CASE WHEN talla_cm > 0 THEN ROUND((peso_kg / ((talla_cm/100)^2))::NUMERIC, 2) ELSE NULL END) STORED,
    percentil_peso      DECIMAL(5,1),
    percentil_talla     DECIMAL(5,1),
    percentil_imc       DECIMAL(5,1),
    registrado_por      INTEGER         REFERENCES usuarios(id_usuario),
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_medidas_paciente ON medidas_antropometricas (id_paciente, fecha_medida DESC);

-- ============================================================
-- TABLA 6: CATÁLOGO DE DIAGNÓSTICOS CIE-10 (referencia)
-- ============================================================
CREATE TABLE diagnosticos_cie10 (
    codigo              VARCHAR(10)     PRIMARY KEY,
    descripcion         TEXT            NOT NULL,
    categoria           VARCHAR(100),
    frecuente_pediatria BOOLEAN         DEFAULT FALSE    -- Para mostrar primero en autocompletado
);

-- ============================================================
-- TABLA 7: CONSULTAS MÉDICAS
-- ============================================================
CREATE TABLE consultas (
    id_consulta         SERIAL PRIMARY KEY,
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente),
    id_medico           INTEGER         NOT NULL REFERENCES usuarios(id_usuario),
    -- Datos de la visita
    fecha_consulta      TIMESTAMP       NOT NULL DEFAULT NOW(),
    tipo_consulta       VARCHAR(50)     DEFAULT 'consulta',    -- consulta, urgencia, seguimiento, telemedicina
    -- Signos vitales
    temperatura_c       DECIMAL(4,1),
    frecuencia_cardiaca INTEGER,
    frecuencia_respiratoria INTEGER,
    saturacion_o2       DECIMAL(4,1),
    tension_sistolica   INTEGER,
    tension_diastolica  INTEGER,
    peso_kg             DECIMAL(5,2),
    talla_cm            DECIMAL(5,2),
    -- Contenido clínico
    motivo_consulta     TEXT            NOT NULL,
    historia_actual     TEXT,
    revision_sistemas   TEXT,
    examen_fisico       TEXT,
    -- Diagnóstico
    diagnostico_principal_cie10  VARCHAR(10)  REFERENCES diagnosticos_cie10(codigo),
    diagnostico_principal_texto  TEXT,
    diagnosticos_secundarios     JSONB        DEFAULT '[]'::JSONB,
    -- Plan
    plan_terapeutico    TEXT,
    indicaciones        TEXT,
    examenes_solicitados TEXT,
    -- Seguimiento
    proxima_cita        DATE,
    notas_privadas      TEXT,           -- Solo visible para el médico
    -- Control
    firma_hash          VARCHAR(255),   -- Hash de la firma digital
    pdf_generado        BOOLEAN         DEFAULT FALSE,
    pdf_url             VARCHAR(500),
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_consultas_paciente ON consultas (id_paciente, fecha_consulta DESC);
CREATE INDEX idx_consultas_fecha ON consultas (fecha_consulta DESC);

-- ============================================================
-- TABLA 8: CATÁLOGO DE MEDICAMENTOS
-- ============================================================
CREATE TABLE medicamentos_catalogo (
    id_medicamento      SERIAL PRIMARY KEY,
    nombre_generico     VARCHAR(200)    NOT NULL,
    nombre_comercial    VARCHAR(200),
    grupo_farmacologico VARCHAR(100),
    -- Dosis pediátrica
    dosis_mg_kg_dia     DECIMAL(8,3),   -- mg por kg por día
    dosis_minima_mg     DECIMAL(8,2),
    dosis_maxima_mg     DECIMAL(8,2),
    dosis_maxima_dia_mg DECIMAL(8,2),
    frecuencias_disponibles JSONB DEFAULT '["cada 8 horas","cada 12 horas","cada 24 horas"]'::JSONB,
    -- Presentaciones
    presentaciones      JSONB DEFAULT '[]'::JSONB,
    -- [{"forma": "jarabe", "concentracion": "250mg/5ml", "volumen": "100ml"}]
    vias_administracion JSONB DEFAULT '["oral"]'::JSONB,
    -- Alertas
    requiere_receta     BOOLEAN         DEFAULT TRUE,
    notas_especiales    TEXT,
    activo              BOOLEAN         DEFAULT TRUE,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_medicamentos_nombre ON medicamentos_catalogo USING GIN (nombre_generico gin_trgm_ops);

-- ============================================================
-- TABLA 9: RECETAS MÉDICAS
-- ============================================================
CREATE TABLE recetas (
    id_receta           SERIAL PRIMARY KEY,
    numero_receta       VARCHAR(20)     NOT NULL UNIQUE,   -- RX-2026-00001
    id_consulta         INTEGER         REFERENCES consultas(id_consulta),
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente),
    id_medico           INTEGER         NOT NULL REFERENCES usuarios(id_usuario),
    fecha_emision       DATE            NOT NULL DEFAULT CURRENT_DATE,
    fecha_vencimiento   DATE,                              -- Generalmente 30 días después
    peso_usado_kg       DECIMAL(5,2),                      -- Peso para cálculo de dosis
    -- Medicamentos (array JSON)
    medicamentos        JSONB           NOT NULL DEFAULT '[]'::JSONB,
    /*
    [{
      "id_medicamento": 1,
      "nombre": "Amoxicilina",
      "presentacion": "250mg/5ml jarabe",
      "dosis_calculada_mg": 250,
      "dosis_texto": "5 ml",
      "frecuencia": "cada 8 horas",
      "duracion_dias": 7,
      "cantidad_total": "1 frasco",
      "via": "oral",
      "instrucciones": "Con o sin alimentos"
    }]
    */
    instrucciones_generales TEXT,
    -- Documentos
    pdf_url             VARCHAR(500),
    pdf_generado        BOOLEAN         DEFAULT FALSE,
    -- Envíos
    enviado_whatsapp    BOOLEAN         DEFAULT FALSE,
    enviado_email       BOOLEAN         DEFAULT FALSE,
    fecha_envio         TIMESTAMP,
    -- Control
    activa              BOOLEAN         DEFAULT TRUE,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recetas_paciente ON recetas (id_paciente, fecha_emision DESC);

-- ============================================================
-- TABLA 10: PLANTILLAS QUIRÚRGICAS
-- ============================================================
CREATE TABLE plantillas_quirurgicas (
    id_plantilla        SERIAL PRIMARY KEY,
    nombre_procedimiento VARCHAR(200)   NOT NULL,
    codigo_cpt          VARCHAR(20),
    categoria           VARCHAR(100),   -- hernias, abdomen, urologia, etc.
    -- Plantilla de descripción quirúrgica
    descripcion_template TEXT,          -- Texto con variables {{paciente}}, {{fecha}}, etc.
    pasos_quirurgicos   JSONB           DEFAULT '[]'::JSONB,
    -- ["Anestesia general.", "Asepsia y antisepsia de región inguinal.", ...]
    -- Plantilla de consentimiento informado
    consentimiento_template TEXT,
    riesgos_especificos JSONB           DEFAULT '[]'::JSONB,
    -- Plantilla de indicaciones postoperatorias
    indicaciones_postop_template TEXT,
    -- Materiales típicos
    materiales_tipicos  JSONB           DEFAULT '[]'::JSONB,
    duracion_estimada_min INTEGER,
    activa              BOOLEAN         DEFAULT TRUE,
    created_by          INTEGER         REFERENCES usuarios(id_usuario),
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA 11: CIRUGÍAS
-- ============================================================
CREATE TABLE cirugias (
    id_cirugia          SERIAL PRIMARY KEY,
    numero_cirugia      VARCHAR(20)     NOT NULL UNIQUE,   -- CIR-2026-00001
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente),
    id_medico           INTEGER         NOT NULL REFERENCES usuarios(id_usuario),
    id_plantilla        INTEGER         REFERENCES plantillas_quirurgicas(id_plantilla),
    -- Datos del procedimiento
    fecha_cirugia       DATE            NOT NULL,
    hora_inicio         TIME,
    hora_fin            TIME,
    duracion_minutos    INTEGER GENERATED ALWAYS AS
                        (CASE WHEN hora_inicio IS NOT NULL AND hora_fin IS NOT NULL
                         THEN EXTRACT(EPOCH FROM (hora_fin - hora_inicio))::INTEGER / 60
                         ELSE NULL END) STORED,
    -- Procedimiento
    procedimiento       VARCHAR(300)    NOT NULL,
    codigo_cpt          VARCHAR(20),
    diagnostico_quirurgico TEXT,
    tipo_cirugia        VARCHAR(50),    -- electiva, urgencia, emergencia
    -- Equipo quirúrgico
    anestesiologo       VARCHAR(200),
    tipo_anestesia      VARCHAR(80),    -- general, regional, local, sedacion
    ayudante_1          VARCHAR(200),
    ayudante_2          VARCHAR(200),
    instrumentista      VARCHAR(200),
    circul_quirurgica   VARCHAR(200),
    -- Lugar
    hospital            VARCHAR(200),
    sala_quirurgica     VARCHAR(50),
    -- Descripción clínica
    descripcion_quirurgica TEXT,
    hallazgos_intraop   TEXT,
    materiales_utilizados JSONB         DEFAULT '[]'::JSONB,
    complicaciones      TEXT,
    sangrado_ml         INTEGER,
    diuresis_ml         INTEGER,
    transfusiones       TEXT,
    -- Estado postoperatorio inmediato
    condicion_al_salir  TEXT,
    destino_postop      VARCHAR(50),    -- sala, UCI, casa
    -- Estado del procedimiento
    estado              estado_cirugia_enum NOT NULL DEFAULT 'programada',
    -- Documentos generados
    consentimiento_url  VARCHAR(500),
    nota_preop_url      VARCHAR(500),
    descripcion_url     VARCHAR(500),
    nota_postop_url     VARCHAR(500),
    epicrisis_url       VARCHAR(500),
    indicaciones_url    VARCHAR(500),
    -- Control
    notas_internas      TEXT,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cirugias_paciente ON cirugias (id_paciente, fecha_cirugia DESC);
CREATE INDEX idx_cirugias_estado ON cirugias (estado);

-- ============================================================
-- TABLA 12: SEGUIMIENTO POSTOPERATORIO
-- ============================================================
CREATE TABLE seguimiento_postop (
    id_seguimiento      SERIAL PRIMARY KEY,
    id_cirugia          INTEGER         NOT NULL REFERENCES cirugias(id_cirugia) ON DELETE CASCADE,
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente),
    fecha_control       DATE            NOT NULL,
    dia_postoperatorio  INTEGER,        -- Calculado desde fecha_cirugia
    -- Evaluación
    estado_herida       VARCHAR(100),
    dolor_escala        SMALLINT CHECK (dolor_escala BETWEEN 0 AND 10),
    temperatura         DECIMAL(4,1),
    peso_kg             DECIMAL(5,2),
    evolucion           TEXT,
    indicaciones_nuevas TEXT,
    proxima_revision    DATE,
    alta_medica         BOOLEAN         DEFAULT FALSE,
    fecha_alta          DATE,
    registrado_por      INTEGER         REFERENCES usuarios(id_usuario),
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA 13: SOLICITUDES A ASEGURADORAS
-- ============================================================
CREATE TABLE solicitudes_aseguradoras (
    id_solicitud        SERIAL PRIMARY KEY,
    numero_solicitud    VARCHAR(30)     NOT NULL UNIQUE,   -- SOL-2026-00001
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente),
    id_aseguradora      INTEGER         NOT NULL REFERENCES aseguradoras(id_aseguradora),
    id_medico           INTEGER         NOT NULL REFERENCES usuarios(id_usuario),
    id_cirugia          INTEGER         REFERENCES cirugias(id_cirugia),
    id_consulta         INTEGER         REFERENCES consultas(id_consulta),
    -- Solicitud
    tipo_solicitud      VARCHAR(80),    -- quirurgica, medicamentos, hospitalizacion, estudios
    fecha_solicitud     DATE            NOT NULL DEFAULT CURRENT_DATE,
    diagnostico_texto   TEXT,
    diagnostico_cie10   VARCHAR(10)     REFERENCES diagnosticos_cie10(codigo),
    procedimiento_texto TEXT,
    justificacion_medica TEXT,
    -- Respuesta
    estado              VARCHAR(30)     DEFAULT 'enviada',  -- enviada, aprobada, rechazada, pendiente
    fecha_respuesta     DATE,
    numero_autorizacion VARCHAR(80),
    monto_aprobado      DECIMAL(10,2),
    notas_respuesta     TEXT,
    -- Documentos
    pdf_url             VARCHAR(500),
    enviado_email       BOOLEAN         DEFAULT FALSE,
    fecha_envio         TIMESTAMP,
    -- Control
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA 14: CITAS Y AGENDA
-- ============================================================
CREATE TABLE citas (
    id_cita             SERIAL PRIMARY KEY,
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente),
    id_medico           INTEGER         NOT NULL REFERENCES usuarios(id_usuario),
    -- Horario
    fecha_hora_inicio   TIMESTAMP       NOT NULL,
    fecha_hora_fin      TIMESTAMP,
    duracion_min        INTEGER         DEFAULT 30,
    -- Tipo y estado
    tipo_cita           tipo_cita_enum  NOT NULL DEFAULT 'consulta',
    estado              estado_cita_enum NOT NULL DEFAULT 'pendiente',
    -- Cita relacionada a cirugía
    id_cirugia          INTEGER         REFERENCES cirugias(id_cirugia),
    -- Comunicación
    recordatorio_enviado BOOLEAN        DEFAULT FALSE,
    recordatorio_enviado_at TIMESTAMP,
    confirmacion_recibida BOOLEAN       DEFAULT FALSE,
    confirmacion_at     TIMESTAMP,
    -- Notas
    motivo_consulta_previo TEXT,
    notas               TEXT,
    -- Control de cancelación
    cancelacion_motivo  TEXT,
    cancelado_por       INTEGER         REFERENCES usuarios(id_usuario),
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_citas_medico_fecha ON citas (id_medico, fecha_hora_inicio);
CREATE INDEX idx_citas_paciente ON citas (id_paciente);
CREATE INDEX idx_citas_fecha ON citas (fecha_hora_inicio);

-- ============================================================
-- TABLA 15: PAGOS Y FINANZAS
-- ============================================================
CREATE TABLE pagos (
    id_pago             SERIAL PRIMARY KEY,
    numero_recibo       VARCHAR(20)     NOT NULL UNIQUE,   -- REC-2026-00001
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente),
    id_consulta         INTEGER         REFERENCES consultas(id_consulta),
    id_cirugia          INTEGER         REFERENCES cirugias(id_cirugia),
    id_cita             INTEGER         REFERENCES citas(id_cita),
    -- Concepto y monto
    concepto            VARCHAR(300)    NOT NULL,
    tipo_servicio       VARCHAR(50),    -- consulta, cirugia, procedimiento, estudios
    monto_total         DECIMAL(10,2)   NOT NULL,
    descuento           DECIMAL(10,2)   DEFAULT 0,
    monto_neto          DECIMAL(10,2) GENERATED ALWAYS AS (monto_total - COALESCE(descuento, 0)) STORED,
    -- Pago
    metodo_pago         metodo_pago_enum NOT NULL DEFAULT 'efectivo',
    estado              estado_pago_enum NOT NULL DEFAULT 'pagado',
    -- Seguro
    id_aseguradora      INTEGER         REFERENCES aseguradoras(id_aseguradora),
    numero_autorizacion_seguro VARCHAR(80),
    monto_cubierto_seguro DECIMAL(10,2) DEFAULT 0,
    monto_copago        DECIMAL(10,2) GENERATED ALWAYS AS
                        (GREATEST(0, monto_total - COALESCE(descuento,0) - COALESCE(monto_cubierto_seguro, 0))) STORED,
    -- Registro
    fecha_pago          DATE            NOT NULL DEFAULT CURRENT_DATE,
    registrado_por      INTEGER         REFERENCES usuarios(id_usuario),
    comprobante_url     VARCHAR(500),
    notas               TEXT,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pagos_paciente ON pagos (id_paciente, fecha_pago DESC);
CREATE INDEX idx_pagos_fecha ON pagos (fecha_pago DESC);

-- ============================================================
-- TABLA 16: DOCUMENTOS GENERADOS
-- ============================================================
CREATE TABLE documentos (
    id_documento        SERIAL PRIMARY KEY,
    tipo                tipo_doc_enum   NOT NULL,
    id_paciente         INTEGER         NOT NULL REFERENCES pacientes(id_paciente),
    id_consulta         INTEGER         REFERENCES consultas(id_consulta),
    id_cirugia          INTEGER         REFERENCES cirugias(id_cirugia),
    id_receta           INTEGER         REFERENCES recetas(id_receta),
    nombre_archivo      VARCHAR(300)    NOT NULL,
    url                 VARCHAR(500)    NOT NULL,
    tamano_bytes        INTEGER,
    generado_por        INTEGER         REFERENCES usuarios(id_usuario),
    enviado_whatsapp    BOOLEAN         DEFAULT FALSE,
    enviado_email       BOOLEAN         DEFAULT FALSE,
    fecha_envio         TIMESTAMP,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA 17: REGISTRO DE AUDITORÍA
-- ============================================================
CREATE TABLE audit_log (
    id_log              BIGSERIAL PRIMARY KEY,
    id_usuario          INTEGER         REFERENCES usuarios(id_usuario),
    accion              VARCHAR(50)     NOT NULL,   -- INSERT, UPDATE, DELETE, LOGIN, LOGOUT, VIEW
    tabla_afectada      VARCHAR(100),
    id_registro         INTEGER,
    descripcion         TEXT,
    datos_anteriores    JSONB,
    datos_nuevos        JSONB,
    ip_address          INET,
    user_agent          TEXT,
    created_at          TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_usuario ON audit_log (id_usuario, created_at DESC);
CREATE INDEX idx_audit_tabla ON audit_log (tabla_afectada, id_registro);

-- ============================================================
-- VISTAS ÚTILES
-- ============================================================

-- Vista: Agenda del día
CREATE OR REPLACE VIEW v_agenda_hoy AS
SELECT
    c.id_cita,
    c.fecha_hora_inicio,
    c.fecha_hora_fin,
    c.tipo_cita,
    c.estado,
    c.motivo_consulta_previo,
    p.nombre_completo AS paciente_nombre,
    p.numero_expediente,
    p.foto_url,
    p.telefono_tutor,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, p.fecha_nacimiento))::INTEGER AS edad_anios,
    p.seguro_medico_texto
FROM citas c
JOIN (
    SELECT pa.*, a.nombre AS seguro_medico_texto
    FROM pacientes pa
    LEFT JOIN aseguradoras a ON pa.id_aseguradora = a.id_aseguradora
) p ON c.id_paciente = p.id_paciente
WHERE c.fecha_hora_inicio::DATE = CURRENT_DATE
ORDER BY c.fecha_hora_inicio;

-- Vista: Dashboard financiero mensual
CREATE OR REPLACE VIEW v_resumen_financiero_mensual AS
SELECT
    DATE_TRUNC('month', fecha_pago) AS mes,
    COUNT(*)                         AS total_transacciones,
    SUM(monto_neto)                  AS ingresos_totales,
    SUM(CASE WHEN tipo_servicio = 'consulta' THEN monto_neto ELSE 0 END) AS ingresos_consultas,
    SUM(CASE WHEN tipo_servicio = 'cirugia'  THEN monto_neto ELSE 0 END) AS ingresos_cirugias,
    AVG(monto_neto)                  AS ticket_promedio
FROM pagos
WHERE estado IN ('pagado', 'parcial')
GROUP BY DATE_TRUNC('month', fecha_pago)
ORDER BY mes DESC;

-- Vista: Estadísticas de pacientes
CREATE OR REPLACE VIEW v_estadisticas_pacientes AS
SELECT
    COUNT(*)                                AS total_pacientes,
    COUNT(*) FILTER (WHERE activo = TRUE)   AS pacientes_activos,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') AS nuevos_ultimo_mes,
    COUNT(*) FILTER (WHERE sexo = 'M')      AS masculinos,
    COUNT(*) FILTER (WHERE sexo = 'F')      AS femeninos
FROM pacientes;

-- Vista: Pacientes con seguimiento pendiente
CREATE OR REPLACE VIEW v_seguimiento_pendiente AS
SELECT
    p.id_paciente,
    p.nombre_completo,
    p.numero_expediente,
    p.telefono_tutor,
    cir.id_cirugia,
    cir.procedimiento,
    cir.fecha_cirugia,
    CURRENT_DATE - cir.fecha_cirugia AS dias_postoperatorio,
    MAX(sp.fecha_control) AS ultimo_control
FROM cirugias cir
JOIN pacientes p ON cir.id_paciente = p.id_paciente
LEFT JOIN seguimiento_postop sp ON cir.id_cirugia = sp.id_cirugia
WHERE cir.estado = 'realizada'
  AND (sp.alta_medica IS NULL OR sp.alta_medica = FALSE)
GROUP BY p.id_paciente, p.nombre_completo, p.numero_expediente,
         p.telefono_tutor, cir.id_cirugia, cir.procedimiento, cir.fecha_cirugia
ORDER BY cir.fecha_cirugia DESC;

-- ============================================================
-- FUNCIONES Y TRIGGERS
-- ============================================================

-- Función: Generar número de expediente automático
CREATE OR REPLACE FUNCTION generar_numero_expediente()
RETURNS TRIGGER AS $$
DECLARE
    ultimo_numero INTEGER;
BEGIN
    SELECT COALESCE(MAX(CAST(SUBSTRING(numero_expediente FROM 4) AS INTEGER)), 0)
    INTO ultimo_numero
    FROM pacientes;
    NEW.numero_expediente := 'PED-' || LPAD((ultimo_numero + 1)::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generar_expediente
BEFORE INSERT ON pacientes
FOR EACH ROW
WHEN (NEW.numero_expediente IS NULL OR NEW.numero_expediente = '')
EXECUTE FUNCTION generar_numero_expediente();

-- Función: Generar número de receta automático
CREATE OR REPLACE FUNCTION generar_numero_receta()
RETURNS TRIGGER AS $$
DECLARE
    ultimo_numero INTEGER;
    anio TEXT := EXTRACT(YEAR FROM NOW())::TEXT;
BEGIN
    SELECT COALESCE(MAX(CAST(SUBSTRING(numero_receta FROM LENGTH('RX-' || anio || '-') + 1) AS INTEGER)), 0)
    INTO ultimo_numero
    FROM recetas
    WHERE numero_receta LIKE 'RX-' || anio || '-%';
    NEW.numero_receta := 'RX-' || anio || '-' || LPAD((ultimo_numero + 1)::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generar_receta
BEFORE INSERT ON recetas
FOR EACH ROW
WHEN (NEW.numero_receta IS NULL OR NEW.numero_receta = '')
EXECUTE FUNCTION generar_numero_receta();

-- Función: Generar número de cirugía automático
CREATE OR REPLACE FUNCTION generar_numero_cirugia()
RETURNS TRIGGER AS $$
DECLARE
    ultimo_numero INTEGER;
    anio TEXT := EXTRACT(YEAR FROM NOW())::TEXT;
BEGIN
    SELECT COALESCE(MAX(CAST(SUBSTRING(numero_cirugia FROM LENGTH('CIR-' || anio || '-') + 1) AS INTEGER)), 0)
    INTO ultimo_numero
    FROM cirugias
    WHERE numero_cirugia LIKE 'CIR-' || anio || '-%';
    NEW.numero_cirugia := 'CIR-' || anio || '-' || LPAD((ultimo_numero + 1)::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_generar_cirugia
BEFORE INSERT ON cirugias
FOR EACH ROW
WHEN (NEW.numero_cirugia IS NULL OR NEW.numero_cirugia = '')
EXECUTE FUNCTION generar_numero_cirugia();

-- Función: Actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_pacientes_updated_at    BEFORE UPDATE ON pacientes    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_consultas_updated_at    BEFORE UPDATE ON consultas    FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_cirugias_updated_at     BEFORE UPDATE ON cirugias     FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_citas_updated_at        BEFORE UPDATE ON citas        FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_solicitudes_updated_at  BEFORE UPDATE ON solicitudes_aseguradoras FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER trg_plantillas_updated_at   BEFORE UPDATE ON plantillas_quirurgicas    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Función: Auditoría automática en tablas clínicas
CREATE OR REPLACE FUNCTION registrar_auditoria()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (accion, tabla_afectada, id_registro, datos_anteriores)
        VALUES (TG_OP, TG_TABLE_NAME, OLD.id_paciente, row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (accion, tabla_afectada, id_registro, datos_anteriores, datos_nuevos)
        VALUES (TG_OP, TG_TABLE_NAME, NEW.id_paciente, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (accion, tabla_afectada, datos_nuevos)
        VALUES (TG_OP, TG_TABLE_NAME, row_to_json(NEW));
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_pacientes  AFTER INSERT OR UPDATE OR DELETE ON pacientes  FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();
CREATE TRIGGER trg_audit_consultas  AFTER INSERT OR UPDATE OR DELETE ON consultas  FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();
CREATE TRIGGER trg_audit_cirugias   AFTER INSERT OR UPDATE OR DELETE ON cirugias   FOR EACH ROW EXECUTE FUNCTION registrar_auditoria();

-- ============================================================
-- DATOS SEMILLA (SEED DATA)
-- ============================================================

-- Usuario administrador inicial (contraseña: MedAdmin2026 — cambiar inmediatamente)
INSERT INTO usuarios (nombre_completo, email, password_hash, rol, especialidad)
VALUES ('Administrador del Sistema', 'admin@consultorio.med', '$2b$12$placeholder_cambiar_al_iniciar', 'medico', 'Cirugía Pediátrica');

-- Aseguradoras Administradoras de Riesgos de Salud (ARS) — República Dominicana
-- Códigos de proveedor del Dr. Lorenzo Otaño (L.E.O.S.)
INSERT INTO aseguradoras (nombre, codigo) VALUES
('APS',                '65157'),
('ASEMAP',             '4457'),
('Banco Central',      '2571'),
('Banco de Reservas',  '10006213'),
('BMI Salud',          '601080045'),
('Constitución',       '6379'),
('CMD',                '9001-0915'),
('Futuro',             '13067'),
('FF.AA.',             '163548'),
('GMA',                '10339'),
('ARS Humano',         '10889'),
('Meta Salud',         '6119'),
('Monumental',         '7045'),
('PALIC',              '8261835'),
('Renacer',            '6432'),
('Salud Segura',       '11083'),
('SEMUNACED',          '228651'),
('SENASA',             '817151'),
('SEMMA',              '11235'),
('SIMAG',              '672812'),
('UASD',               '2563'),
('Universal',          '06052'),
('ARS Yunén',          '12067'),
('Sin seguro / Particular', 'PARTICULAR');

-- Diagnósticos CIE-10 frecuentes en pediatría
INSERT INTO diagnosticos_cie10 (codigo, descripcion, categoria, frecuente_pediatria) VALUES
('K35.9',  'Apendicitis aguda, sin complicaciones',                 'Abdomen',       TRUE),
('K40.9',  'Hernia inguinal unilateral, sin obstrucción ni gangrena','Hernias',       TRUE),
('K40.20', 'Hernia inguinal bilateral sin obstrucción',              'Hernias',       TRUE),
('K42.9',  'Hernia umbilical sin obstrucción ni gangrena',           'Hernias',       TRUE),
('N47',    'Fimosis y parafimosis',                                  'Urología',      TRUE),
('N97.0',  'Criptorquidia',                                         'Urología',      TRUE),
('K92.1',  'Melena',                                                 'Abdomen',       TRUE),
('K57.30', 'Diverticulosis del intestino grueso',                    'Abdomen',       FALSE),
('J06.9',  'Infección aguda de las vías respiratorias superiores',   'Respiratorio',  TRUE),
('J18.9',  'Neumonía no especificada',                               'Respiratorio',  TRUE),
('A09',    'Diarrea y gastroenteritis de presunto origen infeccioso','Digestivo',     TRUE),
('L02.9',  'Absceso cutáneo, furúnculo y ántrax',                   'Piel',          TRUE),
('S06.9',  'Traumatismo intracraneal no especificado',              'Neurología',    FALSE),
('T18.1',  'Cuerpo extraño en estómago',                            'Abdomen',       TRUE),
('R10.0',  'Dolor abdominal agudo',                                  'Síntomas',      TRUE),
('Z76.9',  'Consulta de control de salud',                           'Preventivo',    TRUE);

-- Medicamentos pediátricos más frecuentes
INSERT INTO medicamentos_catalogo
  (nombre_generico, nombre_comercial, grupo_farmacologico, dosis_mg_kg_dia, dosis_maxima_dia_mg,
   frecuencias_disponibles, presentaciones, vias_administracion) VALUES

('Amoxicilina', 'Amoxil', 'Antibiótico betalactámico', 40, 3000,
 '["cada 8 horas","cada 12 horas"]',
 '[{"forma":"jarabe","concentracion":"250mg/5ml","volumen":"100ml"},{"forma":"cápsulas","concentracion":"500mg"}]',
 '["oral"]'),

('Amoxicilina + Ácido Clavulánico', 'Augmentin', 'Antibiótico combinado', 40, 3000,
 '["cada 8 horas","cada 12 horas"]',
 '[{"forma":"jarabe","concentracion":"250mg/62.5mg/5ml"},{"forma":"tabletas","concentracion":"500mg/125mg"}]',
 '["oral"]'),

('Ibuprofeno', 'Advil / Motrin', 'AINE / Antipirético analgésico', 30, 1200,
 '["cada 6 horas","cada 8 horas"]',
 '[{"forma":"suspensión","concentracion":"200mg/5ml"},{"forma":"tabletas","concentracion":"400mg"}]',
 '["oral"]'),

('Acetaminofén', 'Tylenol / Panadol', 'Antipirético analgésico', 15, 4000,
 '["cada 4 horas","cada 6 horas"]',
 '[{"forma":"suspensión","concentracion":"160mg/5ml"},{"forma":"tabletas","concentracion":"500mg"},{"forma":"gotas","concentracion":"100mg/ml"}]',
 '["oral","rectal"]'),

('Cetirizina', 'Zyrtec', 'Antihistamínico', 0.25, 10,
 '["cada 24 horas"]',
 '[{"forma":"jarabe","concentracion":"5mg/5ml"},{"forma":"tabletas","concentracion":"10mg"}]',
 '["oral"]'),

('Metronidazol', 'Flagyl', 'Antibiótico antiparasitario', 30, 2000,
 '["cada 8 horas"]',
 '[{"forma":"suspensión","concentracion":"125mg/5ml"},{"forma":"tabletas","concentracion":"250mg"}]',
 '["oral"]'),

('Omeprazol', 'Prilosec', 'Inhibidor bomba de protones', 1, 40,
 '["cada 24 horas","cada 12 horas"]',
 '[{"forma":"cápsulas","concentracion":"20mg"},{"forma":"tabletas dispersables","concentracion":"10mg"}]',
 '["oral"]'),

('Ranitidina', 'Zantac', 'Antagonista H2', 6, 300,
 '["cada 12 horas"]',
 '[{"forma":"jarabe","concentracion":"75mg/5ml"},{"forma":"tabletas","concentracion":"150mg"}]',
 '["oral"]'),

('Azitromicina', 'Zithromax', 'Antibiótico macrólido', 10, 500,
 '["cada 24 horas"]',
 '[{"forma":"suspensión","concentracion":"200mg/5ml"},{"forma":"tabletas","concentracion":"500mg"}]',
 '["oral"]'),

('Ketorolaco', 'Toradol', 'AINE / Analgésico', 1, 120,
 '["cada 6 horas","cada 8 horas"]',
 '[{"forma":"tabletas","concentracion":"10mg"},{"forma":"inyectable","concentracion":"30mg/ml"}]',
 '["oral","intramuscular","intravenoso"]');

-- Plantillas quirúrgicas frecuentes
INSERT INTO plantillas_quirurgicas
  (nombre_procedimiento, codigo_cpt, categoria, descripcion_template,
   pasos_quirurgicos, indicaciones_postop_template, materiales_tipicos, duracion_estimada_min) VALUES

('Herniorrafia inguinal unilateral', '49500', 'Hernias',
'Previa anestesia {{tipo_anestesia}}, en decúbito supino, asepsia y antisepsia de región inguino-escrotal. Se realizó incisión tipo Pfannenstiel de {{longitud}} cm en pliegue inguinal derecho/izquierdo. Por planos hasta identificar aponeurosis del oblicuo mayor. Apertura de la misma y disección del cordón espermático. Identificación del saco herniario de tipo {{tipo_hernia}}, el cual se disecó hasta la unión con el peritoneo parietal, se ligó con {{sutura_ligadura}} y se resecó. Cierre por planos con {{suturas}}. Piel con {{sutura_piel}}. Sin complicaciones.',
'["Anestesia general/regional satisfactoria.","Asepsia y antisepsia de campo operatorio.","Incisión inguinal transversa de {{longitud}} cm.","Disección por planos hasta identificar cordón espermático.","Identificación y disección del saco herniario.","Ligadura alta del saco y resección.","Cierre del piso inguinal con sutura no absorbible.","Cierre por planos con sutura absorbible.","Piel con sutura subcutánea absorbible.","Apósito estéril. Sin complicaciones."]',
'Reposo relativo por 7 días. Baño con agua y jabón a las 48 horas. No esfuerzo físico por 4 semanas. Acetaminofén 15mg/kg/dosis cada 6 horas por 3 días si dolor. Consulta de seguimiento en 7 días. Acudir a urgencias si: fiebre mayor de 38.5°C, sangrado activo, enrojecimiento excesivo de la herida.',
'["Sutura Vicryl 3-0","Sutura PDS 3-0","Sutura Prolene 3-0","Bisturí frío","Electrocauterio","Apósitos estériles"]',
45),

('Herniorrafia umbilical', '49585', 'Hernias',
'Previa anestesia {{tipo_anestesia}}, en decúbito supino, asepsia y antisepsia de región umbilical. Incisión semicircular infraumbilical de {{longitud}} cm. Disección hasta identificar el defecto fascial de {{cm_defecto}} cm. Reducción del contenido herniario. Cierre del defecto aponeurótico con sutura {{sutura}} en puntos simples/continuo. Cierre subcutáneo y de piel. Sin complicaciones.',
'["Anestesia satisfactoria.","Asepsia y antisepsia del campo operatorio.","Incisión semicircular infraumbilical de {{longitud}} cm.","Disección hasta identificar saco herniario umbilical.","Reducción del contenido: {{contenido}}.","Resección del saco herniario.","Cierre del defecto aponeurótico con {{sutura}}.","Cierre subcutáneo y de piel.","Apósito compresivo. Sin complicaciones."]',
'Reposo relativo 5 días. Baño a las 48 horas. Acetaminofén por dolor. Control en 5-7 días. Sin levantar objetos pesados por 3 semanas.',
'["Sutura Vicryl 2-0","Sutura Monocryl 3-0","Bisturí","Electrocauterio","Apósito adhesivo"]',
30),

('Apendicectomía laparoscópica', '44950', 'Abdomen',
'Previa anestesia general, en decúbito supino, asepsia y antisepsia de abdomen. Abordaje laparoscópico con colocación de trocar umbilical de 10mm y dos trocares de 5mm. Exploración de cavidad abdominal evidenciando {{hallazgos_apendice}}. Disección del mesoapéndice con {{instrumento}}. Ligadura de la base apendicular con endo-loops. Resección del apéndice y extracción por trocar umbilical. Irrigación de cavidad con solución salina. Revisión de hemostasia. Cierre de puertos. Sin complicaciones.',
'["Anestesia general satisfactoria.","Posición en decúbito supino.","Asepsia y antisepsia de abdomen completo.","Colocación de trocar umbilical de 10mm y 2 trocares de 5mm.","Exploración laparoscópica de cavidad abdominal.","Visualización de apéndice cecal: {{descripcion_apendice}}.","Disección del mesoapéndice y ligadura vascular.","Colocación de endo-loops en base apendicular.","Resección del apéndice cecal.","Revisión de hemostasia y limpieza de cavidad.","Extracción de pieza en bolsa de protección.","Cierre de puertos. Apósitos estériles."]',
'Dieta líquida clara 24 horas, progresar según tolerancia. Deambulación temprana. Acetaminofén e Ibuprofeno alternados por dolor. Antibióticos según indicación. Control en 5-7 días. Acudir a urgencias si: fiebre, dolor abdominal intenso, vómitos persistentes.',
'["Trocares 10mm y 5mm","Endo-loops Ethicon","Laparoscopio 0° 10mm","Bisturí armónico/electrocauterio","Bolsa de extracción laparoscópica","Irrigación-aspiración"]',
60),

('Circuncisión / Frenulotomía', '54150', 'Urología',
'Previa anestesia {{tipo_anestesia}}, en decúbito supino, asepsia y antisepsia de región genital. Bloqueo dorsal del pene con lidocaína. {{descripcion_tecnica}}. Sin complicaciones hemostáticas.',
'["Anestesia satisfactoria, bloqueo dorsal del pene.","Asepsia y antisepsia de campo operatorio.","Identificación y evaluación del prepucio.","{{tecnica_empleada}}.","Hemostasia meticulosa con electrocauterio bipolar.","Sutura prepucial con Vicryl 4-0 puntos simples.","Apósito de vaselina. Sin complicaciones."]',
'Mantener apósito 24 horas. Baño con agua tibia desde el día siguiente. Acetaminofén cada 6 horas por 3 días. Aplicar vaselina en la herida cada cambio de pañal. Ropa interior holgada. Control en 7 días. Acudir si sangrado activo o retención urinaria.',
'["Sutura Vicryl 4-0","Electrocauterio bipolar","Apósito de vaselina","Lidocaína 1% sin epinefrina"]',
25),

('Orquidopexia (criptorquidia)', '54640', 'Urología',
'Previa anestesia general, asepsia y antisepsia de región inguino-escrotal. Incisión inguinal para identificación del testículo no descendido en {{ubicacion}}: canal inguinal / cavidad abdominal. Disección del cordón espermático para ganar longitud. Creación de bolsa subdartos en escroto ipsilateral. Fijación del testículo en posición escrotal sin tensión con sutura {{sutura}}. Cierre por planos. Sin complicaciones.',
'["Anestesia general satisfactoria.","Asepsia y antisepsia de campo operatorio inguino-escrotal.","Incisión inguinal de {{cm}} cm.","Localización del testículo en {{ubicacion}}.","Disección del cordón espermático y liberación de adherencias.","Verificación de aporte vascular adecuado.","Creación de bolsa subdartos escrotal.","Descenso y fijación testicular sin tensión.","Cierre por planos con sutura absorbible.","Apósito estéril. Sin complicaciones."]',
'Reposo relativo 7 días. Ropa interior de soporte. Acetaminofén por dolor. Evitar actividad física por 4 semanas. Control en 7-10 días. Ultrasonido escrotal de seguimiento en 3 meses.',
'["Sutura Vicryl 3-0","Sutura Monocryl 4-0","Electrocauterio","Apósitos estériles"]',
50);

-- ============================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ============================================================
COMMENT ON TABLE pacientes IS 'Expedientes digitales de todos los pacientes pediátricos del consultorio';
COMMENT ON TABLE historial_clinico IS 'Antecedentes clínicos, alergias, medicamentos crónicos y vacunas. Relación 1:1 con pacientes';
COMMENT ON TABLE consultas IS 'Registro de cada consulta médica con contenido clínico completo';
COMMENT ON TABLE cirugias IS 'Registro de procedimientos quirúrgicos con toda la documentación del acto operatorio';
COMMENT ON TABLE recetas IS 'Prescripciones médicas con cálculo automático de dosis pediátricas';
COMMENT ON TABLE citas IS 'Agenda del consultorio con estados y control de recordatorios';
COMMENT ON TABLE pagos IS 'Control financiero de ingresos, cobros y pagos de seguro';
COMMENT ON TABLE audit_log IS 'Trazabilidad completa de todas las acciones en el sistema para seguridad y cumplimiento';

-- ============================================================
-- FIN DEL SCHEMA — Sistema listo para uso
-- ============================================================
-- Para inicializar: psql -U postgres -d consultorio -f schema.sql
-- Crear base de datos primero: CREATE DATABASE consultorio_pediatrico;
