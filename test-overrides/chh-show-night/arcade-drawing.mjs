export function label(g,s,x,y,size=12,color='#f5e4c7'){g.fillStyle=color;g.font=`700 ${size}px system-ui,sans-serif`;g.textAlign='center';g.fillText(s,x,y);}
export function panel(g,x,y,w,h,r=5,color='#14262ce0',stroke='#ddbd7b66'){g.beginPath();g.roundRect(x,y,w,h,r);g.fillStyle=color;g.fill();if(stroke){g.strokeStyle=stroke;g.lineWidth=1;g.stroke();}}
export function poly(g,points,color){g.fillStyle=color;g.beginPath();points.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath();g.fill();}
export function glow(g,x,y,r,color='#f5c97160'){const a=g.createRadialGradient(x,y,0,x,y,r);a.addColorStop(0,color);a.addColorStop(1,color.slice(0,7)+'00');g.fillStyle=a;g.fillRect(x-r,y-r,r*2,r*2);}
export function background(g,art,key,height=560){g.fillStyle='#11202b';g.fillRect(0,0,420,height);if(art['arcade_'+key])g.drawImage(art['arcade_'+key],0,0,420,height);}
export function logo(g,art,x,y,w){if(art.eliBanner){const h=w*art.eliBanner.height/art.eliBanner.width;g.drawImage(art.eliBanner,x-w/2,y-h/2,w,h);}}
export function caseBox(g,x,y,w=100,h=22,accent='#a7b4ba'){
 g.save();g.shadowColor='#0009';g.shadowBlur=5;g.shadowOffsetY=4;
 const metal=g.createLinearGradient(0,y,0,y+h);metal.addColorStop(0,'#55616a');metal.addColorStop(.2,'#1e2932');metal.addColorStop(1,'#101c23');
 panel(g,x-w/2,y,w,h,3,metal,accent);g.shadowBlur=0;g.shadowOffsetY=0;
 for(const dx of [-w/2+3,w/2-9]){g.fillStyle='#c0bbb0';g.fillRect(x+dx,y+3,6,5);g.fillRect(x+dx,y+h-8,6,5);}
 panel(g,x-11,y+h/2-3,22,6,2,'#0b1116','#677580');
 g.strokeStyle='#95a5ac44';g.beginPath();g.moveTo(x-w/2+13,y+5);g.lineTo(x+w/2-13,y+5);g.stroke();g.restore();
}
export function pass(g,x,y,scale=1,time=0,reduced=false){
 g.save();g.translate(x,y);g.scale(scale,scale);g.rotate(reduced?0:Math.sin(time*3)*.06);glow(g,0,0,37);
 panel(g,-19,-28,38,54,4,'#16232c','#e5cb8f');g.fillStyle='#b0ad9e';g.fillRect(-6,-23,12,3);
 label(g,'★',0,3,22,'#f2cc76');label(g,'PASS',0,19,9);g.restore();
}
export function musicNote(g,x,y,size=1,color='#f6d17e'){
 g.save();g.translate(x,y);g.scale(size,size);glow(g,0,0,25,color+'55');
 g.strokeStyle=color;g.lineWidth=4;g.beginPath();g.moveTo(-4,10);g.lineTo(-4,-12);g.lineTo(12,-16);g.lineTo(12,5);g.stroke();
 g.fillStyle=color;for(const [x,y] of [[-9,12],[7,7]]){g.beginPath();g.ellipse(x,y,7,4,-.3,0,7);g.fill();}g.restore();
}
export function cassette(g,x,y,kind=0,scale=1){
 g.save();g.translate(x,y);g.scale(scale,scale);
 panel(g,-40,-26,80,52,5,['#476a61','#59617e','#896954','#805c6c','#717c58'][kind],'#d9ccb1');
 panel(g,-33,-20,66,24,3,'#e1d5b5','#a99771');label(g,['DRUMS','VOCALS','MIX','COVER','MASTER'][kind],0,-9,8,'#344048');
 panel(g,-29,0,58,14,2,'#122129','#80958c');
 for(const dx of [-18,18]){g.fillStyle='#e2d9c4';g.beginPath();g.arc(dx,7,7,0,7);g.fill();g.fillStyle='#22303b';g.beginPath();g.arc(dx,7,3,0,7);g.fill();}
 poly(g,[[-21,25],[-17,17],[17,17],[21,25]],'#273740');for(const dx of [-35,35])for(const dy of [-21,20]){g.fillStyle='#b8b0a1';g.fillRect(dx,dy,2,2);}g.restore();
}
export function recentFeedback(g,notes,time,reduced,height=560){
 const n=notes.findLast(n=>n.done&&Number.isFinite(n.resolvedAt)&&time-n.resolvedAt<.45);if(!n)return;
 const life=1-(time-n.resolvedAt)/.45,hit=n.hit??!n.rejected;g.save();g.globalAlpha=life*.6;g.fillStyle=hit?'#a4d5ad':'#ec9273';g.fillRect(0,82,3,height-82);g.fillRect(417,82,3,height-82);g.restore();
}
