// The same twenty opportunities and 40 + 10 rule apply to every game.
export const ROUND_MAX=1000, OPPORTUNITIES=20;
export const gameIds=['eli','joz','steven','chamblissnation'];
export const gameNames={eli:'Eli',joz:'Joz',steven:'Steven',chamblissnation:'Chamblissnation'};
export const roundSeconds={eli:26,joz:21,steven:21,chamblissnation:25};
export function roundSchedule(id,seed=1){
 let n=seed>>>0;const random=()=>{n=(Math.imul(1664525,n)+1013904223)>>>0;return n/4294967296;};
 const first=id==='eli'?2.58:2.3,step=id==='eli'?120/104:(roundSeconds[id]-first-1.4)/19;
 return Array.from({length:20},(_,i)=>({id:i,at:first+i*step,lane:Math.floor(random()*4),x:65+random()*290,kind:i%3}));
}
export function roundScore(events){
 const seen=new Set();let total=0,hits=0,perfect=0,streak=0,bestCombo=0;
 for(const e of events||[]){if(!Number.isInteger(e.id)||e.id<0||e.id>=20||seen.has(e.id))continue;seen.add(e.id);
  if(e.hit===true){hits++;streak++;total+=40;if(e.perfect===true){total+=10;perfect++;}bestCombo=Math.max(bestCombo,streak);}else streak=0;
 }
 return {total,hits,perfect,bestCombo};
}
export function validateRound(result){return gameIds.includes(result?.game)&&typeof result.id==='string'&&result.id.length<100&&Array.isArray(result.events)&&result.events.length===20&&new Set(result.events.map(e=>e.id)).size===20&&result.events.every(e=>Number.isInteger(e.id)&&e.id>=0&&e.id<20&&typeof e.hit==='boolean'&&typeof e.perfect==='boolean'&&(!e.perfect||e.hit));}
export const blankTotals=()=>Object.fromEntries(gameIds.map(id=>[id,0]));
