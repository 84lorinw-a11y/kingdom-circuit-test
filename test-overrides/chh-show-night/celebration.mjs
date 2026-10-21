import {MAX_SCORE} from './state.mjs?v=apollo-23';
export function createCelebration({reduceMotion=false}={}){
 const layer=document.createElement('div');layer.id='celebration';layer.setAttribute('popover','manual');
 const canvas=document.createElement('canvas');canvas.setAttribute('aria-hidden','true');
 const message=document.createElement('div');message.className='victory-message';message.setAttribute('role','status');
 message.innerHTML=`<small>SHOW NIGHT MILESTONE</small><strong>KEEP SHINING.</strong><span>ALL GLORY TO JESUS.</span><p>Your crew. Your music. Your VIP memory.</p>`;
 layer.append(canvas,message);document.body.append(layer);const ctx=canvas.getContext('2d');
 let raf=0,timer=0,started=0,previous=0,nextLaunch=0,sparks=[],rockets=[];
 const colors=['#ffcd6e','#78e1be','#ffa49b','#d7b6ff','#f9f1d6'];
 function close(){cancelAnimationFrame(raf);clearTimeout(timer);layer.hidePopover?.();layer.classList.remove('celebrating');sparks=[];rockets=[];}
 function explode(x,y,color){
  for(let i=0;i<58;i++){const angle=i/58*Math.PI*2,speed=65+Math.random()*155;sparks.push({x,y,vx:Math.cos(angle)*speed,vy:Math.sin(angle)*speed,life:1.1+Math.random()*.55,color});}
 }
 function draw(time){
  const width=innerWidth,height=innerHeight,dpr=Math.min(devicePixelRatio||1,2);
  if(canvas.width!==Math.round(width*dpr)||canvas.height!==Math.round(height*dpr)){canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);}
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);
  const elapsed=(time-started)/1000,dt=Math.min((time-previous)/1000,.04);previous=time;
  if(elapsed>nextLaunch&&elapsed<4.4){const targetY=height*(.14+Math.random()*.36);rockets.push({x:width*(.12+Math.random()*.76),y:height,targetY,color:colors[Math.floor(Math.random()*colors.length)]});nextLaunch=elapsed+.4;}
  rockets=rockets.filter(r=>{r.y-=height*dt*.95;ctx.strokeStyle=r.color;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(r.x,r.y+18);ctx.lineTo(r.x,r.y);ctx.stroke();if(r.y<=r.targetY){explode(r.x,r.y,r.color);return false;}return true;});
  sparks=sparks.filter(s=>{s.life-=dt;s.x+=s.vx*dt;s.y+=s.vy*dt;s.vy+=65*dt;ctx.globalAlpha=Math.min(1,Math.max(0,s.life));ctx.fillStyle=s.color;ctx.fillRect(s.x,s.y,3,3);return s.life>0;});ctx.globalAlpha=1;
  if(elapsed<6.5)raf=requestAnimationFrame(draw);else close();
 }
 return {
  play(){close();layer.classList.add('celebrating');layer.showPopover?.();started=previous=performance.now();nextLaunch=0;if(reduceMotion)timer=setTimeout(close,6500);else{explode(innerWidth*.2,innerHeight*.38,colors[0]);explode(innerWidth*.8,innerHeight*.34,colors[1]);raf=requestAnimationFrame(draw);}},
  stop:close
 };
}
