import {avatars,playerName} from './avatars.mjs';
export const MAX_SCORE=125;
export const initialState=()=>({version:1,name:'',avatar:'red',profileReady:false,beatBest:0,eli:false,photoStyle:{pose:'classic',frame:'gold'},room:'outside',friends:[],merch:null,worship:false,photo:false,entered:false,x:470,y:575});
export const validPhotoStyle=value=>({pose:['classic','lean'].includes(value?.pose)?value.pose:'classic',frame:['gold','mint','rose'].includes(value?.frame)?value.frame:'gold'});
export const score=s=>s.friends.length*15+(s.merch?20:0)+(s.worship?25:0)+(s.eli?25:0)+(s.photo?25:0);
export const coins=s=>20-(s.merch?10:0);
export function pointsToGo(s){
 const remaining=[];
 if(s.friends.length<2)remaining.push(`Invite ${s.friends.includes('jay')?'Grace':s.friends.includes('grace')?'Jay':'Jay + Grace'}: +${(2-s.friends.length)*15}`);
 if(!s.merch)remaining.push('Finish merch + take your bag: +20');
 if(!s.worship)remaining.push('Hands up at either artist: +25');
 if(!s.eli)remaining.push('Finish Eli’s beat game: +25');
 if(!s.photo)remaining.push('Take your VIP photo: +25');
 return remaining.length?`${MAX_SCORE-score(s)} XP TO FIREWORKS · ${remaining.join(' · ')}`:`${MAX_SCORE} XP · FIREWORKS UNLOCKED · YOUR VIP PHOTO IS READY`;
}
export function objective(s){if(s.friends.length<2)return 'A show hits different with your people. Invite Jay and Grace.';if(!s.entered)return 'Crew’s together. Pull up to the show!';if(!s.merch)return 'Finish the merch activity, then take your bag to earn +20 XP.';if(!s.worship)return 'Get to either artist’s circle. Hands high for Jesus. +25 XP.';if(!s.eli)return 'Finish one round of Eli’s B–I–B–L–E beat game. +25 XP.';if(!s.photo)return 'Meet the band in VIP and take your photo. +25 XP.';return `${MAX_SCORE} XP! Night made. Fireworks unlocked. All glory to Jesus.`;}
export function act(s,action,value){
 const next={...s,friends:[...s.friends]};
 if(action==='photoStyle'&&s.room==='vip')next.photoStyle=validPhotoStyle(value);
 if(action==='profile'&&playerName(value?.name)&&avatars.some(a=>a.id===value?.avatar)){next.name=playerName(value.name);next.avatar=value.avatar;next.profileReady=true;}
 if(action==='beat'&&s.room==='show'&&Number.isInteger(value)&&value>=0&&value<=10){next.beatBest=Math.max(s.beatBest||0,value);next.eli=true;}
 if(action==='invite'&&s.room==='outside'&&['jay','grace'].includes(value)&&!s.friends.includes(value))next.friends.push(value);
 if(action==='enter'&&s.friends.length===2){next.room='show';next.entered=true;next.x=500;next.y=575;}
 if(action==='merch'&&s.room==='show'&&!s.merch&&['cream','mint','black'].includes(value))next.merch=value;
 if(action==='worship'&&s.room==='show')next.worship=true;
 if(action==='vip'&&s.room==='show'){next.room='vip';next.x=500;next.y=570;}
 if(action==='photo'&&s.room==='vip')next.photo=true;
 if(action==='outside'){next.room='outside';next.x=730;next.y=400;}
 if(action==='show'&&s.entered){next.room='show';next.x=870;next.y=490;}
 return next;
}
export function restore(raw){try{const s=JSON.parse(raw);if(s.version!==1)return initialState();const f=[...new Set(s.friends)].filter(x=>['jay','grace'].includes(x));const entered=!!s.entered&&f.length===2;const merch=entered&&['cream','mint','black'].includes(s.merch)?s.merch:null;const worship=!!s.worship&&entered;const beatBest=Number.isInteger(s.beatBest)?Math.max(0,Math.min(10,s.beatBest)):0;const eli=entered&&(typeof s.eli==='boolean'?s.eli:beatBest>0);return{...initialState(),photoStyle:validPhotoStyle(s.photoStyle),name:playerName(s.name),avatar:avatars.some(a=>a.id===s.avatar)?s.avatar:'red',profileReady:!!s.profileReady&&!!playerName(s.name),beatBest,eli,friends:f,entered,merch,worship,photo:!!s.photo&&entered,room:s.room==='vip'&&entered?'vip':s.room==='show'&&entered?'show':'outside'};}catch{return initialState();}}
