import {score,journeyScore} from './state.mjs?v=rebuild-11';
import {gameIds} from './scoring.mjs?v=rebuild-11';
// Empty on the static test site until an online score service is connected.
export const SCORE_SERVICE='';
export function bestSession(previous,candidate){return !previous||candidate.total>previous.total?candidate:previous;}
export function createScoreStore(storage=localStorage){
 const key='kc-show-night-scores-v2';let data;try{data=JSON.parse(storage.getItem(key))||{};}catch{data={};}
 data.playerId??=crypto.randomUUID();data.best??=null;
 function save(){try{storage.setItem(key,JSON.stringify(data));}catch{}}
 return {get playerId(){return data.playerId;},get best(){return data.best;},
 record(s){const row={playerId:data.playerId,sessionId:s.sessionId,nickname:s.name,total:score(s),journey:journeyScore(s),...Object.fromEntries(gameIds.map(id=>[id,s.totals[id]])),rounds:s.rounds};data.best=bestSession(data.best,row);save();return row;},
 async board(){if(!SCORE_SERVICE)return {mode:'device',rows:data.best?[data.best]:[]};const r=await fetch(`${SCORE_SERVICE}/scores`);if(!r.ok)throw Error('Scoreboard unavailable');return {mode:'online',rows:await r.json()};}
 };
}

export function createOnlineScores(storage=localStorage){
 const base=typeof document!=='undefined'?document.querySelector('meta[name="score-service"]')?.content:'';
 let token='';try{token=storage.getItem('kc-score-token')||'';}catch{}
 let session='',queue=Promise.resolve();
 async function request(path,body){const r=await fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},body:JSON.stringify(body)});const json=await r.json();if(!r.ok)throw Error(json.error||'Score service unavailable');return json;}
 return {enabled:!!base,get base(){return base;},
 connect(s){if(!base||!s.name)return Promise.resolve();queue=queue.catch(()=>{}).then(async()=>{const r=await request('/session',{sessionId:s.sessionId,nickname:s.name});token=r.token;session=s.sessionId;try{storage.setItem('kc-score-token',token);}catch{}});return queue;},
 journey(action,value){if(!base)return;queue=queue.then(()=>request('/journey',{sessionId:session,action,value}));queue.catch(()=>{});},
 async start(game){if(!base)return null;queue=queue.then(()=>request('/start',{sessionId:session,game}));return queue;},
 async finish(result){if(!base)return;queue=queue.then(()=>request('/finish',{sessionId:session,result}));return queue;},
 async board(){const r=await fetch(base+'/scores');if(!r.ok)throw Error('Board unavailable');return {mode:'online',rows:await r.json()};}
 };
}
