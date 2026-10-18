import {drawPerson} from './sprites.mjs';
// Eli performs and hosts his practice station at center stage.
export const practiceSpot={x:512,y:475};
export function drawPracticeBooth(ctx,time=0){
 const x=512,y=363;
 ctx.save();
 ctx.fillStyle='#06111c88';ctx.beginPath();ctx.ellipse(x,y+4,91,13,0,0,Math.PI*2);ctx.fill();
 drawPerson(ctx,x,y,'dj',{scale:2.9});
 ctx.fillStyle='#060d17';ctx.fillRect(x-89,y-73,178,79);
 ctx.fillStyle='#30435b';ctx.fillRect(x-85,y-69,170,17);
 ctx.fillStyle='#12223a';ctx.fillRect(x-85,y-49,170,51);
 ctx.strokeStyle='#78debf';ctx.lineWidth=2;ctx.strokeRect(x-82,y-46,164,45);
 for(const dx of [-52,52]){ctx.fillStyle='#080e18';ctx.beginPath();ctx.ellipse(x+dx,y-62,22,8,0,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#8195a7';ctx.stroke();ctx.fillStyle='#ffbe59';ctx.fillRect(x+dx-3,y-65,6,6);}
 ctx.fillStyle='#060e19';ctx.fillRect(x-17,y-70,34,18);
 for(let i=0;i<5;i++){ctx.fillStyle=i%2?'#ffbf59':'#7ed9b1';ctx.fillRect(x-12+i*6,y-64+(i%2)*3,3,7);}
 ctx.textAlign='center';ctx.fillStyle='#ffcb78';ctx.font='bold 16px monospace';ctx.fillText('ELI',x,y-25);ctx.fillStyle='#edf6e9';ctx.font='bold 12px monospace';ctx.fillText('B–I–B–L–E',x,y-8);

 ctx.restore();
}
