'use strict';

const DEFAULT_URL = 'https://detector-anomalias-nosql.onrender.com';

function normalizeBaseUrl(raw) {
  let url;
  try { url = new URL(String(raw || '').trim()); }
  catch { throw new Error('La URL de FastAPI no es válida.'); }
  const isLocal = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if (!(url.protocol === 'https:' || (url.protocol === 'http:' && isLocal))) {
    throw new Error('Usa HTTPS; HTTP solo está permitido en localhost.');
  }
  if (url.username || url.password || url.search || url.hash) {
    throw new Error('La URL no puede incluir credenciales, parámetros ni fragmentos.');
  }
  if (url.pathname !== '/' && url.pathname !== '') {
    throw new Error('Utiliza la URL base de FastAPI, sin /docs, /events ni otras rutas.');
  }
  return url.origin;
}

function validateEvent(candidate) {
  const event = {
    user_id: String(candidate?.user_id || '').trim(),
    operation: String(candidate?.operation || '').toUpperCase().trim(),
    collection: String(candidate?.collection || '').trim(),
    records_affected: Number(candidate?.records_affected),
    success: candidate?.success === true || candidate?.success === 'true'
  };
  if (!event.user_id || event.user_id.length > 80) throw new Error('El usuario debe tener entre 1 y 80 caracteres.');
  if (!['READ', 'INSERT', 'UPDATE', 'DELETE'].includes(event.operation)) throw new Error('Operación no válida.');
  if (!event.collection || event.collection.length > 80) throw new Error('La colección debe tener entre 1 y 80 caracteres.');
  if (!Number.isSafeInteger(event.records_affected) || event.records_affected < 0 || event.records_affected > 1000000) {
    throw new Error('records_affected debe ser un entero entre 0 y 1 000 000.');
  }
  if (candidate?.timestamp) {
    const timestamp = String(candidate.timestamp).trim();
    if (!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(timestamp) || Number.isNaN(Date.parse(timestamp))) {
      throw new Error('La fecha debe ser ISO 8601 con zona horaria, por ejemplo 2026-11-27T02:30:00-05:00.');
    }
    event.timestamp = timestamp;
  }
  return event;
}

function preset(kind) {
  const base = { user_id: 'vscode_demo', collection: 'pruebas_vscode', success: true };
  if (kind === 'normal') return {...base, operation:'READ', records_affected:3};
  if (kind === 'mass-update') return {...base, operation:'UPDATE', records_affected:550};
  if (kind === 'high-delete') return {...base, operation:'DELETE', records_affected:550};
  if (kind === 'critical-delete') return {...base, operation:'DELETE', records_affected:1500};
  if (kind === 'unusual-hour') {
    const nowPeru = new Date(Date.now() - 5 * 3600 * 1000);
    const localDay = nowPeru.toISOString().slice(0,10);
    return {...base, operation:'UPDATE', records_affected:25, timestamp:`${localDay}T02:30:00-05:00`};
  }
  throw new Error('Escenario no reconocido.');
}

function formatDetail(detail) {
  if (typeof detail === 'string') return detail.slice(0,250);
  if (Array.isArray(detail)) return 'Verifica los datos del evento.';
  return 'Error de la API.';
}

async function apiRequest(baseUrl, route, {method='GET', headers={}, body, timeout=16000, fetchImpl=globalThis.fetch}={}) {
  const base = normalizeBaseUrl(baseUrl);
  if (!/^\/[a-z0-9/?=&_.-]+$/i.test(route) || route.startsWith('//')) throw new Error('Ruta no permitida.');
  const endpoint = base + route;
  let response;
  try {
    response = await fetchImpl(endpoint, {
      method, headers: {Accept:'application/json', ...headers},
      body: body === undefined ? undefined : (typeof body === 'string' ? body : JSON.stringify(body)),
      signal: AbortSignal.timeout(timeout),
      redirect: 'error'
    });
  } catch (error) {
    if (error?.name === 'TimeoutError') throw new Error('La API no respondió a tiempo. Render Free puede estar iniciándose; vuelve a intentar.');
    throw new Error('No se pudo conectar con FastAPI. Revisa la URL y tu conexión.');
  }
  const raw = await response.text();
  let data;
  try { data = raw ? JSON.parse(raw) : {}; } catch { data = {}; }
  if (!response.ok) {
    const reason = response.status === 401
      ? 'Credenciales inválidas o sesión vencida. Vuelve a iniciar sesión o revisa la API Key.'
      : formatDetail(data?.detail);
    throw new Error(`HTTP ${response.status}: ${reason}`);
  }
  return data;
}

module.exports = { DEFAULT_URL, normalizeBaseUrl, validateEvent, preset, apiRequest };
