import {drawPerson} from './sprites.mjs?v=apollo-04';

export const offerWindow=.42,cleanOfferWindow=.16;
export const offerLane=note=>Math.max(0,Math.min(2,Math.floor((note.x-42)/112)));
export const offerX=lane=>70+lane*140;
export function offerLayout(height=560){return {height,top:132,line:height-151,lead:1.9};}
export function offerY(note,time,height=560){const l=offerLayout(height);return l.line-(note.at-time)*(l.line-l.top)/l.lead;}
export function judgeOffer(notes,lane,time){
 if(!Number.isInteger(lane)||lane<0||lane>2||!Number.isFinite(time))return null;
 const note=notes.filter(n=>!n.done&&offerLane(n)===lane).sort((a,b)=>Math.abs(a.at-time)-Math.abs(b.at-time))[0];
 if(!note||Math.abs(note.at-time)>offerWindow)return null;
 return {note,perfect:Math.abs(note.at-time)<=cleanOfferWindow};
}
const buyers=['fan:3','fan:17','fan:22'];
const amounts=['$1 MILLION','$5 MILLION','$10 MILLION','$25 MILLION'];

export function drawOfferBoard(g,{height=560,art,time,phase,notes,lane=1,reduced=false}){
 const l=offerLayout(height);
 g.fillStyle='#101012';g.fillRect(0,0,420,height);
 if(art.show){g.drawImage(art.show,300,0,930,850,0,0,420,height);g.fillStyle='#101012ed';g.fillRect(0,0,420,height);}
 g.textAlign='center';g.fillStyle='#f5f0e7';g.font='900 29px sans-serif';g.fillText('APOLLO IS NOT 4 SALE',210,39);
 g.font='12px monospace';g.fillStyle='#c7c1b9';g.fillText('THE LABEL STAYS WITH THE CREW.',210,62);
 g.font='bold 11px monospace';g.fillStyle='#ec7a71';g.fillText('TURN THE BUYERS AWAY',210,88);
 for(let i=0;i<3;i++){
  const x=offerX(i);g.fillStyle=lane===i?'#ffffff0c':'#ffffff04';g.fillRect(i*140+6,110,128,height-120);
  g.strokeStyle='#ffffff19';g.lineWidth=1;g.setLineDash([3,9]);g.beginPath();g.moveTo(i*140+4,114);g.lineTo(i*140+4,l.line);g.stroke();g.setLineDash([]);
  g.fillStyle='#f1ede1';g.font='bold 11px monospace';g.fillText(['LEFT','CENTER','RIGHT'][i],x,124);
 }
 // The wide red strip is the timing window; each offer card crosses its center.
 g.fillStyle='#be433c40';g.fillRect(7,l.line-24,406,48);g.fillStyle='#e96d63';g.fillRect(7,l.line-2,406,4);
 for(const note of notes){
  const since=time-(note.resolvedAt??-Infinity);if(note.done&&since>.55)continue;
  const x=offerX(offerLane(note));let y=offerY(note,time,height);if(note.done&&note.rejected)y=l.line-since*180;
  if(y<l.top-12||y>l.line+65)continue;
  g.save();if(note.done)g.globalAlpha=Math.max(0,1-since/.55);
  drawPerson(g,x,y+28,buyers[note.id%buyers.length],{scale:1.52,walking:!reduced,frame:time*7+note.id});
  const ready=Math.abs(note.at-time)<=offerWindow&&!note.done;
  g.fillStyle='#e9e1cf';g.fillRect(x-55,y-23,110,47);g.strokeStyle=ready?'#f28578':'#a29886';g.lineWidth=ready?3:1;g.strokeRect(x-55,y-23,110,47);
  g.fillStyle='#262222';g.font='900 12px sans-serif';g.fillText('BUY APOLLO',x,y-7);g.font='bold 11px monospace';g.fillText(amounts[Math.floor(note.id/5)],x,y+12);
  if(note.done){g.translate(x,y);g.rotate(-.1);g.fillStyle=note.rejected?'#9b2724':'#333';g.fillRect(-58,-15,116,30);g.fillStyle='#fff4eb';g.font='900 16px sans-serif';g.fillText(note.rejected?'NOT 4 SALE':'SLIPPED BY',0,6);}
  g.restore();
 }
 const x=offerX(lane);drawPerson(g,x,height-11,'marty',{scale:2.1,walking:false});
 g.fillStyle='#171719';g.fillRect(x-49,height-44,98,25);g.strokeStyle='#e0645b';g.lineWidth=1;g.strokeRect(x-49,height-44,98,25);g.fillStyle='#f4eee4';g.font='900 12px sans-serif';g.fillText('NOT 4 SALE',x,height-27);
 if(phase==='playing'&&time<1.4){g.fillStyle='#151516f2';g.fillRect(38,171,344,62);g.fillStyle='#f5eee3';g.font='bold 14px sans-serif';g.fillText('BUYERS ARE COMING.',210,196);g.font='12px sans-serif';g.fillText('Tap their lane when the offer hits the red line.',210,218);}
 return l;
}
