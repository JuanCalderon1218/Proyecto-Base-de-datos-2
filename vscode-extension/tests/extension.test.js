'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const Module=require('node:module');
const path=require('node:path');

function mockVSCode() {
  const commands=new Map();const views=[];const webviews=[];
  class Em{constructor(){this.listeners=[];this.event=(listener)=>{this.listeners.push(listener);return {dispose(){}};};}fire(){this.listeners.forEach(x=>x());}dispose(){}}
  class Item{constructor(label,collapsibleState){this.label=label;this.collapsibleState=collapsibleState;}}
  class Icon{constructor(id){this.id=id;}}
  const settings={apiUrl:'https://detector-anomalias-nosql.onrender.com',githubIssuesUrl:'https://github.com/JuanCalderon1218/Proyecto-Base-de-datos-2/issues'};
  const mock={
    EventEmitter:Em,TreeItem:Item,TreeItemCollapsibleState:{None:0,Expanded:2},ThemeIcon:Icon,
    StatusBarAlignment:{Right:1},ViewColumn:{One:1},ConfigurationTarget:{Global:1},
    Uri:{joinPath:(base,...parts)=>({fsPath:path.join(base.fsPath||String(base),...parts)}),parse:url=>({url})},
    workspace:{getConfiguration:()=>({get:(k,fallback)=>settings[k]??fallback,update:async(k,v)=>{settings[k]=v;}})},
    commands:{registerCommand:(name,fn)=>{commands.set(name,fn);return {dispose(){}};}},
    env:{openExternal:async()=>{}},
    window:{createOutputChannel:()=>({appendLine(){},dispose(){}}),createStatusBarItem:()=>({show(){},dispose(){}}),
      createTreeView:(name,opt)=>{views.push({name,opt});return {dispose(){}};},
      createWebviewPanel:()=>{
        const listeners=[];
        const webview={cspSource:'vscode-resource:',asWebviewUri:uri=>uri.fsPath,postMessage:async()=>true,
          onDidReceiveMessage:fn=>{listeners.push(fn);return {dispose(){}};}};
        const panel={webview,iconPath:null,onDidDispose:()=>({dispose(){}}),reveal(){},listeners};webviews.push(panel);return panel;
      },
      showWarningMessage:async()=>undefined,showInformationMessage:async()=>{},showErrorMessage:async()=>{},showInputBox:async()=>undefined}
  };
  return {mock,commands,views,webviews};
}

test('extension activates, registers native sidebar and renders webview',async()=>{
 const {mock,commands,views,webviews}=mockVSCode();
 const original=Module._load;Module._load=function(request,...args){if(request==='vscode')return mock;return original.call(this,request,...args);};
 try{
  delete require.cache[require.resolve('../src/view')];delete require.cache[require.resolve('../src/extension')];
  const extension=require('../src/extension');
  const secrets=new Map();
  const context={subscriptions:[],extensionUri:{fsPath:path.resolve(__dirname,'..')},
   secrets:{get:async key=>secrets.get(key),store:async(k,v)=>secrets.set(k,v),delete:async k=>secrets.delete(k)}};
  extension.activate(context);
  assert.ok(commands.has('nosqlMonitor.openPanel'));
  assert.ok(commands.has('nosqlMonitor.sendCritical'));
  assert.ok(commands.has('nosqlMonitor.login'));
  assert.equal(views[0].name,'nosqlMonitor.sidebar');
  await commands.get('nosqlMonitor.openPanel')();
  assert.equal(webviews.length,1);
  assert.match(webviews[0].webview.html,/NoSQL Anomaly Monitor/);
  assert.match(webviews[0].webview.html,/Content-Security-Policy/);
  assert.match(webviews[0].webview.html,/integraciones automáticas/i);
 } finally {Module._load=original;}
});
