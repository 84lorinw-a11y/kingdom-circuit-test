// Front-of-house mix booth: Andrew stands between the rear monitors and the desk.
export const producerStation={x:922,y:535,prop:'producer-station'};
export function drawProducerBack(g){
 g.save();g.fillStyle='#17181b';g.fillRect(844,387,165,144);g.strokeStyle='#555459';g.lineWidth=2;g.strokeRect(844,387,165,144);
 for(const x of [851,984]){g.fillStyle='#08090b';g.fillRect(x,361,22,55);g.strokeStyle='#393a3f';g.strokeRect(x,361,22,55);for(const y of [373,396]){g.fillStyle='#25262b';g.beginPath();g.arc(x+11,y,y===373?4:8,0,7);g.fill();}}
 g.fillStyle='#111216';g.fillRect(875,367,102,18);g.fillStyle='#d8d0bf';g.font='bold 9px monospace';g.textAlign='center';g.fillText('FRONT OF HOUSE',926,380);g.restore();
}
export function drawProducerStation(g,{x,y}=producerStation){
 g.save();g.translate(x,y);
 g.fillStyle='#04050899';g.beginPath();g.ellipse(0,4,94,12,0,0,7);g.fill();
 g.fillStyle='#111216';g.fillRect(-83,-51,170,55);g.strokeStyle='#777775';g.lineWidth=2;g.strokeRect(-83,-51,170,55);
 g.fillStyle='#33363b';g.beginPath();g.moveTo(-83,-51);g.lineTo(-69,-92);g.lineTo(72,-92);g.lineTo(87,-51);g.closePath();g.fill();g.strokeStyle='#757877';g.stroke();
 // Channel strips, meters and faders; eight independent lanes.
 for(let i=0;i<8;i++){const sx=-62+i*12;g.strokeStyle='#111215';g.lineWidth=2;g.beginPath();g.moveTo(sx,-76);g.lineTo(sx,-56);g.stroke();g.fillStyle='#b1afa8';g.fillRect(sx-3,-63-i%3*3,6,3);g.fillStyle=['#9fbd97','#d6b47e','#b1b7cf'][i%3];g.fillRect(sx-2,-88,4,6);g.fillStyle='#141518';g.beginPath();g.arc(sx,-80,2,0,7);g.fill();}
 // DAW display and a smaller cue screen angled toward the engineer.
 for(const [sx,w] of [[-43,56],[23,37]]){g.fillStyle='#0b0e11';g.fillRect(sx,-117,w,29);g.strokeStyle='#7e7e7a';g.lineWidth=1;g.strokeRect(sx,-117,w,29);for(let i=0;i<4;i++){g.fillStyle=['#647e75','#9c8472','#697b91','#858167'][i];g.fillRect(sx+4,-112+i*5,w-9-(i%2)*8,3);}}
 g.fillStyle='#111215';g.fillRect(52,-83,19,28);for(let i=0;i<4;i++){g.fillStyle='#888780';g.fillRect(54,-80+i*6,14,2);g.fillStyle='#91ad8e';g.fillRect(69,-80+i*6,2,2);}
 g.fillStyle='#e4dbca';g.font='bold 13px sans-serif';g.textAlign='center';g.fillText('ANDREW PRIM',2,-29);g.fillStyle='#b7afa1';g.font='8px monospace';g.fillText('MIX / PRODUCE / A&R',2,-13);
 for(const sx of [-80,81]){g.fillStyle='#aaa89f';g.fillRect(sx,-48,4,7);g.fillRect(sx,-8,4,7);}g.restore();
}
