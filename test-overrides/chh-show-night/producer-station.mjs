// A quiet track-review corner: plain touring equipment, no generated brand art.
export const producerStation={x:966,y:478,prop:'producer-station'};
export function drawProducerStation(ctx,{x,y}=producerStation){
 ctx.save();ctx.translate(x,y);
 ctx.fillStyle='#04050880';ctx.beginPath();ctx.ellipse(0,0,48,8,0,0,Math.PI*2);ctx.fill();
 // Black road case, metal edging, recessed handles and casters.
 const face=ctx.createLinearGradient(-37,-52,39,0);face.addColorStop(0,'#292b2b');face.addColorStop(.5,'#111315');face.addColorStop(1,'#353536');
 ctx.fillStyle='#090a0c';ctx.fillRect(-36,-58,77,52);
 ctx.fillStyle=face;ctx.fillRect(-36,-52,77,45);
 ctx.fillStyle='#4c4d4d';ctx.beginPath();ctx.moveTo(-41,-64);ctx.lineTo(34,-68);ctx.lineTo(42,-57);ctx.lineTo(-36,-54);ctx.closePath();ctx.fill();
 ctx.strokeStyle='#777774';ctx.lineWidth=1.6;ctx.strokeRect(-36,-53,77,46);
 ctx.strokeStyle='#17191b';ctx.lineWidth=3;ctx.strokeRect(-4,-39,17,6);
 ctx.fillStyle='#a2a19a';for(const cx of [-34,38])for(const cy of [-50,-11])ctx.fillRect(cx-2,cy-2,4,4);
 ctx.fillStyle='#101112';ctx.fillRect(-31,-6,9,6);ctx.fillRect(24,-6,9,6);
 // A laptop with a restrained multitrack view, angled toward Andrew.
 ctx.fillStyle='#91938f';ctx.beginPath();ctx.moveTo(-31,-66);ctx.lineTo(8,-68);ctx.lineTo(16,-61);ctx.lineTo(-26,-59);ctx.closePath();ctx.fill();
 ctx.fillStyle='#181b1e';ctx.beginPath();ctx.moveTo(-33,-97);ctx.lineTo(7,-99);ctx.lineTo(8,-68);ctx.lineTo(-31,-66);ctx.closePath();ctx.fill();
 ctx.strokeStyle='#777d7c';ctx.lineWidth=1;ctx.stroke();
 ctx.fillStyle='#253132';ctx.fillRect(-29,-93,32,21);
 for(let i=0;i<4;i++){
  ctx.fillStyle=['#878d78','#8a6d64','#69848a','#8b8476'][i];
  ctx.fillRect(-26,-90+i*4,11+i*4,2);
 }
 // Headphones and a paper set of track notes on top of the case.
 ctx.strokeStyle='#111315';ctx.lineWidth=3;ctx.beginPath();ctx.arc(24,-67,8,Math.PI,Math.PI*2);ctx.stroke();
 ctx.fillStyle='#060709';ctx.fillRect(14,-70,5,8);ctx.fillRect(29,-70,5,8);
 ctx.fillStyle='#a49d88';ctx.fillRect(15,-61,16,6);ctx.strokeStyle='#555449';ctx.lineWidth=.6;
 for(let i=0;i<3;i++){ctx.beginPath();ctx.moveTo(18,-60+i*1.7);ctx.lineTo(28,-60+i*1.7);ctx.stroke();}
 ctx.fillStyle='#d0c9b7';ctx.textAlign='center';ctx.font='bold 6px monospace';ctx.fillText('ANDREW PRIM',2,-24);
 ctx.font='4.7px monospace';ctx.fillText('PRODUCER / A&R',2,-15);ctx.restore();
}
