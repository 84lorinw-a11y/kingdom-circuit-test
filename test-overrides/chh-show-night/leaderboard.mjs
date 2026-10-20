import {score,journeyScore,act} from './state.mjs?v=apollo-06';
import {gameIds} from './scoring.mjs?v=apollo-06';
const nameKey=name=>'name:'+String(name||'').trim().toLocaleLowerCase();
export function bestSession(previous,candidate){return !previous||candidate.total>previous.total?candidate:previous;}
export async function confirmSessionSave(state,online,{localSaved=true}={}){
 const total=score(state);
 if(!online.enabled)return {status:localSaved?'device':'unsaved',total,localSaved};
 try{
  const response=await online.connect(state);
  if(!response?.state)throw Error('Save was not confirmed');
  const saved=score(response.state);
  return {status:saved===total&&!online.pendingCount?'online':'partial',saved,total,localSaved};
 }catch{return {status:localSaved?'waiting':'unsaved',total,localSaved};}
}
export function createScoreStore(storage=localStorage){
 const key='kc-apollo-night-scores-v2';let data;try{data=JSON.parse(storage.getItem(key))||{};}catch{data={};}
 data.playerId??=crypto.randomUUID();data.best??=null;data.players??={};
 if(data.best?.nickname)data.players[nameKey(data.best.nickname)]=bestSession(data.players[nameKey(data.best.nickname)],data.best);
 function save(){try{storage.setItem(key,JSON.stringify(data));}catch{}}
 return {get playerId(){return data.playerId;},get best(){return data.best;},
 record(s){const row={playerId:data.playerId,sessionId:s.sessionId,nickname:s.name,total:score(s),journey:journeyScore(s),...Object.fromEntries(gameIds.map(id=>[id,s.totals[id]])),rounds:s.rounds};if(!s.profileReady||!s.name)return row;data.best=bestSession(data.best,row);data.players[nameKey(s.name)]=bestSession(data.players[nameKey(s.name)],row);save();return row;},
 async board(){const rows=Object.values(data.players).sort((a,b)=>b.total-a.total||a.nickname.localeCompare(b.nickname)).map((r,i)=>({...r,rank:i+1}));return {mode:'device',rows,totalPlayers:rows.length,nextOffset:null};}
 };
}

// Hosting supplies the API URL; an empty value is explicitly device-only.
export function createOnlineScores(storage=localStorage,{base=typeof document!=='undefined'?document.querySelector('meta[name="score-service"]')?.content||'':'',fetcher=fetch,timeoutMs=8000}={}){
 if(/script\.google(?:usercontent)?\.com/.test(base))throw Error('The Apollo campaign cannot use the original competition service');
 let tokens={},legacy='';try{tokens=JSON.parse(storage.getItem('kc-apollo-score-profiles')||'{}');legacy=storage.getItem('kc-apollo-score-token')||'';}catch{}
 let token='',session='',latest=null,queue=Promise.resolve();
 const enqueue=work=>(queue=queue.catch(()=>{}).then(work));
 async function request(path,body){const control=new AbortController(),timer=setTimeout(()=>control.abort(),timeoutMs);try{const r=await fetcher(base+path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},...(body===undefined?{}:{body:JSON.stringify(body)}),signal:control.signal});const json=await r.json();if(!r.ok)throw Error(json.error||'Score service unavailable');return json;}finally{clearTimeout(timer);}}
 async function openSession(s){
  const key=nameKey(s.name);token=(s.sessionId===session&&token)||tokens[key]||(!Object.keys(tokens).length?legacy:'');
  const r=await request('/session',{sessionId:s.sessionId,nickname:s.name});token=r.token;session=s.sessionId;tokens[key]=token;legacy='';
  try{storage.setItem('kc-apollo-score-profiles',JSON.stringify(tokens));storage.setItem('kc-apollo-score-token',token);}catch{}
  // Restore only journey state. Old browser-only game scores are not imported.
  let remote=r.state;
  async function send(action,value){await request('/journey',{sessionId:session,action,value});remote=act(remote,action,value);}
  const missing=s.friends.filter(friend=>!remote.friends.includes(friend));
  if(missing.length&&remote.room!=='outside')await send('outside');
  for(const friend of missing)await send('invite',friend);
  if(s.entered&&!remote.entered)await send('enter');
  if(s.worship&&!remote.worship){if(remote.room!=='show')await send('show');await send('worship');}
  if(s.photo&&!remote.photo){if(remote.room!=='show')await send('show');await send('vip');await send('photo');}
  if(s.room==='outside'&&remote.room!=='outside')await send('outside');
  if(s.room==='show'&&remote.room!=='show')await send('show');
  if(s.room==='vip'&&remote.room!=='vip'){if(remote.room!=='show')await send('show');await send('vip');}
  return {state:remote};
 }
 return {enabled:!!base,get base(){return base;},
 connect(s){latest=structuredClone(s);if(!base||!s.name)return Promise.resolve();const snapshot=structuredClone(s);return enqueue(()=>openSession(snapshot));},
 journey(action,value){if(!base||!latest)return;latest=act(latest,action,value);const snapshot=structuredClone(latest);enqueue(()=>openSession(snapshot)).catch(()=>{});},
 async start(game){if(!base)return null;const snapshot=structuredClone(latest);return enqueue(async()=>{await openSession(snapshot);return request('/start',{sessionId:session,game});});},
 async finish(result){if(!base)return;const id=session;return enqueue(()=>request('/finish',{sessionId:id,result}));},
 async board(offset=0){await queue.catch(()=>{});return request(`/scores?offset=${offset}&limit=50`);}
 };
}
