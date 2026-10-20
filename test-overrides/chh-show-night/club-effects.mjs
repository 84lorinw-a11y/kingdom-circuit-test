import {drawPerson} from './sprites.mjs?v=apollo-04';

function roadCase(g,x,y,w=38,h=30){
 g.fillStyle='#16181c';g.fillRect(x-w/2,y-h,w,h);g.strokeStyle='#a6a8aa';g.lineWidth=2;g.strokeRect(x-w/2,y-h,w,h);g.fillStyle='#7c8185';g.fillRect(x-6,y-h+9,12,3);
 g.fillStyle='#08090b';g.beginPath();g.arc(x-w/2+6,y+3,4,0,7);g.arc(x+w/2-6,y+3,4,0,7);g.fill();
}
export function drawAlleyLoadIn(g,time,reduced){
 g.save();
 // Small figures deepen into the existing alley, leaving the front sidewalk open.
 const progress=reduced?.45:(Math.sin(time/4800)+1)/2,y=370+progress*43,x=90+progress*15;
 drawPerson(g,58,390,'fan:16',{scale:1.25,flip:true});
 drawPerson(g,x-17,y,'fan:5',{scale:1.1+progress*.2,walking:!reduced,frame:time/160});roadCase(g,x+7,y+7,29+progress*6,24);
 roadCase(g,139,424,36,32);roadCase(g,139,390,31,25);
 g.fillStyle='#141719';g.fillRect(52,312,87,20);g.fillStyle='#d1c5ad';g.textAlign='center';g.font='bold 10px monospace';g.fillText('LOAD IN →',95,326);
 g.restore();
}
export function drawStageSmoke(g,time,reduced){
 g.save();
 // Stage machine emits a low layer, well below faces and above floor game rings.
 g.fillStyle='#14161a';g.fillRect(220,326,40,24);g.strokeStyle='#74797c';g.lineWidth=1;g.strokeRect(220,326,40,24);g.fillStyle='#686b6b';g.fillRect(257,332,10,9);g.fillStyle='#98b5a2';g.fillRect(226,331,3,3);
 g.strokeStyle='#1e2023';g.lineWidth=3;g.beginPath();g.moveTo(222,347);g.lineTo(204,357);g.lineTo(190,357);g.stroke();
 g.beginPath();g.rect(266,318,559,55);g.clip();
 for(let i=0;i<7;i++){
  const age=reduced?i/7:((time/13000+i/7)%1),x=270+age*535,y=348+Math.sin(age*7+i)*5,r=30+age*55;
  const fog=g.createRadialGradient(x,y,0,x,y,r);fog.addColorStop(0,`rgba(203,205,211,${.3*(1-age)})`);fog.addColorStop(1,'rgba(203,205,211,0)');g.fillStyle=fog;g.beginPath();g.ellipse(x,y,r,r*.35,0,0,7);g.fill();
 }
 g.restore();
}
