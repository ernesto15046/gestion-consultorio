// ══════════════════════════════════════════════════════════════
//  SUPABASE — Conexión y capa de datos sincronizada
//  Reemplaza localStorage con base de datos en la nube
// ══════════════════════════════════════════════════════════════

const SUPABASE_URL  = 'https://cltipxpaudwztcdrjfzp.supabase.co';
const SUPABASE_KEY  = 'TU_ANON_KEY_AQUI'; // ← se reemplaza cuando el usuario envíe la key

// ── Cliente Supabase (cargado desde CDN en cada HTML) ─────────
let _sb = null;
function getSB() {
  if (!_sb) _sb = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  return _sb;
}

// ══════════════════════════════════════════════════════════════
//  CAPA DE DATOS — Reemplaza todas las llamadas a localStorage
//  Uso: await DB.pacientes.getAll()
//       await DB.pacientes.save(obj)
//       await DB.pacientes.delete(id)
// ══════════════════════════════════════════════════════════════
const DB = {

  // ── PACIENTES ───────────────────────────────────────────────
  pacientes: {
    async getAll() {
      const { data, error } = await getSB()
        .from('pacientes').select('*').order('nombre');
      if (error) { console.error('pacientes.getAll:', error); return []; }
      return data.map(_mapPaciente);
    },
    async getById(id) {
      const { data } = await getSB()
        .from('pacientes').select('*').eq('id', id).single();
      return data ? _mapPaciente(data) : null;
    },
    async save(p) {
      const row = _unmapPaciente(p);
      if (p.id && !p.id.startsWith('PAC-')) {
        // Update existente
        const { data, error } = await getSB()
          .from('pacientes').update(row).eq('id', p.id).select().single();
        if (error) throw error;
        return _mapPaciente(data);
      } else {
        // Nuevo — generar expediente si no tiene
        if (!row.expediente) row.expediente = await _nextExpediente();
        const { data, error } = await getSB()
          .from('pacientes').insert(row).select().single();
        if (error) throw error;
        return _mapPaciente(data);
      }
    },
    async delete(id) {
      const { error } = await getSB().from('pacientes').delete().eq('id', id);
      if (error) throw error;
    },
    async search(q) {
      const { data } = await getSB()
        .from('pacientes').select('*')
        .ilike('nombre', `%${q}%`).order('nombre').limit(20);
      return (data || []).map(_mapPaciente);
    }
  },

  // ── CONSULTAS ───────────────────────────────────────────────
  consultas: {
    async getAll() {
      const { data } = await getSB()
        .from('consultas').select('*, pacientes(nombre, expediente)')
        .order('fecha', { ascending: false });
      return (data || []).map(_mapConsulta);
    },
    async getByPaciente(pacienteId) {
      const { data } = await getSB()
        .from('consultas').select('*').eq('paciente_id', pacienteId)
        .order('fecha', { ascending: false });
      return (data || []).map(_mapConsulta);
    },
    async save(c) {
      const row = _unmapConsulta(c);
      if (c.id && !c.id.toString().startsWith('CON-')) {
        const { data, error } = await getSB()
          .from('consultas').update(row).eq('id', c.id).select().single();
        if (error) throw error;
        return _mapConsulta(data);
      } else {
        const { data, error } = await getSB()
          .from('consultas').insert(row).select().single();
        if (error) throw error;
        return _mapConsulta(data);
      }
    },
    async delete(id) {
      await getSB().from('consultas').delete().eq('id', id);
    }
  },

  // ── CITAS ───────────────────────────────────────────────────
  citas: {
    async getAll() {
      const { data } = await getSB()
        .from('citas').select('*').order('fecha').order('hora');
      return (data || []).map(_mapCita);
    },
    async getByFecha(fecha) {
      const { data } = await getSB()
        .from('citas').select('*').eq('fecha', fecha).order('hora');
      return (data || []).map(_mapCita);
    },
    async getRango(desde, hasta) {
      const { data } = await getSB()
        .from('citas').select('*')
        .gte('fecha', desde).lte('fecha', hasta).order('fecha').order('hora');
      return (data || []).map(_mapCita);
    },
    async save(c) {
      const row = _unmapCita(c);
      if (c.id && !c.id.toString().startsWith('CIT-')) {
        const { data, error } = await getSB()
          .from('citas').update(row).eq('id', c.id).select().single();
        if (error) throw error;
        return _mapCita(data);
      } else {
        const { data, error } = await getSB()
          .from('citas').insert(row).select().single();
        if (error) throw error;
        return _mapCita(data);
      }
    },
    async delete(id) {
      await getSB().from('citas').delete().eq('id', id);
    }
  },

  // ── ASEGURADORAS ────────────────────────────────────────────
  aseguradoras: {
    async getAll() {
      const { data } = await getSB()
        .from('aseguradoras').select('*').order('nombre');
      return (data || []).map(_mapARS);
    },
    async save(a) {
      const row = _unmapARS(a);
      if (a.id && !a.id.startsWith('ASG-')) {
        const { data, error } = await getSB()
          .from('aseguradoras').update(row).eq('id', a.id).select().single();
        if (error) throw error;
        return _mapARS(data);
      } else {
        const { data, error } = await getSB()
          .from('aseguradoras').insert(row).select().single();
        if (error) throw error;
        return _mapARS(data);
      }
    }
  },

  // ── SOLICITUDES ─────────────────────────────────────────────
  solicitudes: {
    async getAll() {
      const { data } = await getSB()
        .from('solicitudes').select('*').order('creado_en', { ascending: false });
      return (data || []).map(_mapSolicitud);
    },
    async getByARS(arsId) {
      const { data } = await getSB()
        .from('solicitudes').select('*').eq('aseguradora_id', arsId)
        .order('creado_en', { ascending: false });
      return (data || []).map(_mapSolicitud);
    },
    async save(s) {
      const row = _unmapSolicitud(s);
      if (s.id && !s.id.startsWith('SOL-')) {
        const { data, error } = await getSB()
          .from('solicitudes').update(row).eq('id', s.id).select().single();
        if (error) throw error;
        return _mapSolicitud(data);
      } else {
        if (!row.numero) row.numero = await _nextNumeroSolicitud();
        const { data, error } = await getSB()
          .from('solicitudes').insert(row).select().single();
        if (error) throw error;
        return _mapSolicitud(data);
      }
    },
    async cambiarEstado(id, estado, extra = {}) {
      const update = { estado, actualizado_en: new Date().toISOString(), ...extra };
      const { data, error } = await getSB()
        .from('solicitudes').update(update).eq('id', id).select().single();
      if (error) throw error;
      return _mapSolicitud(data);
    },
    async delete(id) {
      await getSB().from('solicitudes').delete().eq('id', id);
    }
  },

  // ── HONORARIOS ──────────────────────────────────────────────
  honorarios: {
    async getAll() {
      const { data } = await getSB()
        .from('honorarios').select('*').order('aseguradora').order('procedimiento');
      return data || [];
    },
    async save(h) {
      if (h.id && !h.id.startsWith('HON-')) {
        const { data, error } = await getSB()
          .from('honorarios').update(h).eq('id', h.id).select().single();
        if (error) throw error;
        return data;
      } else {
        const { id: _id, ...row } = h;
        const { data, error } = await getSB()
          .from('honorarios').insert(row).select().single();
        if (error) throw error;
        return data;
      }
    },
    async delete(id) {
      await getSB().from('honorarios').delete().eq('id', id);
    }
  }
};

// ══════════════════════════════════════════════════════════════
//  MAPPERS — Convierte formato BD ↔ formato app legacy
//  (mantiene compatibilidad con el código existente)
// ══════════════════════════════════════════════════════════════

function _mapPaciente(r) {
  return {
    id: r.id, expediente: r.expediente, nombre: r.nombre,
    fechaNac: r.fecha_nac, sexo: r.sexo, cedula: r.cedula,
    telefono: r.telefono, telefono2: r.telefono2, email: r.email,
    direccion: r.direccion, padre: r.padre, madre: r.madre,
    tipoSangre: r.tipo_sangre, alergias: r.alergias,
    antecedentes: r.antecedentes, aseguradora: r.aseguradora,
    poliza: r.poliza, notas: r.notas,
    creadoEn: r.creado_en
  };
}
function _unmapPaciente(p) {
  return {
    expediente: p.expediente, nombre: p.nombre,
    fecha_nac: p.fechaNac || null, sexo: p.sexo, cedula: p.cedula,
    telefono: p.telefono, telefono2: p.telefono2, email: p.email,
    direccion: p.direccion, padre: p.padre, madre: p.madre,
    tipo_sangre: p.tipoSangre, alergias: p.alergias,
    antecedentes: p.antecedentes, aseguradora: p.aseguradora,
    poliza: p.poliza, notas: p.notas,
    actualizado_en: new Date().toISOString()
  };
}

function _mapConsulta(r) {
  return {
    id: r.id, pacienteId: r.paciente_id,
    pacienteNombre: r.pacientes?.nombre || r.paciente_nombre,
    fecha: r.fecha, hora: r.hora,
    motivo: r.motivo, historia: r.historia,
    examenFisico: r.examen_fisico,
    peso: r.peso, talla: r.talla, temp: r.temp,
    fc: r.fc, fr: r.fr, sat: r.sat, pa: r.pa,
    diagnostico: r.diagnostico, plan: r.plan,
    indicaciones: r.indicaciones, examenes: r.examenes,
    proximaCita: r.proxima_cita, tipo: r.tipo,
    creadoEn: r.creado_en
  };
}
function _unmapConsulta(c) {
  return {
    paciente_id: c.pacienteId, fecha: c.fecha, hora: c.hora || null,
    motivo: c.motivo, historia: c.historia,
    examen_fisico: c.examenFisico || c.examen,
    peso: c.peso || null, talla: c.talla || null,
    temp: c.temp || null, fc: c.fc || null,
    fr: c.fr || null, sat: c.sat || null, pa: c.pa || null,
    diagnostico: c.diagnostico, plan: c.plan,
    indicaciones: c.indicaciones, examenes: c.examenes,
    proxima_cita: c.proximaCita || null, tipo: c.tipo || 'consulta'
  };
}

function _mapCita(r) {
  return {
    id: r.id, pacienteId: r.paciente_id,
    nombre: r.paciente_nombre, fecha: r.fecha, hora: r.hora,
    duracion: r.duracion, tipo: r.tipo, motivo: r.motivo,
    estado: r.estado, telefono: r.telefono,
    notas: r.notas, color: r.color
  };
}
function _unmapCita(c) {
  return {
    paciente_id: c.pacienteId || null,
    paciente_nombre: c.nombre || c.pacienteNombre,
    fecha: c.fecha, hora: c.hora,
    duracion: c.duracion || 30, tipo: c.tipo || 'consulta',
    motivo: c.motivo, estado: c.estado || 'confirmada',
    telefono: c.telefono, notas: c.notas, color: c.color || '#0E7C7B'
  };
}

function _mapARS(r) {
  return {
    id: r.id, nombre: r.nombre, sigla: r.sigla,
    tel: r.tel, telAut: r.tel_aut, email: r.email,
    web: r.web, ejecutivo: r.ejecutivo, telEj: r.tel_ejecutivo,
    codProv: r.cod_proveedor, pin: r.pin,
    red: r.red, deducible: r.deducible,
    cobertura: r.cobertura, procedimientos: r.procedimientos,
    notas: r.notas, creado: r.creado_en
  };
}
function _unmapARS(a) {
  return {
    nombre: a.nombre, sigla: a.sigla,
    tel: a.tel, tel_aut: a.telAut, email: a.email,
    web: a.web, ejecutivo: a.ejecutivo, tel_ejecutivo: a.telEj,
    cod_proveedor: a.codProv, pin: a.pin,
    red: a.red, deducible: a.deducible,
    cobertura: a.cobertura, procedimientos: a.procedimientos,
    notas: a.notas
  };
}

function _mapSolicitud(r) {
  return {
    id: r.id, numero: r.numero, tipo: r.tipo,
    pacienteId: r.paciente_id, paciente: r.paciente_nombre,
    aseguradoraId: r.aseguradora_id, aseguradora: r.aseguradora,
    poliza: r.poliza, titular: r.titular,
    diagnostico: r.diagnostico, cie10: r.cie10,
    procedimiento: r.procedimiento, cpt: r.cpt, hospital: r.hospital,
    monto: r.monto_solicitado,
    montoAprobado: r.monto_aprobado,
    montoPagado: r.monto_pagado,
    montoPaciente: r.monto_paciente,
    deducible: r.deducible,
    coberturaPct: r.cobertura_pct,
    numAut: r.num_autorizacion,
    prioridad: r.prioridad, estado: r.estado,
    fechaServicio: r.fecha_servicio,
    fechaEnvio: r.fecha_envio,
    fechaAprobacion: r.fecha_aprobacion,
    fechaPago: r.fecha_pago,
    justificacion: r.justificacion, notas: r.notas,
    documentos: r.documentos || [],
    fechaCreacion: r.creado_en?.split('T')[0]
  };
}
function _unmapSolicitud(s) {
  return {
    tipo: s.tipo, paciente_id: s.pacienteId || null,
    paciente_nombre: s.paciente,
    aseguradora_id: s.aseguradoraId || null,
    aseguradora: s.aseguradora, poliza: s.poliza, titular: s.titular,
    diagnostico: s.diagnostico, cie10: s.cie10,
    procedimiento: s.procedimiento, cpt: s.cpt, hospital: s.hospital,
    monto_solicitado: s.monto || 0,
    monto_aprobado: s.montoAprobado || null,
    monto_pagado: s.montoPagado || null,
    monto_paciente: s.montoPaciente || null,
    deducible: s.deducible || 0,
    cobertura_pct: s.coberturaPct || null,
    num_autorizacion: s.numAut || null,
    prioridad: s.prioridad || 'normal', estado: s.estado || 'pendiente',
    fecha_servicio: s.fechaServicio || null,
    justificacion: s.justificacion, notas: s.notas,
    documentos: s.documentos || [],
    actualizado_en: new Date().toISOString()
  };
}

// ══════════════════════════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════════════════════════
async function _nextExpediente() {
  const { count } = await getSB()
    .from('pacientes').select('*', { count: 'exact', head: true });
  const n = (count || 0) + 1;
  return 'PAC' + String(n).padStart(4, '0');
}

async function _nextNumeroSolicitud() {
  const year = new Date().getFullYear();
  const { count } = await getSB()
    .from('solicitudes').select('*', { count: 'exact', head: true })
    .gte('creado_en', `${year}-01-01`);
  const n = (count || 0) + 1;
  return `SOL-${year}-${String(n).padStart(4, '0')}`;
}

// ══════════════════════════════════════════════════════════════
//  MIGRACIÓN — Exporta datos de localStorage a Supabase
//  Ejecutar UNA SOLA VEZ desde la computadora con datos
// ══════════════════════════════════════════════════════════════
async function migrarLocalStorageASupabase() {
  const log = (msg, ok = true) => console.log((ok ? '✅' : '❌') + ' ' + msg);

  try {
    // 1. Pacientes
    const pacs = JSON.parse(localStorage.getItem('mc_pacientes') || '[]');
    if (pacs.length) {
      for (const p of pacs) {
        try { await DB.pacientes.save(p); log('Paciente: ' + p.nombre); }
        catch(e) { log('Paciente ' + p.nombre + ': ' + e.message, false); }
      }
    }

    // 2. Consultas
    const cons = JSON.parse(localStorage.getItem('mc_consultas') || '[]');
    if (cons.length) {
      // Necesitamos mapear IDs legacy → UUIDs nuevos
      const pacsNuevos = await DB.pacientes.getAll();
      for (const c of cons) {
        const pac = pacsNuevos.find(p => p.expediente === c.pacienteId || p.nombre === c.pacienteNombre);
        if (pac) {
          try {
            await DB.consultas.save({ ...c, pacienteId: pac.id });
            log('Consulta: ' + (c.fecha || '') + ' ' + (pac.nombre || ''));
          } catch(e) { log('Consulta error: ' + e.message, false); }
        }
      }
    }

    // 3. Citas
    const citas = JSON.parse(localStorage.getItem('mc_citas') || '[]');
    for (const c of citas) {
      try { await DB.citas.save(c); log('Cita: ' + c.fecha + ' ' + c.nombre); }
      catch(e) { log('Cita error: ' + e.message, false); }
    }

    // 4. Aseguradoras
    const arsList = JSON.parse(localStorage.getItem('mc_aseguradoras') || '[]');
    for (const a of arsList) {
      try { await DB.aseguradoras.save(a); log('ARS: ' + a.nombre); }
      catch(e) { log('ARS error: ' + e.message, false); }
    }

    // 5. Solicitudes
    const sols = JSON.parse(localStorage.getItem('mc_solicitudes') || '[]');
    for (const s of sols) {
      try { await DB.solicitudes.save(s); log('Solicitud: ' + s.id); }
      catch(e) { log('Solicitud error: ' + e.message, false); }
    }

    alert('✅ Migración completada. Revisa la consola para ver el detalle.');
  } catch(e) {
    console.error('Error en migración:', e);
    alert('❌ Error en migración: ' + e.message);
  }
}

// Exponer globalmente para usar desde consola del navegador
window.DB = DB;
window.migrarLocalStorageASupabase = migrarLocalStorageASupabase;
