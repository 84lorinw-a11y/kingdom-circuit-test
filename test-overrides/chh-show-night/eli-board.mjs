import {drawPerson} from './sprites.mjs?v=apollo-10';

export const laneColors=['#80e2be','#a9b8ff','#ffc876','#ff9eb5'];
export function beatLayout(height=560){
 const h=Math.max(360,height),laneTop=Math.min(205,h*.35);
 return {width:420,height:h,laneTop,hitY:h-42,laneWidth:105,noteWidth:76,noteHeight:56,lead:1.8};
}
export const beatY=(layout,at,time)=>layout.hitY-(at-time)*(layout.hitY-layout.laneTop)/layout.lead;
export function beatLane(clientX,left,width){return Math.max(0,Math.min(3,Math.floor((clientX-left)/width*4)));}
export function judgeBeat(notes,lane,time){
 if(!Number.isInteger(lane)||lane<0||lane>3||!Number.isFinite(time))return null;
 const note=notes.filter(n=>!n.done&&n.lane===lane).sort((a,b)=>Math.abs(a.at-time)-Math.abs(b.at-time))[0];
 if(!note||Math.abs(note.at-time)>=.32)return null;
 return {note,perfect:Math.abs(note.at-time)<.16};
}
export function streakLabel(combo){return combo>=20?'20 IN A ROW · ALL FOR THE KING':combo>=15?'ALL FOR THE KING':combo>=10?'ON FIRE':combo>=5?'LOCKED IN':'FIND YOUR RHYTHM';}

export function drawBeatBoard(g,{height,art,time,phase,notes,reduced,combo,bass=0,flashes=[]}){
 const l=beatLayout(height),{laneTop,hitY}=l;
 g.fillStyle='#07131f';g.fillRect(0,0,420,l.height);
 if(art.show){g.drawImage(art.show,300,0,930,850,0,0,420,l.height);g.fillStyle='#07131edb';g.fillRect(0,0,420,l.height);}
 // Keep the concert's artist and detailed decks in the minigame.
 g.save();g.beginPath();g.rect(0,0,420,laneTop+2);g.clip();
 const glow=g.createRadialGradient(210,laneTop*.5,8,210,laneTop*.5,230);glow.addColorStop(0,'#2b9f814d');glow.addColorStop(1,'#09203100');g.fillStyle=glow;g.fillRect(0,0,420,laneTop);
 const feet=laneTop-35;drawPerson(g,210,feet,'eli-williams',{scale:2.5,lean:reduced?0:Math.sin(time*2)*.018});
 if(art.booth)g.drawImage(art.booth,85,laneTop-125,250,125);
 g.restore();
 const track=g.createLinearGradient(0,laneTop,0,l.height);track.addColorStop(0,'#07131fee');track.addColorStop(1,'#102b3bf5');g.fillStyle=track;g.fillRect(0,laneTop,420,l.height-laneTop);
 for(let lane=0;lane<4;lane++){
  const x=lane*105,color=laneColors[lane];
  g.fillStyle=lane%2?'#ffffff05':'#ffffff0a';g.fillRect(x+3,laneTop,99,l.height-laneTop);
  g.strokeStyle='#9bc4d824';g.lineWidth=1;g.beginPath();g.moveTo(x+1,laneTop);g.lineTo(x+1,l.height);g.stroke();
  // Touch targets and falling notes share the same four lane centers.
  g.fillStyle='#07131f';g.fillRect(x+13,hitY-22,79,44);g.strokeStyle=color;g.lineWidth=2;g.strokeRect(x+13,hitY-22,79,44);
  g.fillStyle=color;g.font='bold 14px monospace';g.textAlign='center';g.fillText(String(lane+1),x+52.5,hitY+5);
  const life=Math.max(0,(flashes[lane]||0)-time);
  if(life){g.fillStyle=color;g.globalAlpha=Math.min(.5,life*1.8);g.fillRect(x+3,laneTop,99,l.height-laneTop);g.globalAlpha=1;}
 }
 if(!reduced){g.strokeStyle='#7ed9b11b';g.lineWidth=1;for(let n=0;n<5;n++){const y=laneTop+((time*55+n*80)%(hitY-laneTop));g.beginPath();g.moveTo(4,y);g.lineTo(416,y);g.stroke();}}
 g.fillStyle='#ffcb6c28';g.fillRect(0,hitY-13,420,26);g.shadowColor='#ffcb6c';g.shadowBlur=reduced?0:10+bass*10;g.fillStyle='#ffe3a0';g.fillRect(0,hitY-3,420,6);g.shadowBlur=0;
 for(const n of notes){
  if(n.done)continue;const y=beatY(l,n.at,time);if(y<laneTop-28||y>l.height+28)continue;
  const ready=Math.abs(n.at-time)<.32,x=n.lane*105+52.5,color=ready?'#ffdb8e':laneColors[n.lane];
  g.fillStyle='#020a14';g.fillRect(x-38,y-25,76,58);g.shadowColor=color;g.shadowBlur=reduced?0:ready?18:5;g.fillStyle=color;g.fillRect(x-38,y-28,76,52);g.shadowBlur=0;
  g.fillStyle='#ffffff60';g.fillRect(x-34,y-24,68,3);g.fillStyle='#0b1b2b';g.font='900 34px monospace';g.textAlign='center';g.fillText('BIBLE'[n.id%5],x,y+11);
 }
 // Small, persistent cue stays outside the falling-note lanes.
 g.fillStyle='#091724ed';g.fillRect(0,laneTop-26,420,26);g.font='bold 11px monospace';g.textAlign='center';g.fillStyle=combo>=5?'#ffdb8e':'#b7d6d5';g.fillText(streakLabel(combo),210,laneTop-9);
 if(phase==='playing'&&time<1.35){g.fillStyle='#07131fdc';g.fillRect(70,hitY-125,280,64);g.fillStyle='#ffdb8e';g.font='bold 24px monospace';g.fillText('GET READY',210,hitY-96);g.font='12px monospace';g.fillStyle='#e9f5ec';g.fillText('TAP WHEN THE LETTER HITS THE LINE',210,hitY-76);}
 return l;
}
