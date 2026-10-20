import {vipReturn} from './venue-layout.mjs?v=apollo-09';
import {matchesVipCode} from './vip-access.mjs?v=apollo-09';
import {avatars,playerName} from './avatars.mjs?v=apollo-09';
import {gameIds,blankTotals,roundScore,validateRound} from './scoring.mjs?v=apollo-09';
import {roomStops,visitIds} from './journey-guide.mjs?v=apollo-09';
export {journeyObjective as objective} from './journey-guide.mjs?v=apollo-09';
export const MAX_SCORE=1000; // First celebration milestone, never a total-score ceiling.
export const initialState=()=>({version:2,vipUnlocked:false,name:'',avatar:'',profileReady:false,beatBest:0,crewDelivered:0,eli:false,photoStyle:{pose:'classic',frame:'gold'},room:'outside',friends:[],visited:[],merch:null,worship:false,photo:false,entered:false,x:470,y:575,totals:blankTotals(),roundIds:[],rounds:0,sessionId:''});
export const validPhotoStyle=value=>({pose:['classic','lean','peace'].includes(value?.pose)?value.pose:'classic',frame:['gold','mint','rose'].includes(value?.frame)?value.frame:'gold'});
export const journeyScore=s=>s.friends.length*15+(s.worship?25:0)+(s.photo?25:0);
export const score=s=>journeyScore(s)+gameIds.reduce((n,id)=>n+(s.totals?.[id]||0),0);
export const coins=s=>20-(s.merch?10:0);
export const pointsToGo=s=>`Next fireworks: ${(Math.floor(score(s)/1000)+1)*1000} · Replay any game to keep scoring`;
export function act(s,action,value){
 const next={...s,friends:[...s.friends],visited:[...(s.visited||[])],totals:{...s.totals}};
 const visit=id=>{if(!next.visited.includes(id))next.visited.push(id);};
 if(action==='visit'&&roomStops[s.room]?.includes(value))visit(value);
 if(action==='photoStyle'&&s.room==='vip')next.photoStyle=validPhotoStyle(value);
 if(action==='profile'&&playerName(value?.name)&&avatars.some(a=>a.id===value?.avatar)){next.name=playerName(value.name);next.avatar=value.avatar;next.profileReady=true;}
 if(action==='round'&&s.room==='show'&&validateRound(value)&&!s.roundIds.includes(value.id)){
  const points=roundScore(value.events);next.totals[value.game]=(next.totals[value.game]||0)+points.total;next.roundIds=[...s.roundIds,value.id];next.rounds=s.rounds+1;
  if(value.game==='eli'){next.eli=true;next.beatBest=Math.max(s.beatBest,points.hits);}
  if(value.game==='brenno'&&Number.isInteger(value.meta?.delivered))next.crewDelivered=Math.min(20,(s.crewDelivered||0)+Math.max(0,Math.min(20,value.meta.delivered)));
  if(value.game==='apollo'&&!s.merch)next.merch='not4sale';
  visit(value.game==='apollo'?'merch':value.game==='eli'?'dj':value.game);
 }
 if(action==='invite'&&s.room==='outside'&&['jay','grace'].includes(value)&&!s.friends.includes(value))next.friends.push(value);
 if(action==='enter'&&s.friends.length===2){next.room='show';next.entered=true;next.x=500;next.y=575;}
 if(action==='worship'&&s.room==='show')next.worship=true;
 if(action==='unlockVip'&&s.room==='show'&&matchesVipCode(value))next.vipUnlocked=true;
 if(action==='vip'&&s.room==='show'&&s.vipUnlocked){next.room='vip';next.x=500;next.y=570;visit('vip');}
 if(action==='photo'&&s.room==='vip')next.photo=true;
 if(action==='outside'){next.room='outside';next.x=730;next.y=400;}
 if(action==='show'&&s.entered){next.room='show';Object.assign(next,vipReturn);}
 return next;
}
export function restore(raw){try{
 const s=JSON.parse(raw);if(![1,2].includes(s.version))return initialState();
 const f=[...new Set(Array.isArray(s.friends)?s.friends:[])].filter(x=>['jay','grace'].includes(x)),entered=!!s.entered&&f.length===2;
 const totals=blankTotals();if(s.version===2&&entered)for(const id of gameIds){const n=s.totals?.[id];totals[id]=Number.isSafeInteger(n)&&n>=0?n:0;}
 const avatar=avatars.some(a=>a.id===s.avatar)?s.avatar:'';
 return {...initialState(),name:playerName(s.name),avatar,vipUnlocked:entered&&s.vipUnlocked===true,profileReady:!!s.profileReady&&!!playerName(s.name)&&!!avatar,photoStyle:validPhotoStyle(s.photoStyle),friends:f,entered,visited:entered&&Array.isArray(s.visited)?[...new Set(s.visited.filter(id=>visitIds.includes(id)))]:[],merch:entered&&['not4sale','cream','mint','black','camo'].includes(s.merch)?s.merch:null,worship:!!s.worship&&entered,photo:!!s.photo&&entered,eli:!!s.eli&&entered,crewDelivered:entered?Math.max(0,Math.min(20,Number(s.crewDelivered)||0)):0,beatBest:Math.max(0,Math.min(20,Number(s.beatBest)||0)),room:entered&&['show','vip'].includes(s.room)?(s.room==='vip'&&s.vipUnlocked!==true?'show':s.room):'outside',totals,roundIds:Array.isArray(s.roundIds)?s.roundIds.filter(x=>typeof x==='string'):[],rounds:Number.isSafeInteger(s.rounds)&&s.rounds>=0?s.rounds:0,sessionId:typeof s.sessionId==='string'?s.sessionId:''};
 }catch{return initialState();}}
