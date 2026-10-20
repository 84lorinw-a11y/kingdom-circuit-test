import {merchItems} from './merch-items.mjs?v=apollo-13';
// The same twenty opportunities and 40 + 10 rule apply to every game.
export const ROUND_MAX=1000, OPPORTUNITIES=20;
export const gameIds=['eli','marty','brenno','ryan-ellis','gavin-the-hotrod','lj-the-messenger','dearis','tonyxtrotter','andrew-prim','apollo'];
export const gameNames={eli:'Eli',marty:'Marty',brenno:'Brenno','ryan-ellis':'Ryan Ellis','gavin-the-hotrod':'Gavin','lj-the-messenger':'LJ',dearis:'De’aris',tonyxtrotter:'tonyxtrotter','andrew-prim':'Andrew Prim',apollo:'Apollo merch'};
export const roundSeconds={eli:26,marty:40,brenno:45,apollo:25,'ryan-ellis':40,'gavin-the-hotrod':40,'lj-the-messenger':45,dearis:45,tonyxtrotter:45,'andrew-prim':40};
export function roundSchedule(id,seed=1){
 let n=seed>>>0;const random=()=>{n=(Math.imul(1664525,n)+1013904223)>>>0;return n/4294967296;};
 const first=id==='eli'?2.58:id==='apollo'?2.3:3.3,step=id==='eli'?120/104:(roundSeconds[id]-first-1.4)/19;
 return Array.from({length:20},(_,i)=>{
  const lane=Math.floor(random()*4),position=random();
  return {id:i,at:first+i*step,lane,x:id==='apollo'?(i%2?265:65)+position*90:65+position*290,kind:i%(id==='apollo'?merchItems.length:3)};
 });
}
export function roundScore(events){
 const seen=new Set();let total=0,hits=0,perfect=0,streak=0,bestCombo=0;
 for(const e of events||[]){if(!Number.isInteger(e.id)||e.id<0||e.id>=20||seen.has(e.id))continue;seen.add(e.id);if(e.breakBefore)streak=0;
  if(e.hit===true){hits++;streak++;total+=40;if(e.perfect===true){total+=10;perfect++;}bestCombo=Math.max(bestCombo,streak);}else streak=0;
 }
 return {total,hits,perfect,bestCombo};
}
export function validateRound(result){return gameIds.includes(result?.game)&&typeof result.id==='string'&&result.id.length<100&&Array.isArray(result.events)&&result.events.length===20&&new Set(result.events.map(e=>e.id)).size===20&&result.events.every(e=>Number.isInteger(e.id)&&e.id>=0&&e.id<20&&typeof e.hit==='boolean'&&typeof e.perfect==='boolean'&&(!e.perfect||e.hit));}
export const blankTotals=()=>Object.fromEntries(gameIds.map(id=>[id,0]));
