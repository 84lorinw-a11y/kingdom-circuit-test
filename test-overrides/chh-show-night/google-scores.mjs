import {act} from './state.mjs?v=scores-27';

// Apps Script accepts a simple text POST, avoiding unsupported CORS preflight.
// Tokens stay on this device; the sheet contains only their SHA-256 identifiers.
export function createGoogleScores(storage,{base,fetcher=fetch,timeoutMs=12000,schedule=setTimeout,cancel=clearTimeout}={}) {
 const prefix='kc-google-scores-v1:'+base;
 const read=(key,fallback)=>{try{return JSON.parse(storage.getItem(prefix+key))??fallback;}catch{return fallback;}};
 const write=(key,value)=>{try{storage.setItem(prefix+key,JSON.stringify(value));}catch{}};
 let profiles=read(':profiles',{}),pending=read(':pending',[]),rejected=read(':rejected',[]),latest=null,queue=Promise.resolve(),retryTimer=null;
 const enqueue=work=>(queue=queue.catch(()=>{}).then(work));
 const snapshot=()=>structuredClone(latest);
 function identity(state) {
  const key='name:'+state.name.trim().toLocaleLowerCase();
  if(!profiles[key]) {profiles[key]=crypto.randomUUID().replaceAll('-','')+crypto.randomUUID().replaceAll('-','');write(':profiles',profiles);}
  return profiles[key];
 }
 const journey=s=>({friends:s.friends,entered:s.entered,worship:s.worship,photo:s.photo,room:s.room});
 async function attemptRequest(path,body,token) {
  const control=new AbortController(),timer=schedule(()=>control.abort(),timeoutMs);
  try {
   const response=await fetcher(base,{method:'POST',redirect:'follow',credentials:'omit',headers:{'Content-Type':'text/plain;charset=UTF-8'},body:JSON.stringify({path,body,token,...(path==='/scores'?body:{})}),signal:control.signal});
   const value=await response.json();
   if(!response.ok||value.error){const error=Error(value.error||'Score service unavailable');error.status=value.status||response.status;throw error;}
   return value;
  } finally {cancel(timer);}
 }
 async function request(path,body,token) {
  for(let attempt=0;;attempt++) {
   try{return await attemptRequest(path,body,token);}
   catch(error){
    if(attempt>=2||![429,503].includes(error.status))throw error;
    // Sheets serializes writes. Brief contention should not interrupt a player.
    await new Promise(resolve=>schedule(resolve,600*(attempt+1)+Math.random()*400));
   }
  }
 }
 function retryLater() { if(retryTimer||!pending.length)return;retryTimer=schedule(()=>{retryTimer=null;enqueue(flush).catch(()=>{});},30000); }
 async function flush() {
  for(const entry of [...pending]) {
   try {await request('/finish',{sessionId:entry.sessionId,result:entry.result},entry.token);pending=pending.filter(item=>item.result.id!==entry.result.id);write(':pending',pending);}
   catch(error) {
    // A rejected/abandoned round must not trap every future replay behind it.
    if(error.status>=400&&error.status<500&&error.status!==429){
     rejected.push({...entry,error:error.message});write(':rejected',rejected);
     pending=pending.filter(item=>item.result.id!==entry.result.id);write(':pending',pending);
    } else retryLater();
    throw error;
   }
  }
 }
 function connectState(state) {return request('/session',{sessionId:state.sessionId,nickname:state.name,journey:journey(state)},identity(state));}
 const service={
  enabled:true,base,get pendingCount(){return pending.length;},get rejectedCount(){return rejected.length;},
  connect(state){latest=structuredClone(state);const current=snapshot();return enqueue(async()=>{await flush();return connectState(current);});},
  journey(action,value){if(!latest)return;latest=act(latest,action,value);const current=snapshot();enqueue(()=>connectState(current)).catch(()=>{});},
  start(game){if(!latest)return Promise.resolve(null);const current=snapshot(),roundId=crypto.randomUUID();return enqueue(async()=>{await flush();return request('/start',{sessionId:current.sessionId,nickname:current.name,journey:journey(current),game,roundId},identity(current));});},
  finish(result){if(!latest)return Promise.reject(Error('No active score session'));const current=snapshot();if(!pending.some(entry=>entry.result.id===result.id)){pending.push({sessionId:current.sessionId,token:identity(current),result:structuredClone(result)});write(':pending',pending);}return enqueue(flush);},
  board(offset=0){return enqueue(async()=>{try{await flush();}catch{}return request('/scores',{offset,limit:50});});},
  retry(){return enqueue(flush);},
  dispose(){if(retryTimer)cancel(retryTimer);retryTimer=null;}
 };
 return service;
}
