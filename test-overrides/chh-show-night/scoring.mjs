// The same twenty opportunities and 40 + 10 rule apply to every game.
export const ROUND_MAX=1000, OPPORTUNITIES=20;
export const gameIds=['eli','marty','brenno','ryan-ellis','gavin-the-hotrod','lj-the-messenger','dearis','tonyxtrotter','andrew-prim','apollo'];
export const gameNames={eli:'Eli',marty:'Marty',brenno:'Brenno','ryan-ellis':'Ryan Ellis','gavin-the-hotrod':'Gavin','lj-the-messenger':'LJ',dearis:'De’aris',tonyxtrotter:'tonyxtrotter','andrew-prim':'Andrew Prim',apollo:'Apollo merch'};
export const roundSeconds={eli:26,marty:21,brenno:21,apollo:25,'ryan-ellis':28,'gavin-the-hotrod':28,'lj-the-messenger':28,dearis:28,tonyxtrotter:28,'andrew-prim':30};
export function roundSchedule(id,seed=1){
 let n=seed>>>0;const random=()=>{n=(Math.imul(1664525,n)+1013904223)>>>0;return n/4294967296;};
 const first=id==='eli'?2.58:2.3,step=id==='eli'?120/104:(roundSeconds[id]-first-1.4)/19;
 return Array.from({length:20},(_,i)=>{
  const lane=Math.floor(random()*4),position=random();
  return {id:i,at:id==='andrew-prim'?3+Math.floor(i/4)*5.3+(i%4)*.8:first+i*step,lane,x:id==='apollo'?(i%2?265:65)+position*90:65+position*290,kind:i%3};
 });
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
