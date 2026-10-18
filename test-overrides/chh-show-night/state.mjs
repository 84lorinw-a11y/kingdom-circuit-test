import {avatars,playerName} from './avatars.mjs?v=show-12';
import {gameIds,blankTotals,roundScore,validateRound} from './scoring.mjs?v=show-12';
export const MAX_SCORE=1000; // First celebration milestone, never a total-score ceiling.
export const initialState=()=>({version:2,name:'',avatar:'red',profileReady:false,beatBest:0,eli:false,photoStyle:{pose:'classic',frame:'gold'},room:'outside',friends:[],merch:null,worship:false,photo:false,entered:false,x:470,y:575,totals:blankTotals(),roundIds:[],rounds:0,sessionId:''});
export const validPhotoStyle=value=>({pose:['classic','lean'].includes(value?.pose)?value.pose:'classic',frame:['gold','mint','rose'].includes(value?.frame)?value.frame:'gold'});
export const journeyScore=s=>s.friends.length*15+(s.worship?25:0)+(s.photo?25:0);
export const score=s=>journeyScore(s)+gameIds.reduce((n,id)=>n+(s.totals?.[id]||0),0);
export const coins=s=>20-(s.merch?10:0);
export const pointsToGo=s=>`Next fireworks: ${(Math.floor(score(s)/1000)+1)*1000} · Replay any game to keep scoring`;
export function objective(s){if(s.friends.length<2)return 'Tap Jay + Grace. Bring your people.';if(!s.entered)return 'Crew ready. Tap the venue to head inside.';if(s.room==='vip')return 'Make a memory. Tap the photo circle.';return 'Tap an artist or merch. Play, replay, keep scoring.';}
export function act(s,action,value){
 const next={...s,friends:[...s.friends],totals:{...s.totals}};
 if(action==='photoStyle'&&s.room==='vip')next.photoStyle=validPhotoStyle(value);
 if(action==='profile'&&playerName(value?.name)&&avatars.some(a=>a.id===value?.avatar)){next.name=playerName(value.name);next.avatar=value.avatar;next.profileReady=true;}
 if(action==='round'&&s.room==='show'&&validateRound(value)&&!s.roundIds.includes(value.id)){
  const points=roundScore(value.events);next.totals[value.game]+=points.total;next.roundIds=[...s.roundIds,value.id];next.rounds=s.rounds+1;
  if(value.game==='eli'){next.eli=true;next.beatBest=Math.max(s.beatBest,points.hits);}
  if(value.game==='chamblissnation'&&!s.merch)next.merch='camo';
 }
 if(action==='invite'&&s.room==='outside'&&['jay','grace'].includes(value)&&!s.friends.includes(value))next.friends.push(value);
 if(action==='enter'&&s.friends.length===2){next.room='show';next.entered=true;next.x=500;next.y=575;}
 if(action==='worship'&&s.room==='show')next.worship=true;
 if(action==='vip'&&s.room==='show'){next.room='vip';next.x=500;next.y=570;}
 if(action==='photo'&&s.room==='vip')next.photo=true;
 if(action==='outside'){next.room='outside';next.x=730;next.y=400;}
 if(action==='show'&&s.entered){next.room='show';next.x=870;next.y=490;}
 return next;
}
export function restore(raw){try{
 const s=JSON.parse(raw);if(![1,2].includes(s.version))return initialState();
 const f=[...new Set(Array.isArray(s.friends)?s.friends:[])].filter(x=>['jay','grace'].includes(x)),entered=!!s.entered&&f.length===2;
 const totals=blankTotals();if(s.version===2&&entered)for(const id of gameIds){const n=s.totals?.[id];totals[id]=Number.isSafeInteger(n)&&n>=0?n:0;}
 return {...initialState(),name:playerName(s.name),avatar:avatars.some(a=>a.id===s.avatar)?s.avatar:'red',profileReady:!!s.profileReady&&!!playerName(s.name),photoStyle:validPhotoStyle(s.photoStyle),friends:f,entered,merch:entered&&['cream','mint','black','camo'].includes(s.merch)?s.merch:null,worship:!!s.worship&&entered,photo:!!s.photo&&entered,eli:!!s.eli&&entered,beatBest:Math.max(0,Math.min(20,Number(s.beatBest)||0)),room:entered&&['show','vip'].includes(s.room)?s.room:'outside',totals,roundIds:Array.isArray(s.roundIds)?s.roundIds.filter(x=>typeof x==='string'):[],rounds:Number.isSafeInteger(s.rounds)&&s.rounds>=0?s.rounds:0,sessionId:typeof s.sessionId==='string'?s.sessionId:''};
 }catch{return initialState();}}
