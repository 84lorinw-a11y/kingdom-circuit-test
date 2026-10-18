export const breakDuration=6000;
export function breakProgress(start,now){const elapsed=Math.max(0,now-start);return {elapsed,remaining:Math.max(0,Math.ceil((breakDuration-elapsed)/1000)),done:elapsed>=breakDuration};}
// Animate a small bottle and bent arm over the existing Jay / Grace artwork.
export function drawWaterSip(ctx,{x,y,who},elapsed,reduced){
 const phase=elapsed/1000+(who==='grace'?1.1:0),sip=reduced?.75:(Math.sin(phase*2.1)+1)/2;
 const handX=14-sip*9,handY=-72-sip*36,skin=who==='jay'?'#835035':'#e9b58d';
 ctx.save();ctx.translate(x,y);ctx.lineCap='round';ctx.lineJoin='round';
 ctx.strokeStyle=who==='jay'?'#515541':'#a384bc';ctx.lineWidth=11;ctx.beginPath();ctx.moveTo(22,-96);ctx.lineTo(30,-77);ctx.stroke();
 ctx.strokeStyle=skin;ctx.lineWidth=6;ctx.beginPath();ctx.moveTo(30,-77);ctx.lineTo(handX,handY+5);ctx.stroke();
 ctx.translate(handX,handY);ctx.rotate(-sip*.9);ctx.fillStyle='#a7e4f4';ctx.strokeStyle='#26788d';ctx.lineWidth=1.3;ctx.fillRect(-4,-15,9,23);ctx.strokeRect(-4,-15,9,23);ctx.fillStyle='#f1fcff';ctx.fillRect(-3,-7,7,6);ctx.fillStyle='#4aabd0';ctx.fillRect(-3,-20,7,5);ctx.fillStyle=skin;ctx.beginPath();ctx.arc(3,2,4,0,7);ctx.fill();ctx.restore();
}
