import {drawPerson} from './sprites.mjs?v=apollo-09';
// Stationary deal table: reject ownership offers, leave genuine support alone.
export const offerLane=note=>Math.max(0,Math.min(2,Math.floor((note.x-42)/112)));
export const offerX=lane=>70+lane*140;
export function offerPrompt(notes,time){const note=notes.find(n=>!n.done);if(!note)return null;const start=note.id?notes[note.id-1].at:0;return {note,start,ready:time>=start&&time<=note.at};}
export function judgeOffer(notes,lane,time){const prompt=offerPrompt(notes,time);if(!prompt?.ready||!Number.isInteger(lane)||lane<0||lane>2)return null;const hit=offerLane(prompt.note)===lane;return {note:prompt.note,hit,perfect:hit&&time-prompt.start<=.9};}
const deals=[['BUY THE LABEL','OWN YOUR MASTERS','CONTROL THE CREW','SELL APOLLO'],['BOOK A SHOW','BUY A TICKET','JOIN THE CREW','SHARE THE MUSIC']];
export function drawOfferBoard(g,{time,phase,notes}){
 g.fillStyle='#171719';g.fillRect(0,0,420,560);g.textAlign='center';
 const text=(v,x,y,size=14,color='#eee8da')=>{g.fillStyle=color;g.font=`bold ${size}px sans-serif`;g.fillText(v,x,y);};
 text('APOLLO IS NOT 4 SALE',210,38,26);text('Spot the buyout. Shut it down.',210,64,14,'#c7b7a3');
 const prompt=offerPrompt(notes,time),note=prompt?.note;drawPerson(g,210,230,'marty',{scale:2.5});
 g.fillStyle='#44372e';g.beginPath();g.moveTo(16,234);g.lineTo(404,234);g.lineTo(419,460);g.lineTo(1,460);g.closePath();g.fill();g.strokeStyle='#7d6250';g.lineWidth=4;g.stroke();
 for(let i=0;i<3;i++){const x=offerX(i),buy=note&&i===offerLane(note);drawPerson(g,x,500,['fan:3','fan:17','fan:22'][i],{scale:1.5});
  g.fillStyle='#e6ddc9';g.fillRect(x-62,270,124,121);g.strokeStyle='#9c8d77';g.lineWidth=1;g.strokeRect(x-62,270,124,121);text(['LEFT','CENTER','RIGHT'][i],x,292,11,'#736451');
  const words=note?deals[buy?0:1][(note.id+i)%4].split(' '):['NEXT','MEETING'];words.forEach((word,j)=>text(word,x,317+j*17,14,'#282326'));text(buy?'OWNERSHIP: US':'OWNERSHIP: YOU',x,380,9,'#655440');}
 if(prompt&&phase==='playing'){g.fillStyle='#4c4844';g.fillRect(35,520,350,6);g.fillStyle='#dc766a';g.fillRect(35,520,350*Math.max(0,(note.at-time)/(note.at-prompt.start)),6);text(prompt.ready?'REJECT THE BUYOUT BELOW':'NEXT MEETING…',210,549,12);}
}
