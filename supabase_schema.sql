-- ══════════════════════════════════════════════════════════════
--  SCHEMA — Sistema de Gestión Consultorio Dr. Otaño
--  Ejecutar en: Supabase Dashboard → SQL Editor → New Query
-- ══════════════════════════════════════════════════════════════

-- ── Habilitar extensión UUID ──────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── PACIENTES ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pacientes (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  expediente    TEXT UNIQUE,
  nombre        TEXT NOT NULL,
  fecha_nac     DATE,
  sexo          TEXT,
  cedula        TEXT,
  telefono      TEXT,
  telefono2     TEXT,
  email         TEXT,
  direccion     TEXT,
  padre         TEXT,
  madre         TEXT,
  tipo_sangre   TEXT,
  alergias      TEXT,
  antecedentes  TEXT,
  aseguradora   TEXT,
  poliza        TEXT,
  notas         TEXT,
  activo        BOOLEAN DEFAULT true,
  creado_en     TIMESTAMPTZ DEFAULT NOW(),
  actualizado_en TIMESTAMPTZ DEFAULT NOW()
);

-- ── CONSULTAS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS consultas (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  paciente_id     UUID REFERENCES pacientes(id) ON DELETE CASCADE,
  fecha           DATE NOT NULL DEFAULT CURRENT_DATE,
  hora            TIME,
  motivo          TEXT,
  historia        TEXT,
  examen_fisico   TEXT,
  peso            NUMERIC(5,2),
  talla           NUMERIC(5,2),
  temp            NUMERIC(4,1),
  fc              INTEGER,
  fr              INTEGER,
  sat             NUMERIC(4,1),
  pa              TEXT,
  diagnostico     TEXT,
  plan            TEXT,
  indicaciones    TEXT,
  examenes        TEXT,
  proxima_cita    DATE,
  tipo            TEXT DEFAULT 'consulta',
  creado_en       TIMESTAMPTZ DEFAULT NOW()
);

-- ── CITAS / AGENDA ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS citas (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  paciente_id     UUID REFERENCES pacientes(id) ON DELETE SET NULL,
  paciente_nombre TEXT,
  fecha           DATE NOT NULL,
  hora            TIME NOT NULL,
  duracion        INTEGER DEFAULT 30,
  tipo            TEXT DEFAULT 'consulta',
  motivo          TEXT,
  estado          TEXT DEFAULT 'confirmada',
  telefono        TEXT,
  notas           TEXT,
  color           TEXT DEFAULT '#0E7C7B',
  creado_en       TIMESTAMPTZ DEFAULT NOW()
);

-- ── ASEGURADORAS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aseguradoras (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nombre          TEXT NOT NULL UNIQUE,
  sigla           TEXT,
  tel             TEXT,
  tel_aut         TEXT,
  email           TEXT,
  web             TEXT,
  ejecutivo       TEXT,
  tel_ejecutivo   TEXT,
  cod_proveedor   TEXT,
  pin             TEXT,
  red             TEXT DEFAULT 'abierta',
  deducible       NUMERIC(10,2) DEFAULT 0,
  cobertura       NUMERIC(5,2) DEFAULT 80,
  procedimientos  TEXT,
  notas           TEXT,
  creado_en       TIMESTAMPTZ DEFAULT NOW()
);

-- ── SOLICITUDES ARS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS solicitudes (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  numero          TEXT UNIQUE,
  tipo            TEXT NOT NULL,
  paciente_id     UUID REFERENCES pacientes(id) ON DELETE SET NULL,
  paciente_nombre TEXT,
  aseguradora_id  UUID REFERENCES aseguradoras(id) ON DELETE SET NULL,
  aseguradora     TEXT,
  poliza          TEXT,
  titular         TEXT,
  diagnostico     TEXT,
  cie10           TEXT,
  procedimiento   TEXT,
  cpt             TEXT,
  hospital        TEXT,
  monto_solicitado NUMERIC(12,2) DEFAULT 0,
  monto_aprobado  NUMERIC(12,2),
  monto_pagado    NUMERIC(12,2),
  monto_paciente  NUMERIC(12,2),
  deducible       NUMERIC(12,2) DEFAULT 0,
  cobertura_pct   NUMERIC(5,2),
  num_autorizacion TEXT,
  prioridad       TEXT DEFAULT 'normal',
  estado          TEXT DEFAULT 'pendiente',
  fecha_servicio  DATE,
  fecha_envio     DATE,
  fecha_aprobacion DATE,
  fecha_pago      DATE,
  justificacion   TEXT,
  notas           TEXT,
  documentos      JSONB DEFAULT '[]',
  creado_en       TIMESTAMPTZ DEFAULT NOW(),
  actualizado_en  TIMESTAMPTZ DEFAULT NOW()
);

-- ── HONORARIOS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS honorarios (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  aseguradora_id  UUID REFERENCES aseguradoras(id) ON DELETE CASCADE,
  aseguradora     TEXT,
  procedimiento   TEXT NOT NULL,
  cpt             TEXT,
  cie10           TEXT,
  monto           NUMERIC(12,2) DEFAULT 0,
  cobertura_pct   NUMERIC(5,2) DEFAULT 80,
  monto_aprobado_historico NUMERIC(12,2),
  dias_respuesta  INTEGER,
  notas           TEXT,
  creado_en       TIMESTAMPTZ DEFAULT NOW()
);

-- ── DOCUMENTOS GENERADOS ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS documentos (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  paciente_id     UUID REFERENCES pacientes(id) ON DELETE SET NULL,
  paciente_nombre TEXT,
  tipo            TEXT NOT NULL,
  titulo          TEXT,
  contenido       JSONB,
  creado_en       TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════════════
--  ÍNDICES — para búsquedas rápidas
-- ══════════════════════════════════════════════════════════════
CREATE INDEX IF NOT EXISTS idx_pacientes_nombre     ON pacientes(nombre);
CREATE INDEX IF NOT EXISTS idx_pacientes_expediente ON pacientes(expediente);
CREATE INDEX IF NOT EXISTS idx_consultas_paciente   ON consultas(paciente_id);
CREATE INDEX IF NOT EXISTS idx_consultas_fecha      ON consultas(fecha);
CREATE INDEX IF NOT EXISTS idx_citas_fecha          ON citas(fecha);
CREATE INDEX IF NOT EXISTS idx_solicitudes_estado   ON solicitudes(estado);
CREATE INDEX IF NOT EXISTS idx_solicitudes_paciente ON solicitudes(paciente_id);

-- ══════════════════════════════════════════════════════════════
--  ROW LEVEL SECURITY — datos seguros (acceso solo con tu key)
-- ══════════════════════════════════════════════════════════════
ALTER TABLE pacientes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE consultas    ENABLE ROW LEVEL SECURITY;
ALTER TABLE citas        ENABLE ROW LEVEL SECURITY;
ALTER TABLE aseguradoras ENABLE ROW LEVEL SECURITY;
ALTER TABLE solicitudes  ENABLE ROW LEVEL SECURITY;
ALTER TABLE honorarios   ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos   ENABLE ROW LEVEL SECURITY;

-- Políticas: acceso total con la anon key (para app de un solo usuario)
CREATE POLICY "acceso_total" ON pacientes    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "acceso_total" ON consultas    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "acceso_total" ON citas        FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "acceso_total" ON aseguradoras FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "acceso_total" ON solicitudes  FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "acceso_total" ON honorarios   FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "acceso_total" ON documentos   FOR ALL USING (true) WITH CHECK (true);
