'use strict';
const vscode = require('vscode');

function htmlForWebview(webview, extensionUri) {
  const js = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'media', 'panel.js'));
  const css = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'media', 'panel.css'));
  const csp = `default-src 'none'; style-src ${webview.cspSource}; script-src ${webview.cspSource};`;
  return `<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<meta http-equiv="Content-Security-Policy" content="${csp}"/>
<title>NoSQL Anomaly Monitor</title><link rel="stylesheet" href="${css}"/></head>
<body>
<header class="head">
 <div><div class="eyebrow">INTEGRACIÓN NATIVA · VS CODE</div><h1>◈ NoSQL Anomaly Monitor</h1><p>Detector de Anomalías NoSQL · FastAPI + MongoDB Atlas</p></div>
 <div class="buttons"><button id="refresh">↻ Actualizar</button><button id="health">Comprobar API</button></div>
</header>
<div id="notice" class="notice">Inicia sesión para consultar el dashboard y guarda tu API Key para enviar eventos de prueba.</div>
<section class="toolbar">
 <span class="label">API</span><code id="apiUrl">—</code>
 <button id="configure">Configurar URL</button><button id="key">API Key</button><button id="login">Iniciar sesión</button><button id="logout">Cerrar sesión</button>
</section>
<section class="stats">
 <div class="stat"><small>Eventos registrados</small><strong id="evTotal">—</strong></div>
 <div class="stat"><small>Eventos anómalos</small><strong id="evAnom">—</strong></div>
 <div class="stat"><small>Alertas totales</small><strong id="alTotal">—</strong></div>
 <div class="stat"><small>Críticas</small><strong id="alCritical">—</strong></div>
</section>
<div class="layout">
 <main>
  <section class="panel"><div class="section-head"><h2>Enviar evento de prueba</h2><span class="pill">Simulado: no modifica documentos reales</span></div>
   <div class="presets"><button data-preset="normal">Normal</button><button data-preset="mass-update">UPDATE 550</button><button data-preset="high-delete">DELETE 550</button><button data-preset="critical-delete" class="warn">DELETE 1500 · CRITICAL</button><button data-preset="unusual-hour">Horario inusual</button></div>
   <form id="eventForm">
    <div class="fields">
      <label>Usuario<input name="user_id" value="vscode_demo" required maxlength="80"/></label>
      <label>Colección<input name="collection" value="pruebas_vscode" required maxlength="80"/></label>
      <label>Operación<select name="operation"><option>READ</option><option>INSERT</option><option>UPDATE</option><option>DELETE</option></select></label>
      <label>Registros afectados<input name="records_affected" type="number" value="3" min="0" max="1000000" required/></label>
      <label>Resultado<select name="success"><option value="true">Exitoso</option><option value="false">Fallido</option></select></label>
      <label>Timestamp ISO (opcional)<input name="timestamp" placeholder="2026-11-27T02:30:00-05:00" /></label>
    </div><div class="actions"><button type="submit" class="primary">Enviar evento personalizado →</button></div>
   </form>
   <div id="lastResult" class="result" hidden><h3>Respuesta de FastAPI</h3><pre id="resultText"></pre></div>
  </section>
  <section class="panel"><div class="section-head"><h2>Últimas alertas</h2><span>Selecciona para ver los detalles</span></div><div class="table-scroll"><table><thead><tr><th>Alerta</th><th>Usuario</th><th>Regla</th><th>Score</th><th>Severidad</th><th>Estado</th></tr></thead><tbody id="alertsBody"><tr><td colspan="6">Inicia sesión para consultar alertas.</td></tr></tbody></table></div><div id="alertDetails" class="details" hidden></div></section>
  <section class="panel"><div class="section-head"><h2>Últimos eventos</h2><span>Registrados por la API</span></div><div class="table-scroll"><table><thead><tr><th>Evento</th><th>Operación</th><th>Registros</th><th>Usuario</th><th>Score</th><th>Estado</th></tr></thead><tbody id="eventsBody"><tr><td colspan="6">Inicia sesión para consultar eventos.</td></tr></tbody></table></div></section>
 </main>
 <aside>
  <section class="panel"><h2>Integraciones automáticas</h2><div class="integration"><span class="dot green"></span><div><b>Discord</b><p>Notifica cuando se crea una alerta.</p></div></div><div class="integration"><span class="dot violet"></span><div><b>GitHub Issues</b><p>Registra incidencias HIGH y CRITICAL.</p></div></div><div class="buttons-col"><button id="issues">Abrir GitHub Issues ↗</button><button id="dashboard">Abrir dashboard web ↗</button></div></section>
  <section class="panel"><h2>Historial de integraciones</h2><ul class="history" id="historyList"><li>Inicia sesión para consultar el historial.</li></ul></section>
  <section class="panel"><h2>¿Qué demuestra?</h2><p>VS Code se conecta a la API real de tu proyecto. Un evento simulado se evalúa con el motor existente, recibe Score y puede activar Discord y GitHub sin cambiar datos de MongoDB.</p><p class="muted">La lectura de alertas requiere JWT. El envío de eventos utiliza X-API-Key.</p></section>
 </aside>
</div>
<footer>NoSQL Anomaly Monitor · Extensión académica · Calderon / Mango · 2026</footer>
<script src="${js}"></script></body></html>`;
}
module.exports = { htmlForWebview };
