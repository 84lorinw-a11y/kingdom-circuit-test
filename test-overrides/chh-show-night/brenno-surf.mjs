import {loadImage} from './asset-loader.mjs?v=apollo-25';
import {drawPerson} from './sprites.mjs?v=apollo-25';
import {brennoFan} from './crowds.mjs?v=apollo-25';
import {background,label,panel,glow,logo,caseBox} from './arcade-drawing.mjs?v=apollo-25';

export const SURF_HEIGHT=640,SURF_ARRIVAL_SECONDS=1.4;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),mix=(a,b,p)=>a+(b-a)*p;
const jobs=new WeakMap();
export function loadCrowdSurfArt(art,{load=loadImage}={}){
 if(art.brennoSurfer)return Promise.resolve();
 if(!jobs.has(art)){
  const job=load(new URL('./assets/brenno-crowd-surf-v1.webp',import.meta.url).href).then(img=>{art.brennoSurfer=img;});
  jobs.set(art,job);job.catch(()=>jobs.delete(art));
 }
 return jobs.get(art);
}
export function diveTarget(note){return {x:(note.id+1)*192,y:387+Math.sin(note.id*1.31+note.x*.03)*31};}
export const diveSpeed=note=>note.id<3?112:138+note.id*3+(note.id%3)*7;
export function diveAim(note,elapsed){
 const range=90,speed=diveSpeed(note);
 const phase=(Math.max(0,elapsed)*speed/(range*2))%2;
 return (-range+range*2*(phase<=1?phase:2-phase))*(note.id%2?-1:1);
}
export function diveWindows(note){return note.id<3?{hit:44,clean:18}:note.id<10?{hit:34,clean:13}:{hit:26,clean:9};}
export function divePose(state,time){
 if(!state.flight)return {x:state.x,y:state.y,angle:0,air:0};
 const f=state.flight,p=clamp((time-f.start)/f.duration,0,1),arc=Math.sin(Math.PI*p);
 return {x:mix(f.from.x,f.to.x,p),y:mix(f.from.y,f.to.y,p)-arc*(f.clean?128:108),angle:arc*(f.clean?-.22:.13),air:arc};
}
export function createBrennoRound({notes,seconds=40,onResolve=()=>{}}){
 let t=0,combo=0,hits=0,message='LAND IN GOLD. SEND IT.',messageUntil=4;
 const state={x:0,y:416,camera:-96,index:0,aimStart:.2,flight:null,phase:'aim',complete:false,won:false,failed:false,reason:null,lives:3,cleanLandings:0,rescues:0,lastLanding:null};
 const next=()=>notes[state.index];
 function launch(){
  if(state.phase!=='aim'||t<state.aimStart||!next())return;
  const note=next(),target=diveTarget(note),error=diveAim(note,t-state.aimStart),window=diveWindows(note);
  const hit=Math.abs(error)<=window.hit,clean=Math.abs(error)<=window.clean;
  // One attempt on touch-down. Holding, dragging, or key-repeat cannot score
  // another opportunity while airborne; the landing awards this one once.
  note.attempted=true;note.error=error;
  state.flight={note,from:{x:state.x,y:state.y},to:{x:target.x+error,y:target.y},target,start:t,duration:hit?.68:.94,hit,clean};
  state.phase='air';message=clean?'SEND IT!':hit?'YOU’RE FLYING!':'MISSED THE CROWD!';messageUntil=t+1.1;
 }
 function step(time,dt){
  if(state.complete)return;
  t=Math.min(time,seconds);dt=clamp(dt,0,.05);
  if(state.flight&&t>=state.flight.start+state.flight.duration){
   const f=state.flight,n=f.note;n.done=true;n.hit=f.hit;n.rejected=!f.hit;n.clean=f.hit&&f.clean;n.resolvedAt=t;
   combo=f.hit?combo+1:0;if(f.hit)hits++;if(n.clean)state.cleanLandings++;if(!f.hit){state.rescues++;state.lives--;}
   onResolve(n,f.hit,n.clean);state.lastLanding={x:f.to.x,y:f.to.y,time:t,hit:f.hit,clean:n.clean};
   // The crowd can rescue two misses. The third ends this run.
   state.x=f.target.x;state.y=f.target.y;state.index++;state.flight=null;
   state.failed=state.lives===0;state.reason=state.failed?'misses':null;state.won=!state.failed&&state.index===notes.length;
   state.complete=state.failed||state.won;state.phase=state.failed?'out':state.won?'encore':'aim';state.aimStart=t+.26;
   message=n.clean?combo>=3?`${combo} IN A ROW · CROWD GOES OFF!`:'STUCK IT! +50':f.hit?'NICE LANDING! +40':state.lives?`LIFE LOST · ${state.lives===1?'LAST CHANCE!':state.lives+' LEFT'}`:'THREE MISSES · RUN OVER';messageUntil=t+1.2;
  }
  if(!state.complete&&t>=seconds){state.complete=true;state.failed=true;state.reason='time';state.phase='out';state.flight=null;}
  if(!state.flight)state.camera+=(state.x-96-state.camera)*Math.min(1,dt*12);
 }
 return {
  step,point(type){if(type==='down')launch();},key(key){if(key===' '||key==='Enter')launch();},
  draw(g,{art={},reduced=false,arrival=null}={}){drawCrowdSurf(g,{art,time:t,state,notes,hits,combo,reduced,arrival,message:t<messageUntil?message:''});},
  snapshot:()=>({time:t,combo,hits,...state,notes}),meta:()=>({dives:hits,cleanLandings:state.cleanLandings,rescues:state.rescues,lives:state.lives,outcome:state.won?'won':state.failed?'lost':null,reason:state.reason,delivered:0})
 };
}
function fanGroup(g,x,y,id,active=false,beat=0){
 if(active)glow(g,x,y+28,80,'#efc47942');
 for(let i=0;i<5;i++)drawPerson(g,x+(i-2)*23,y+141+(i%2)*7+beat,brennoFan(id*5+i),{scale:1.95+(i%2)*.18,back:true,hands:true});
}
function flightSprite(g,art,x,y,width,angle=0){
 g.save();g.translate(x,y);g.rotate(angle);
 if(art.brennoSurfer){const height=width*art.brennoSurfer.height/art.brennoSurfer.width;g.drawImage(art.brennoSurfer,-width/2,-height+30,width,height);}
 else {g.rotate(-1.1);drawPerson(g,0,45,'brenno',{scale:2});}g.restore();
}
function arrivalScene(g,{art,arrival,hits,reduced,time}){
 const p=clamp(arrival,0,1),ease=1-(1-p)**3;
 background(g,art,'soundstage',SURF_HEIGHT);logo(g,art,210,83,174);
 panel(g,47,352,326,129,5,'#18252a','#b2a182');caseBox(g,210,457,330,27);
 for(let i=0;i<8;i++)drawPerson(g,18+i*55,593,brennoFan(i+9),{scale:2.2,back:true,hands:true});
 glow(g,210,334,142,'#f6ce7357');
 if(p<.76)flightSprite(g,art,mix(85,210,ease),mix(464,390,ease)-Math.sin(p*Math.PI)*115,190,-Math.sin(p*Math.PI)*.25);
 else drawPerson(g,210,451,'brenno',{scale:4.3,lean:reduced?0:Math.sin(time*3)*.025});
 if(!reduced)for(let i=0;i<32;i++){g.fillStyle=['#f4cf75','#7edbc9','#ed8b69'][i%3];const x=25+(i*73)%370,y=145+((i*41+arrival*180)%390);g.fillRect(x,y,3,7);}
 panel(g,41,166,338,80,8,'#0c202be8','#e3c27a');label(g,hits>=16?'THAT’S A HEADLINER.':'BACK ON STAGE.',210,197,23,'#ffe0a0');label(g,`${hits} DIVES LANDED · THE CROWD’S STILL WITH YOU`,210,226,10,'#bce5db');
}
export function drawCrowdSurf(g,{art,time:t,state:s,notes,hits,combo,reduced,message,arrival}){
 g.save();
 if(arrival!=null){arrivalScene(g,{art,arrival,hits,reduced,time:t});g.restore();return;}
 background(g,art,'soundstage',SURF_HEIGHT);
 const shade=g.createLinearGradient(0,160,0,640);shade.addColorStop(0,'#06152100');shade.addColorStop(1,'#071521bc');g.fillStyle=shade;g.fillRect(0,160,420,480);
 logo(g,art,210,39,116);label(g,'THE FLOOR IS YOURS.',210,82,18,'#ffe1a0');
 for(let i=0;i<20;i++){panel(g,31+i*18,100,13,5,2,i<s.index?(notes[i].hit?'#e5c074':'#596c74'):'#20343e',null);}
 label(g,`${s.index} / 20 DIVES  →  THE STAGE`,210,127,10,'#b7dcd7');
 label(g,`${s.lives} / 3 LIVES  ·  ${s.lives===1?'LAST CHANCE!':'3 MISSES = OUT'}`,210,146,11,s.lives<=1?'#ff977c':'#ffe1a0');
 // Clear landing groups give each jump room to read on a small phone.
 for(let i=0;i<9;i++)drawPerson(g,16+i*50,624,brennoFan(i+18),{scale:1.75,back:true,hands:true,lean:reduced?0:Math.sin(t*2+i)*.018});
 const next=notes[s.index],target=next?diveTarget(next):{x:s.x+192,y:388},tx=target.x-s.camera;
 const currentX=s.x-s.camera,pose=divePose(s,t),bounce=reduced?0:Math.sin(t*3)*1.7;
 if(s.index===0){caseBox(g,currentX,440,147,35);label(g,'BRENNO',currentX,464,10);}
 else fanGroup(g,currentX,s.y,s.index-1,false,bounce);
 fanGroup(g,tx,target.y,s.index,true,-bounce);
 const window=next?diveWindows(next):{hit:44,clean:17};
 if(next){g.strokeStyle='#f7d58b';g.lineWidth=3;g.beginPath();g.ellipse(tx,target.y+30,window.hit,13,0,0,Math.PI*2);g.stroke();label(g,'LAND HERE',tx,target.y+57,10,'#ffdb91');}
 if(next&&s.phase==='aim'){
  const error=diveAim(next,Math.max(0,t-s.aimStart)),aimX=tx+error;
  g.save();g.strokeStyle='#abdcd987';g.lineWidth=2;g.setLineDash([3,8]);g.beginPath();g.moveTo(currentX,s.y-35);g.quadraticCurveTo((currentX+aimX)/2,target.y-205,aimX,target.y+15);g.stroke();g.restore();
  g.fillStyle=Math.abs(error)<=window.hit?'#ffe3a2':'#91b6c2';g.beginPath();g.moveTo(aimX-8,target.y-8);g.lineTo(aimX+8,target.y-8);g.lineTo(aimX,target.y+6);g.closePath();g.fill();
 }
 if(s.phase==='air'){
  if(!reduced){g.strokeStyle='#efcc8a66';g.lineWidth=2;for(let i=1;i<5;i++){g.beginPath();g.moveTo(pose.x-s.camera-70-i*9,pose.y-17+i*6);g.lineTo(pose.x-s.camera-92-i*9,pose.y-17+i*6);g.stroke();}}
  flightSprite(g,art,pose.x-s.camera,pose.y,176+pose.air*12,reduced?0:pose.angle);
 }else if(s.index===0)drawPerson(g,currentX,440,'brenno',{scale:3.1});
 else flightSprite(g,art,currentX,s.y+bounce,176,reduced?0:-.035);
 const landing=s.lastLanding,age=landing?t-landing.time:99;
 if(age<.6){glow(g,landing.x-s.camera,landing.y+25,85,landing.hit?'#eaca785e':'#8fd6ce40');if(!reduced&&landing.hit)for(let i=0;i<9;i++){const a=i*Math.PI*2/9;g.fillStyle='#f7d280';g.fillRect(landing.x-s.camera+Math.cos(a)*age*130,landing.y+Math.sin(a)*age*100,3,5);}}
 panel(g,28,157,364,43,7,'#0e242de8','#a8b9aa55');label(g,message||'TAP WHEN THE ARROW ENTERS GOLD',210,183,12,combo>=3?'#ffdc8c':'#d9ebe5');
 // Meter and landing arrow use the same error as scoring.
 panel(g,25,524,370,99,10,'#0b1c28f2','#dfbe7666');
 if(next){
  const center=210,scale=1.5,error=s.flight?s.flight.note.error:diveAim(next,Math.max(0,t-s.aimStart));
  panel(g,66,547,288,18,6,'#344651',null);panel(g,center-window.hit*scale,547,window.hit*scale*2,18,5,'#cfaa61',null);
  panel(g,center-window.clean*scale,547,window.clean*scale*2,18,4,'#ffe0a0',null);
  const marker=center+error*scale;g.fillStyle='#fff7df';g.beginPath();g.moveTo(marker-6,538);g.lineTo(marker+6,538);g.lineTo(marker,548);g.closePath();g.fill();g.fillRect(marker-1,547,2,20);
 }
 label(g,s.phase==='air'?'AIR TIME!':'TAP TO SEND IT',210,592,19,'#ffe2a0');label(g,`${hits} LANDED  ·  ${combo} STREAK  ·  BRIGHT CENTER = +50`,210,611,9,'#a8d4cf');
 g.restore();
}
