import {panel,label,glow} from './arcade-drawing.mjs?v=apollo-25';

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
 g.save();g.fillStyle='#08121a';g.fillRect(0,0,420,l.height);
 if(art.arcade_eli){const im=art.arcade_eli,cut=im.height*.35;
  g.drawImage(im,0,0,im.width,cut,0,0,420,laneTop);
  g.drawImage(im,0,cut,im.width,im.height-cut,0,laneTop,420,l.height-laneTop);
 }
 if(art.eliBanner){const w=85,h=w*art.eliBanner.height/art.eliBanner.width;g.save();g.translate(83,laneTop*.235);g.rotate(.11);g.drawImage(art.eliBanner,-w/2,-h/2,w,h);g.restore();}
 const track=g.createLinearGradient(0,laneTop,0,l.height);track.addColorStop(0,'#05121a77');track.addColorStop(1,'#081822c4');g.fillStyle=track;g.fillRect(0,laneTop,420,l.height-laneTop);
 for(let lane=0;lane<4;lane++){
  const x=lane*105,color=laneColors[lane],life=Math.max(0,(flashes[lane]||0)-time);
  panel(g,x+5,laneTop+8,95,l.height-laneTop-14,8,lane%2?'#08151e44':'#18303c44',color+'35');
  g.strokeStyle=color+'77';g.lineWidth=1;g.beginPath();g.moveTo(x+11,laneTop+15);g.lineTo(x+11,l.height-12);g.stroke();
  panel(g,x+14,hitY-22,77,44,7,'#102c38',color);
  label(g,String(lane+1),x+52.5,hitY+6,16,color);
  if(life){g.save();g.globalAlpha=Math.min(.4,life*1.5);g.fillStyle=color;g.fillRect(x+6,laneTop+8,93,l.height-laneTop-16);g.restore();glow(g,x+52.5,hitY,46,color+'88');}
 }
 if(!reduced)for(let i=0;i<7;i++){const y=laneTop+((time*45+i*64)%(hitY-laneTop));g.strokeStyle='#b8e3cc12';g.lineWidth=1;g.beginPath();g.moveTo(9,y);g.lineTo(411,y);g.stroke();}
 g.shadowColor='#ffce72';g.shadowBlur=reduced?0:10+bass*8;g.fillStyle='#ffe2a2';g.fillRect(4,hitY-2,412,4);g.shadowBlur=0;
 for(const n of notes){
  if(n.done)continue;const y=beatY(l,n.at,time);if(y<laneTop-28||y>l.height+28)continue;
  const ready=Math.abs(n.at-time)<.32,x=n.lane*105+52.5,color=ready?'#ffdc8e':laneColors[n.lane];
  const cap=g.createLinearGradient(0,y-28,0,y+28);cap.addColorStop(0,'#edf7ea');cap.addColorStop(.08,color);cap.addColorStop(.88,color);cap.addColorStop(1,'#536d76');
  g.save();g.shadowColor=ready?color:'#000';g.shadowBlur=reduced?0:ready?16:6;g.shadowOffsetY=4;panel(g,x-38,y-28,76,56,8,cap,'#edfff5b0');g.restore();
  panel(g,x-31,y-21,62,40,5,'#00000009','#19344044');label(g,'BIBLE'[n.id%5],x,y+12,33,'#102734');
 }
 // Feedback strip stays above the note lanes; the DJ remains visible.
 panel(g,89,laneTop-24,242,24,4,'#09222be8','#b0c2a855');label(g,streakLabel(combo),210,laneTop-8,10,combo>=5?'#ffe3a0':'#c5e4de');
 if(phase==='playing'&&time<1.35){panel(g,61,hitY-124,298,61,8,'#09202eef','#d8c58b');label(g,'GET READY',210,hitY-97,22);label(g,'TAP WHEN THE LETTER HITS THE LINE',210,hitY-78,10);}
 g.restore();return l;
}
