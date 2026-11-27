'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {DEFAULT_URL,normalizeBaseUrl,validateEvent,preset,apiRequest}=require('../src/api');

test('Default API is the production Render base',()=>assert.equal(normalizeBaseUrl(DEFAULT_URL),'https://detector-anomalias-nosql.onrender.com'));
test('allow local HTTP for dev, not insecure remote',()=>{
 assert.equal(normalizeBaseUrl('http://127.0.0.1:8000/'),'http://127.0.0.1:8000');
 assert.throws(()=>normalizeBaseUrl('http://example.com'),/HTTPS/);
 assert.throws(()=>normalizeBaseUrl('https://api.example.com/events'),/URL base/);
 assert.throws(()=>normalizeBaseUrl('https://alice:secret@example.com'),/credenciales/);
});
test('validates events and rejects out-of-range inputs',()=>{
 assert.deepEqual(validateEvent(preset('normal')),{user_id:'vscode_demo',operation:'READ',collection:'pruebas_vscode',records_affected:3,success:true});
 assert.throws(()=>validateEvent({...preset('normal'),records_affected:-1}),/records_affected/);
 assert.throws(()=>validateEvent({...preset('normal'),operation:'DROP'}),/Operación/);
});
test('all five presets are correctly defined',()=>{
 assert.equal(preset('mass-update').records_affected,550);
 assert.equal(preset('high-delete').operation,'DELETE');
 assert.equal(preset('critical-delete').records_affected,1500);
 assert.match(preset('unusual-hour').timestamp,/T02:30:00-05:00$/);
 assert.throws(()=>preset('unknown'));
});
test('API request uses proper route, headers and payload without redirects',async()=>{
 const mock=async(url,opts)=>{
  assert.equal(url,'https://detector-anomalias-nosql.onrender.com/events');
  assert.equal(opts.method,'POST'); assert.equal(opts.headers['X-API-Key'],'test-key');
  assert.equal(opts.redirect,'error');
  assert.equal(JSON.parse(opts.body).records_affected,1500);
  return {ok:true,text:async()=>JSON.stringify({event_id:'EVT-12345678',analysis:{score:75,severity:'critical'}})};
 };
 const result=await apiRequest(DEFAULT_URL,'/events',{method:'POST',headers:{'X-API-Key':'test-key'},body:preset('critical-delete'),fetchImpl:mock});
 assert.equal(result.analysis.score,75);
});
test('API errors report 401 without leaking token',async()=>{
 const mock=async()=>({ok:false,status:401,text:async()=>JSON.stringify({detail:'invalid key'})});
 await assert.rejects(apiRequest(DEFAULT_URL,'/events',{fetchImpl:mock}),/Credenciales inválidas/);
});
test('invalid route blocked',async()=>{await assert.rejects(apiRequest(DEFAULT_URL,'//attacker.com'),/Ruta no permitida/);});
