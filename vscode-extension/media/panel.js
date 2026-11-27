'use strict';
(function () {
  const vscode = acquireVsCodeApi();
  const $ = id => document.getElementById(id);
  const send = (action, extra = {}) => vscode.postMessage({action, ...extra});
  const notice = (text, kind='') => { $('notice').textContent = String(text); $('notice').className='notice '+kind; };
  const setText = (id, text) => { $(id).textContent = text == null ? '—' : String(text); };
  const td = (tr, value, styleClass) => {
    const cell=document.createElement('td'); cell.textContent=String(value == null ? '—' : value);
    if (styleClass) cell.className=styleClass;
    tr.appendChild(cell); return cell;
  };
  const empty = (id, text, columns) => { const tbody=$(id); tbody.replaceChildren(); const tr=document.createElement('tr'); const cell=td(tr,text); cell.colSpan=columns; tbody.appendChild(tr); };
  function renderAlerts(rows) {
    const b=$('alertsBody'); b.replaceChildren();
    if (!rows?.length) { empty('alertsBody','No hay alertas para mostrar.',6); return; }
    for(const a of rows.slice(0,25)) {
      const tr=document.createElement('tr'); tr.className='clickable';
      td(tr,a.alert_id); td(tr,a.user_id); td(tr,(a.types||[]).join(' + ')||a.signature||a.operation); td(tr,a.score);
      td(tr,(a.severity||'').toUpperCase(),'sev '+String(a.severity||'').toLowerCase()); td(tr,a.status);
      tr.addEventListener('click',()=>send('alertDetails',{id:a.alert_id})); b.appendChild(tr);
    }
  }
  function renderEvents(rows) {
    const b=$('eventsBody');b.replaceChildren();
    if(!rows?.length){empty('eventsBody','No hay eventos para mostrar.',6);return;}
    for(const e of rows.slice(0,25)) {
      const tr=document.createElement('tr');td(tr,e.event_id);td(tr,e.operation);td(tr,e.records_affected);td(tr,e.user_id);td(tr,e.anomaly_score);
      td(tr,e.is_anomalous?'Anómalo':'Normal',e.is_anomalous?'sev high':'');b.appendChild(tr);
    }
  }
  function renderHistory(rows) {
    const list=$('historyList');list.replaceChildren();
    if(!rows?.length){const li=document.createElement('li');li.textContent='No hay registros de integración.';list.appendChild(li);return;}
    for(const row of rows.slice(0,10)) {
      const li=document.createElement('li');li.textContent=`${String(row.provider||'integración').toUpperCase()} · ${row.status||'registrado'}`;
      const sm=document.createElement('small');sm.textContent=`${row.alert_id||'—'} · ${row.created_at?new Date(row.created_at).toLocaleString('es-PE'):'—'}`;
      li.appendChild(sm);list.appendChild(li);
    }
  }
  const commands = {refresh:'refresh',health:'health',configure:'configure',key:'key',login:'login',logout:'logout',issues:'issues',dashboard:'dashboard'};
  for (const [id,action] of Object.entries(commands)) $(id).addEventListener('click',()=>send(action));
  for(const b of document.querySelectorAll('[data-preset]')) b.addEventListener('click',()=>send('preset',{kind:b.dataset.preset}));
  $('eventForm').addEventListener('submit',ev=>{
    ev.preventDefault();const fd=new FormData(ev.target);const event={};for(const [k,v] of fd.entries()) event[k]=v;
    if(!event.timestamp) delete event.timestamp; send('event',{event});
  });
  window.addEventListener('message',ev=>{
    const msg=ev.data||{};
    if(msg.type==='status') notice(msg.message,msg.kind||'');
    if(msg.type==='config') setText('apiUrl',msg.url);
    if(msg.type==='data'){
      setText('evTotal',msg.summary?.events?.total);setText('evAnom',msg.summary?.events?.anomalous);
      setText('alTotal',msg.summary?.alerts?.total);setText('alCritical',msg.summary?.alerts?.critical);
      renderAlerts(msg.alerts);renderEvents(msg.events);renderHistory(msg.history);
      notice('Datos actualizados desde FastAPI. Sesión autenticada.','success');
    }
    if(msg.type==='result'){
      const e=msg.event||{}; const a=e.analysis||{};
      const detections=(a.detections||[]).map(d=>d.type+' ('+d.score+' puntos)').join(', ')||'Ninguna';
      const integrations=Object.entries(a.integrations||{}).map(([k,v])=>k+': '+(v.status||'—')).join(', ')||'Sin integraciones nuevas';
      $('lastResult').hidden=false;
      $('resultText').textContent=`Evento: ${e.event_id||'—'}\nOperación: ${e.operation||'—'}\nAnómalo: ${a.is_anomalous?'SÍ':'NO'}\nScore: ${a.score??0}/100\nSeveridad: ${String(a.severity||'NORMAL').toUpperCase()}\nDetecciones: ${detections}\nAlerta: ${a.alert_id||'—'}\nAgrupada: ${a.alert_merged?'Sí':'No'}\nIntegraciones: ${integrations}`;
      notice('Evento enviado y analizado correctamente.','success');
    }
    if(msg.type==='alertDetails'){$('alertDetails').hidden=false;$('alertDetails').textContent=msg.details||'Sin detalle disponible.';}
  });
  send('init');
}());
