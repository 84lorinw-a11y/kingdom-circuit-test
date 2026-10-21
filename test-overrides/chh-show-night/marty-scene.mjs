import {loadImage} from './asset-loader.mjs?v=apollo-25';
import {drawPerson} from './sprites.mjs?v=apollo-25';
import {apolloCrew} from './apollo-crew.mjs?v=apollo-25';

export const MARTY_HEIGHT=640;
export const martyRowY=n=>325+n.id%3*110;
const pendingArt=new WeakMap();
// This image is fetched only when Marty's game opens, and reused on replay.
export function loadMartyArt(art,{load=loadImage}={}){
 if(art.martyStudio)return Promise.resolve();
 if(!pendingArt.has(art)){
  const job=load(new URL('./assets/marty-studio-v1.webp',import.meta.url).href).then(image=>{art.martyStudio=image;});
  pendingArt.set(art,job);job.catch(()=>pendingArt.delete(art));
 }
 return pendingArt.get(art);
}
const clamp=n=>Math.max(0,Math.min(1,n));
const label=(g,value,x,y,size=12,color='#f9e8c4')=>{g.font=`700 ${size}px system-ui,sans-serif`;g.textAlign='center';g.fillStyle=color;g.fillText(value,x,y);};
function rounded(g,x,y,w,h,r,fill,stroke){g.beginPath();g.roundRect(x,y,w,h,r);g.fillStyle=fill;g.fill();if(stroke){g.strokeStyle=stroke;g.lineWidth=1;g.stroke();}}
function inkStamp(g,x,y,scale=1){
 g.save();g.translate(x,y);g.rotate(-.14);g.scale(scale,scale);
 g.strokeStyle='#a52d22';g.lineWidth=3;g.strokeRect(-59,-20,118,40);g.lineWidth=1;g.strokeRect(-55,-16,110,32);
 label(g,'NOT FOR SALE',0,5,12,'#a52d22');
 // A few gaps give the ink a rubber-stamp texture without another image.
 g.fillStyle='#eadcbf';for(const [x,y] of [[-48,-20],[28,17],[-12,-20],[54,9]])g.fillRect(x,y,4,2);
 g.restore();
}
const offers=['$10 MILLION','PRIVATE ISLAND','UNLIMITED SNACKS','YOUR OWN JET','A GOLDEN DESK','100% CONTROL'];
function contract(g,n,stamped){
 g.shadowColor='#12090088';g.shadowBlur=7;g.shadowOffsetY=4;
 rounded(g,-59,-40,118,80,3,'#eadcbf');g.shadowBlur=0;g.shadowOffsetY=0;
 rounded(g,-55,-36,110,17,2,'#83392e');label(g,'BUYOUT OFFER',0,-24,9,'#fff1db');
 label(g,offers[Math.floor(n.id/3)%offers.length],0,-2,11,'#382b23');
 g.strokeStyle='#a2907288';g.lineWidth=.6;g.beginPath();g.moveTo(-47,8);g.lineTo(47,8);g.stroke();
 label(g,'THEY OWN APOLLO',0,20,8,'#6a4c3c');
 if(!stamped)label(g,'TAP TO REJECT',0,33,8,'#8e3428');
}
function crewPass(g,n){
 rounded(g,-59,-40,118,80,5,'#193f35','#9bb99a');
 rounded(g,-49,-25,35,53,3,'#cad1b6');
 g.save();g.beginPath();g.rect(-49,-25,35,53);g.clip();
 drawPerson(g,-31,91,apolloCrew[Math.floor(n.id/5)+1].id,{scale:2.1});g.restore();
 g.fillStyle='#c9c7ad';g.fillRect(-8,-34,16,3);
 label(g,'CREW',23,-7,13,'#e7ecd0');label(g,'ALL ACCESS',23,6,7,'#b5ccb3');
 label(g,'LET PASS →',23,26,8,'#d8edbd');
}
function musicSleeve(g,time,reduced){
 rounded(g,-59,-40,118,80,4,'#17333e','#85b3bd');
 g.fillStyle='#070e14';g.beginPath();g.arc(-28,-3,24,0,Math.PI*2);g.fill();
 for(const radius of [16,20]){g.strokeStyle='#75869255';g.lineWidth=1;g.beginPath();g.arc(-28,-3,radius,0,Math.PI*2);g.stroke();}
 g.save();g.translate(-28,-3);g.rotate(reduced?0:time*.6);g.fillStyle='#e6aa64';g.beginPath();g.arc(0,0,8,0,Math.PI*2);g.fill();g.fillStyle='#142430';g.fillRect(-1,-5,2,10);g.restore();
 label(g,'NEW',26,-13,10,'#c3dfe0');label(g,'MUSIC',26,2,11,'#c3dfe0');label(g,'LET PASS →',0,30,8,'#b5e1d0');
}
export function drawMarty(g,{art,time,state,notes,hits,reduced=false,message='',itemX,offerKind}){
 g.save();g.fillStyle='#39261d';g.fillRect(0,0,420,MARTY_HEIGHT);
 if(art.martyStudio)g.drawImage(art.martyStudio,0,0,420,MARTY_HEIGHT);
 // Use Eli's real logo, preserving its proportions on the studio wall plaque.
 if(art.eliBanner){const logo=art.eliBanner,w=120,h=w*logo.height/logo.width;g.drawImage(logo,29,46-h/2,w,h);}
 const shade=g.createLinearGradient(0,245,0,640);shade.addColorStop(0,'#180d0922');shade.addColorStop(1,'#180d0966');g.fillStyle=shade;g.fillRect(0,245,420,395);
 rounded(g,12,245,396,29,5,'#24180ed9','#c6a27480');
 label(g,'TAP BUYOUTS',88,264,10,'#f3be9a');label(g,'LET CREW + MUSIC PASS →',280,264,10,'#c5dfba');
 for(let row=0;row<3;row++){
  const y=325+row*110;
  rounded(g,10,y-47,400,94,8,'#21150d39','#ddb78b25');
  g.setLineDash([3,8]);g.strokeStyle='#f5d4a629';g.lineWidth=1;g.beginPath();g.moveTo(22,y);g.lineTo(370,y);g.stroke();g.setLineDash([]);
  label(g,String(row+1),24,y+35,9,'#e7c79570');label(g,'→',385,y+6,20,'#b5ceb28a');
 }
 // Rejected contracts form a small physical pile at the edge of the desk.
 for(let i=0;i<Math.min(7,state.pile);i++){
  g.save();g.translate(45+i*2,611-i*2);g.rotate((i%3-1)*.09);rounded(g,-24,-13,48,26,1,'#c4b291','#8d7356');label(g,'REJECTED',0,3,6,'#8b3525');g.restore();
 }
 label(g,`${state.pile} REJECTED`,106,619,9,'#e9cca4');
 label(g,`${hits} / 20 GOOD CALLS`,310,619,10,'#e5d3ae');
 for(const n of notes){
  const kind=offerKind(n),age=time-n.resolvedAt;
  if(time<n.at-3)continue;
  if(n.done&&!(n.hit&&kind==='offer'&&age<.9))continue;
  let x=itemX(n,n.done?n.resolvedAt:time),y=martyRowY(n),scale=1,tilt=0;
  if(x<-65||x>425)continue;
  if(n.done&&!reduced&&age>.28){const p=clamp((age-.28)/.62),ease=p*p;x+=(48-x)*ease;y+=(604-y)*ease;scale=1-.65*ease;tilt=-p*.28;}
  g.save();g.translate(x,y);g.rotate(tilt);g.scale(scale,scale);
  if(n.done&&reduced)g.globalAlpha=clamp(1-age/.9);
  if(kind==='offer'){
   contract(g,n,n.done);
   if(n.done){const pop=reduced?1:1+.3*(1-clamp(age/.15));inkStamp(g,0,6,pop);}
  }else if(kind==='crew')crewPass(g,n);else musicSleeve(g,time,reduced);
  g.restore();
 }
 // Feedback sits below Marty, above the active desk, so it never hides a card.
 if(message){
  const success=message==='NOT FOR SALE!'||message==='WELCOME TO APOLLO';
  rounded(g,81,209,258,27,5,'#111914ef',success?'#bcd39588':'#eea38288');label(g,message,210,227,11,success?'#ddedc3':'#ffc3a5');
 }
 const recent=notes.findLast(n=>n.done&&time-n.resolvedAt<.45);
 if(recent&&!(recent.hit&&offerKind(recent)==='offer')){
  g.globalAlpha=.6*(1-clamp((time-recent.resolvedAt)/.45));g.fillStyle=recent.hit?'#b8e7a3':'#fa865f';g.fillRect(recent.hit?414:0,282,6,310);g.globalAlpha=1;
 }
 g.restore();
}
