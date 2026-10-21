import {drawPerson} from './sprites.mjs?v=apollo-21';

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
export function drawStageSmoke(g,time,reduced,art){
 g.save();
 // The photographed-style prop sits onstage; the plume leaves its right nozzle.
 g.fillStyle='#00000035';g.beginPath();g.ellipse(368,357,25,4,0,0,Math.PI*2);g.fill();
 if(art?.hazer)g.drawImage(art.hazer,335,319,60,40);
 for(let i=0;i<12;i++){
  const age=reduced?(i+.5)/12:((time/16000+i/12)%1);
  const x=392+age*350,y=344-age*12+Math.sin(age*9+i)*3,r=9+age*58;
  const alpha=.16*Math.min(1,age*18)*Math.pow(1-age,1.5);
  g.save();g.translate(x,y);g.scale(1,.28+age*.1);
  // Scale the gradient with the wisp, so its entire edge fades to transparency.
  const fog=g.createRadialGradient(0,0,0,0,0,r);
  fog.addColorStop(0,`rgba(206,203,202,${alpha})`);fog.addColorStop(.4,`rgba(206,203,202,${alpha*.6})`);fog.addColorStop(1,'rgba(206,203,202,0)');
  g.fillStyle=fog;g.beginPath();g.arc(0,0,r,0,Math.PI*2);g.fill();g.restore();
 }
 g.restore();
}
export function drawStageLights(g,time,reduced){
 // Slow, faint cones from the existing fixtures. No strobes or new fixtures.
 g.save();g.beginPath();g.rect(205,66,620,310);g.clip();
 for(const [x,phase] of [[294,0],[682,2.4]]){
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
