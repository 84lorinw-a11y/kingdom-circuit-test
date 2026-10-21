import {loadImage} from './asset-loader.mjs?v=apollo-25';

export const HOTROD_ARRIVAL_SECONDS=2.4;
export const HOTROD_HEIGHT=640;
const pendingArt=new WeakMap();
// Only called when Gavin's modal opens. Successful artwork survives replays.
export function loadHotrodArt(art,{load=loadImage}={}){
 if(art.hotrodCar&&art.hotrodRoad)return Promise.resolve();
 if(!pendingArt.has(art)){
  const job=Promise.all([['hotrodCar','hotrod-gavin-v1.webp'],['hotrodRoad','hotrod-road-v1.webp']].map(async([key,file])=>{
   if(!art[key])art[key]=await load(new URL(`./assets/${file}`,import.meta.url).href);
  }));
  pendingArt.set(art,job);job.catch(()=>pendingArt.delete(art));
 }
 return pendingArt.get(art);
}
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const ease=v=>v*v*(3-2*v);
const label=(g,value,x,y,size=12,color='#fff0cb')=>{g.font=`700 ${size}px system-ui,sans-serif`;g.textAlign='center';g.fillStyle=color;g.fillText(value,x,y);};
function poly(g,points,color){g.fillStyle=color;g.beginPath();points.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath();g.fill();}
function rounded(g,x,y,w,h,r,fill,stroke){g.beginPath();g.roundRect(x,y,w,h,r);g.fillStyle=fill;g.fill();if(stroke){g.strokeStyle=stroke;g.lineWidth=1.6;g.stroke();}}
function star(g,x,y,r){const pts=[];for(let i=0;i<10;i++){const a=-Math.PI/2+i*Math.PI/5,s=i%2?r*.46:r;pts.push([x+Math.cos(a)*s,y+Math.sin(a)*s]);}poly(g,pts,'#ffdb78');}
function roadCase(g,x,y,size){
 g.save();g.translate(x,y);g.scale(size,size);
 g.fillStyle='#0008';g.beginPath();g.ellipse(2,22,43,11,0,0,Math.PI*2);g.fill();
 for(const dx of [-26,26])rounded(g,dx-4,13,8,12,3,'#080c10','#4b4d51');
 poly(g,[[-37,-19],[-26,-31],[37,-31],[42,-20]],'#393c40');
 poly(g,[[37,-19],[42,-29],[42,10],[37,19]],'#171b21');
 const metal=g.createLinearGradient(0,-20,0,20);metal.addColorStop(0,'#34383e');metal.addColorStop(.45,'#191e24');metal.addColorStop(1,'#292e34');
 rounded(g,-37,-19,74,38,2,metal,'#aaa8a1');
 g.strokeStyle='#60696e';g.lineWidth=1;g.strokeRect(-31,-13,62,26);
 for(const dx of [-35,28])for(const dy of [-19,12])rounded(g,dx,dy,7,7,1,'#b6b4ae','#6a7075');
 for(const dx of [-23,19])rounded(g,dx,-7,5,10,1,'#a6a6a0','#d5d2c7');
 rounded(g,-10,-3,20,7,2,'#080d12','#737b80');
 g.strokeStyle='#d0c0a0';g.beginPath();g.moveTo(-36,-21);g.lineTo(-26,-30);g.lineTo(36,-30);g.stroke();
 g.restore();
}
function backstagePass(g,x,y,size,time,reduced){
 g.save();g.translate(x,y);g.scale(size,size);g.rotate(reduced?0:Math.sin(time*3)*.07);
 const glow=g.createRadialGradient(0,0,4,0,0,48);glow.addColorStop(0,'#ffc94b5c');glow.addColorStop(1,'#ffb72b00');g.fillStyle=glow;g.fillRect(-48,-48,96,96);
 rounded(g,-21,-30,42,60,4,'#161b20','#ffe299');
 g.fillStyle='#7f7b67';g.fillRect(-6,-25,12,3);star(g,0,-5,12);label(g,'PASS',0,19,11);
 for(let i=0;i<4;i++){const a=time*1.3+i*Math.PI/2,r=35+(i%2)*4;g.fillStyle='#ffdc84';g.fillRect(Math.cos(a)*r,Math.sin(a)*r,2,2);}
 g.restore();
}
export function hotrodArrivalPose(fromX,progress){
 const p=ease(clamp(progress));return {x:fromX+(230-fromX)*p,y:531-300*p,scale:1-.46*p,tilt:Math.sin(p*Math.PI)*(230-fromX)*.001};
}
export function drawHotrod(g,{art,time,state,notes,hits,reduced=false,arrival=null,message=''}){
 const arriving=arrival!==null,boost=!arriving&&state.boost>time;
 g.save();g.fillStyle='#111820';g.fillRect(0,0,420,HOTROD_HEIGHT);
 if(art.hotrodRoad){const img=art.hotrodRoad,w=img.height*420/HOTROD_HEIGHT;g.drawImage(img,(img.width-w)/2,0,w,img.height,0,0,420,HOTROD_HEIGHT);}
 const shade=g.createLinearGradient(0,90,0,HOTROD_HEIGHT);shade.addColorStop(0,'#03101a00');shade.addColorStop(1,'#020c1859');g.fillStyle=shade;g.fillRect(0,90,420,HOTROD_HEIGHT-90);
 // Perspective markings move down the road; the venue stays part of the scene.
 const travel=reduced?0:time*.48+(arriving?arrival*(1-arrival*.5)*.65:0);
 for(let i=0;i<13;i++){
  const z=((i/13+travel)%1),depth=z*z*1.45,y=135+depth*335,depth2=depth+.025+depth*.07;
  g.globalAlpha=.26+z*.55;
  for(const side of [-1,1])poly(g,[[210+side*70*depth-1,y],[210+side*70*depth+1,y],[210+side*70*depth2+2,135+depth2*335],[210+side*70*depth2-2,135+depth2*335]],'#ecdfba');
 }
 g.globalAlpha=1;
 const pose=arriving?hotrodArrivalPose(state.x,arrival):{x:state.x,y:531,scale:1,tilt:reduced?0:clamp((state.targetX-state.x)*.0011,-.13,.13)};
 // Two warm headlight pools are cheap canvas gradients, not extra media files.
 g.save();g.translate(pose.x,pose.y);g.rotate(pose.tilt);g.scale(pose.scale,pose.scale);
 for(const side of [-1,1]){
  const light=g.createLinearGradient(0,-75,0,-235);light.addColorStop(0,'#ffe4a870');light.addColorStop(1,'#eac46b00');
  poly(g,[[side*34-5,-72],[side*34+5,-72],[side*34+34,-225],[side*34-34,-225]],light);
 }
 g.restore();
 if(!arriving)for(const n of notes){
  if(n.done||time<n.at-3)continue;
  const z=clamp(1-(n.at-time)/3),depth=z*z,scale=.18+depth*.82,y=135+depth*335;
  for(let lane=0;lane<3;lane++){
   const x=210+(lane-1)*140*depth;
   if(lane===n.lane%3)backstagePass(g,x,y,scale,time,reduced);else roadCase(g,x,y,scale);
  }
 }
 g.save();g.translate(pose.x,pose.y);g.rotate(pose.tilt);g.scale(pose.scale,pose.scale);
 g.fillStyle='#0007';g.beginPath();g.ellipse(0,20,61,78,0,0,Math.PI*2);g.fill();
 if(boost&&!reduced){for(const dx of [-22,22]){const fire=g.createLinearGradient(0,67,0,105);fire.addColorStop(0,'#ffe6b8c0');fire.addColorStop(1,'#f5892800');poly(g,[[dx-4,65],[dx+4,65],[dx+7,97+Math.sin(time*24)*6],[dx-7,97]],fire);}}
 if(art.hotrodCar)g.drawImage(art.hotrodCar,-64,-92,128,192);
 g.restore();
 // Collected passes turn into a short gold ring; a miss gives one soft red edge.
 if(!arriving){const recent=notes.findLast(n=>n.done&&time-n.resolvedAt<.48);if(recent){const age=clamp((time-recent.resolvedAt)/.48);g.globalAlpha=1-age;
  if(recent.hit){g.strokeStyle='#ffdd85';g.lineWidth=2;g.beginPath();g.ellipse(state.x,446,22+age*32,10+age*16,0,0,Math.PI*2);g.stroke();label(g,'+ PASS',state.x,412-age*14,11);}
  else{g.fillStyle='#f05b3b28';g.fillRect(0,0,7,HOTROD_HEIGHT);g.fillRect(413,0,7,HOTROD_HEIGHT);}g.globalAlpha=1;
 }}
 rounded(g,132,9,156,24,5,'#08121cce','#d2b67688');label(g,arriving?'MADE IT TO THE SHOW':`${hits} / 20 BACKSTAGE PASSES`,210,25,10);
 if(arriving&&arrival>.78){rounded(g,98,292,224,39,6,'#08121ced','#dabf7a');label(g,'GAVIN HAS ARRIVED',210,316,15);}
 else if(boost||message){rounded(g,98,43,224,26,5,'#08121ce8');label(g,boost?'CREW HYPED · KEEP IT GOING':message,210,61,11,boost?'#ffda7f':'#fff0cb');}
 g.restore();
}
