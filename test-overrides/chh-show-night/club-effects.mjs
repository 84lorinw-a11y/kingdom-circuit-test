import {drawPerson} from './sprites.mjs?v=apollo-10';

function roadCase(g,x,y,w=38,h=30){
 g.fillStyle='#16181c';g.fillRect(x-w/2,y-h,w,h);g.strokeStyle='#a6a8aa';g.lineWidth=2;g.strokeRect(x-w/2,y-h,w,h);g.fillStyle='#7c8185';g.fillRect(x-6,y-h+9,12,3);
 g.fillStyle='#08090b';g.beginPath();g.arc(x-w/2+6,y+3,4,0,7);g.arc(x+w/2-6,y+3,4,0,7);g.fill();
}
export function drawAlleyLoadIn(g,time,reduced,art){
 g.save();const dx=reduced?0:Math.sin(time/9000)*3;
 roadCase(g,143,419,31,28);roadCase(g,143,388,29,25);
 if(art.roadies)g.drawImage(art.roadies,0,0,art.roadies.width,art.roadies.height,12+dx,315,146,97);
 g.fillStyle='#141719';g.fillRect(52,294,87,20);g.fillStyle='#d1c5ad';g.textAlign='center';g.font='bold 10px monospace';g.fillText('LOAD IN →',95,308);g.restore();
}
export function drawStageSmoke(g,time,reduced){
 g.save();
 // Stage machine emits a low layer, well below faces and above floor game rings.
 g.fillStyle='#14161a';g.fillRect(220,326,40,24);g.strokeStyle='#74797c';g.lineWidth=1;g.strokeRect(220,326,40,24);g.fillStyle='#686b6b';g.fillRect(257,332,10,9);g.fillStyle='#98b5a2';g.fillRect(226,331,3,3);
 g.strokeStyle='#1e2023';g.lineWidth=3;g.beginPath();g.moveTo(222,347);g.lineTo(204,357);g.lineTo(190,357);g.stroke();
 g.beginPath();g.rect(266,318,559,64);g.clip();
 for(let i=0;i<9;i++){
  const age=reduced?i/9:((time/13000+i/9)%1),x=270+age*535,y=348+Math.sin(age*7+i)*5,r=30+age*55;
  const fog=g.createRadialGradient(x,y,0,x,y,r);fog.addColorStop(0,`rgba(203,205,211,${.37*(1-age)})`);fog.addColorStop(1,'rgba(203,205,211,0)');g.fillStyle=fog;g.beginPath();g.ellipse(x,y,r,r*.40,0,0,7);g.fill();
 }
 g.restore();
}
export function drawStageLights(g,time,reduced){
 // Slow, faint cones from the existing fixtures. No strobes or new fixtures.
 g.save();g.beginPath();g.rect(205,66,620,310);g.clip();
 for(const [x,phase] of [[335,0],[714,2.4]]){
  const aim=x+(reduced?0:Math.sin(time/11000+phase)*65);
  const light=g.createLinearGradient(x,70,aim,365);
  light.addColorStop(0,'rgba(246,227,202,.10)');
  light.addColorStop(.7,'rgba(246,227,202,.035)');
  light.addColorStop(1,'rgba(246,227,202,0)');
  g.fillStyle=light;g.beginPath();g.moveTo(x-3,70);g.lineTo(x+3,70);
  g.lineTo(aim+65,365);g.lineTo(aim-65,365);g.closePath();g.fill();
 }
 g.restore();
}
