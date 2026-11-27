'use strict';

const vscode = require('vscode');
const {DEFAULT_URL, normalizeBaseUrl, validateEvent, preset, apiRequest} = require('./api');
const {htmlForWebview} = require('./view');

const API_SECRET='nosqlMonitor.eventApiKey';
const JWT_SECRET='nosqlMonitor.jwtToken';
const ISSUES='https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/issues';

function activate(context) {
  let panel;
  let lastAlerts=[];
  let lastSummary;
  const emitter=new vscode.EventEmitter();
  const log=vscode.window.createOutputChannel('NoSQL Anomaly Monitor');
  const status=vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right,70);
  status.text='$(shield) NoSQL Monitor';status.tooltip='Abrir Detector de Anomalías NoSQL';
  status.command='nosqlMonitor.openPanel';status.show();
  context.subscriptions.push(emitter,log,status);

  const getUrl=()=>normalizeBaseUrl(vscode.workspace.getConfiguration('nosqlMonitor').get('apiUrl',DEFAULT_URL));
  const notify=(message,kind='')=>{
    if(panel) void panel.webview.postMessage({type:'status',message,kind});
    if(kind==='error') vscode.window.showErrorMessage(message);
  };
  const api=(route,options)=>apiRequest(getUrl(),route,options);
  async function bearer() {
    const token=await context.secrets.get(JWT_SECRET);
    if(!token) throw new Error('Inicia sesión JWT para consultar alertas y eventos.');
    return { Authorization:`Bearer ${token}` };
  }
  async function openWeb(url) {
    const parsed=new URL(url);
    if(parsed.protocol!=='https:') throw new Error('El enlace externo debe usar HTTPS.');
    await vscode.env.openExternal(vscode.Uri.parse(parsed.href));
  }
  function broadcastConfig(){if(panel)void panel.webview.postMessage({type:'config',url:getUrl()});}

  async function checkHealth() {
    const result=await api('/health',{timeout:30000});
    if(result.status!=='ok') throw new Error('La API respondió, pero el estado no es OK.');
    notify('API activa y conectada: '+getUrl(),'success');
    return result;
  }

  async function saveApiUrl() {
    const existing=vscode.workspace.getConfiguration('nosqlMonitor').get('apiUrl',DEFAULT_URL);
    const answer=await vscode.window.showInputBox({prompt:'URL base de FastAPI (sin /docs ni /events)',value:existing,ignoreFocusOut:true,
      validateInput:v=>{try{normalizeBaseUrl(v);return null;}catch(e){return e.message;}}});
    if(answer===undefined)return;
    const url=normalizeBaseUrl(answer);
    await vscode.workspace.getConfiguration('nosqlMonitor').update('apiUrl',url,vscode.ConfigurationTarget.Global);
    await context.secrets.delete(JWT_SECRET);
    notify('URL actualizada. Por seguridad, vuelve a iniciar sesión.','success');
    broadcastConfig();
    return url;
  }
  async function saveApiKey() {
    const answer=await vscode.window.showInputBox({prompt:'EVENT_API_KEY de Render o de tu entorno local',password:true,ignoreFocusOut:true,placeHolder:'La clave no se mostrará ni guardará en archivos'});
    if(answer===undefined)return;
    const key=answer.trim();
    if(key.length<8) throw new Error('La API Key parece demasiado corta; revisa el valor.');
    await context.secrets.store(API_SECRET,key);
    notify('API Key guardada de forma segura en VS Code.','success');
  }
  async function login() {
    const username=await vscode.window.showInputBox({prompt:'Usuario de la aplicación (admin / analyst)',ignoreFocusOut:true});
    if(username===undefined)return;
    if(!username.trim()) throw new Error('Indica el usuario.');
    const password=await vscode.window.showInputBox({prompt:'Contraseña del dashboard',password:true,ignoreFocusOut:true});
    if(password===undefined)return;
    const data=await api('/auth/login',{
      method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body:new URLSearchParams({username:username.trim(),password}).toString(),timeout:30000
    });
    if(!data.access_token)throw new Error('El servidor no devolvió un token JWT.');
    await context.secrets.store(JWT_SECRET,data.access_token);
    notify('Sesión JWT iniciada para '+username.trim()+'.','success');
    await refresh();
  }
  async function logout() {
    const token=await context.secrets.get(JWT_SECRET);
    if(token){try{await api('/auth/logout',{method:'POST',headers:{Authorization:`Bearer ${token}`},timeout:8000});}catch{log.appendLine('Logout local; la sesión remota podría haber expirado.');}}
    await context.secrets.delete(JWT_SECRET);
    lastAlerts=[];lastSummary=undefined;emitter.fire();
    if(panel)void panel.webview.postMessage({type:'data',summary:null,alerts:[],events:[],history:[]});
    notify('Sesión cerrada. La API Key de eventos permanece guardada.','success');
  }
  async function refresh() {
    broadcastConfig();
    const headers=await bearer();
    const results=await Promise.allSettled([
      api('/dashboard/summary',{headers,timeout:30000}),
      api('/alerts?limit=25',{headers,timeout:30000}),
      api('/events?limit=25',{headers,timeout:30000}),
      api('/integrations/history',{headers,timeout:30000})
    ]);
    if(results.slice(0,3).every(r=>r.status==='rejected')) throw results[0].reason;
    const val=i=>results[i].status==='fulfilled'?results[i].value:undefined;
    const errors=results.map((r,i)=>r.status==='rejected'?`Consulta ${i+1}: ${r.reason.message}`:null).filter(Boolean);
    lastSummary=val(0);lastAlerts=Array.isArray(val(1))?val(1):[];
    const events=Array.isArray(val(2))?val(2):[];
    const history=Array.isArray(val(3))?val(3):[];
    emitter.fire();
    if(panel)void panel.webview.postMessage({type:'data',summary:lastSummary,alerts:lastAlerts,events,history});
    if(errors.length)notify('Actualización parcial. '+errors.join(' | '),'error');
    else notify('Alertas y eventos actualizados correctamente.','success');
  }
  async function sendEvent(candidate) {
    const key=await context.secrets.get(API_SECRET);
    if(!key)throw new Error('Primero configura la API Key con el botón «API Key».');
    const event=validateEvent(candidate);
    const potentiallyHigh=(event.operation==='DELETE'&&event.records_affected>=200)||(event.operation==='UPDATE'&&event.records_affected>=500);
    const warning=potentiallyHigh
      ? 'Este evento de PRUEBA puede crear una alerta y activar Discord y GitHub Issues. NO modifica documentos reales en MongoDB. ¿Enviar?'
      : 'Se enviará un evento sintético al Detector NoSQL. No modifica documentos reales. ¿Continuar?';
    const confirmed=await vscode.window.showWarningMessage(warning,{modal:potentiallyHigh},'Enviar evento');
    if(confirmed!=='Enviar evento')return;
    const saved=await api('/events',{method:'POST',headers:{'X-API-Key':key,'Content-Type':'application/json'},body:event,timeout:45000});
    if(panel)void panel.webview.postMessage({type:'result',event:saved});
    const analysis=saved.analysis||{};
    vscode.window.showInformationMessage(`NoSQL: ${saved.event_id||'evento'} · ${analysis.score??0} puntos · ${(analysis.severity||'normal').toUpperCase()}`);
    if(await context.secrets.get(JWT_SECRET)){
      try{await refresh();}catch(e){log.appendLine('No se pudo refrescar tras envío: '+e.message);}
    }
    return saved;
  }
  async function showAlert(alertId) {
    if(typeof alertId!=='string'||!/^ALT-[A-Z0-9]{8}$/.test(alertId))throw new Error('Identificador de alerta no válido.');
    const headers=await bearer();
    const row=await api(`/alerts/${alertId}`,{headers});
    const clean={alert_id:row.alert_id,user_id:row.user_id,operation:row.operation,collection:row.collection,
      records_affected:row.records_affected,score:row.score,severity:row.severity,status:row.status,
      occurrence_count:row.occurrence_count,detections:row.detections,reasons:row.reasons};
    const details=JSON.stringify(clean,null,2);
    if(!panel) await openPanel();
    void panel.webview.postMessage({type:'alertDetails',details});
  }
  async function openPanel() {
    if(panel){panel.reveal();return;}
    panel=vscode.window.createWebviewPanel('nosqlMonitor','NoSQL Anomaly Monitor',vscode.ViewColumn.One,
      {enableScripts:true,retainContextWhenHidden:true,localResourceRoots:[vscode.Uri.joinPath(context.extensionUri,'media')]});
    panel.iconPath=vscode.Uri.joinPath(context.extensionUri,'resources','icon.svg');
    panel.webview.html=htmlForWebview(panel.webview,context.extensionUri);
    panel.onDidDispose(()=>{panel=undefined;},null,context.subscriptions);
    panel.webview.onDidReceiveMessage(async msg=>{
      if(!msg||typeof msg!=='object')return;
      try{
        switch(msg.action){
          case 'init':broadcastConfig();if(await context.secrets.get(JWT_SECRET))await refresh();break;
          case 'refresh':await refresh();break;
          case 'health':await checkHealth();break;
          case 'configure':await saveApiUrl();break;
          case 'key':await saveApiKey();break;
          case 'login':await login();break;
          case 'logout':await logout();break;
          case 'event':await sendEvent(msg.event);break;
          case 'preset':await sendEvent(preset(msg.kind));break;
          case 'issues':await openWeb(vscode.workspace.getConfiguration('nosqlMonitor').get('githubIssuesUrl',ISSUES));break;
          case 'dashboard':await openWeb(getUrl()+'/dashboard');break;
          case 'alertDetails':await showAlert(msg.id);break;
        }
      }catch(e){notify(e.message||'Ocurrió un error.','error');log.appendLine(String(e.message||e));}
    },null,context.subscriptions);
    broadcastConfig();
  }
  function cmd(id,handler){context.subscriptions.push(vscode.commands.registerCommand('nosqlMonitor.'+id,async(...args)=>{
    try{return await handler(...args);}catch(e){notify(e.message||String(e),'error');}
  }));}
  cmd('openPanel',openPanel);
  cmd('refresh',refresh);
  cmd('checkHealth',checkHealth);
  cmd('setApiUrl',saveApiUrl);
  cmd('setApiKey',saveApiKey);
  cmd('login',login);
  cmd('logout',logout);
  cmd('sendNormal',()=>sendEvent(preset('normal')));
  cmd('sendCritical',()=>sendEvent(preset('critical-delete')));
  cmd('openIssues',()=>openWeb(vscode.workspace.getConfiguration('nosqlMonitor').get('githubIssuesUrl',ISSUES)));
  cmd('openDashboard',()=>openWeb(getUrl()+'/dashboard'));
  cmd('openAlert',showAlert);

  function item(label,command,icon,description){
    const t=new vscode.TreeItem(label,vscode.TreeItemCollapsibleState.None);
    t.command={command:'nosqlMonitor.'+command,title:label};t.iconPath=new vscode.ThemeIcon(icon);
    if(description)t.description=description;
    return t;
  }
  const treeProvider={onDidChangeTreeData:emitter.event,
    getTreeItem:x=>x,
    getChildren:node=>{
      if(node?.section==='alerts')return lastAlerts.slice(0,10).map(a=>{
        const t=item(a.alert_id,'openAlert','warning',`${String(a.severity||'').toUpperCase()} · ${a.score||0} pts`);
        t.command.arguments=[a.alert_id];t.tooltip=`${a.user_id} | ${(a.types||[]).join(' + ')}`;return t;
      });
      if(node)return[];
      const items=[item('Abrir panel completo','openPanel','dashboard'),item('Actualizar alertas','refresh','refresh'),
        item('Comprobar conexión','checkHealth','plug'),item('Iniciar sesión','login','account'),
        item('Guardar API Key','setApiKey','key'),item('Configurar URL','setApiUrl','gear'),
        item('Enviar evento normal','sendNormal','play'),item('Enviar prueba CRITICAL','sendCritical','warning'),
        item('Abrir GitHub Issues','openIssues','github')];
      if(lastAlerts.length){const section=new vscode.TreeItem(`Alertas recientes (${lastAlerts.length})`,vscode.TreeItemCollapsibleState.Expanded);section.section='alerts';section.iconPath=new vscode.ThemeIcon('shield');items.push(section);}
      return items;
    }
  };
  context.subscriptions.push(vscode.window.createTreeView('nosqlMonitor.sidebar',{treeDataProvider:treeProvider}));
}

function deactivate() {}
module.exports={activate,deactivate};
