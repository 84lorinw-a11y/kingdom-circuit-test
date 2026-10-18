import {drawPerson} from './sprites.mjs?v=save-28';

const make=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(text)el.textContent=text;return el;};
const button=(label,fn,cls='')=>{const b=make('button',cls,label);b.type='button';b.onclick=fn;return b;};
export const photoFrames={gold:'#fff1d7',mint:'#bcebd6',rose:'#efc1c1'};
export function drawPhotoLineup(g,{avatar='player',pose='classic',x=335,y=610,spacing=107,scale=3.4}={}){
 const lineup=['jay',avatar,'mc','dj','singer','grace'];
 lineup.forEach((person,i)=>drawPerson(g,x+i*spacing,y,person,{scale,peace:pose==='peace',lean:pose==='lean'?(i<3?.07:-.07):0}));
}
// One camera composition for the live preview and the saved memory.
export function drawVipPhoto(g,{backdrop,avatar='player',pose='classic',x=0,y=0,width=480,height=414}={}){
 const crop={x:460,y:45,width:640,height:552},zoom=Math.min(width/crop.width,height/crop.height);
 g.save();g.beginPath();g.rect(x,y,width,height);g.clip();
 g.translate(x+(width-crop.width*zoom)/2-crop.x*zoom,y+(height-crop.height*zoom)/2-crop.y*zoom);g.scale(zoom,zoom);
 if(backdrop)g.drawImage(backdrop,0,0,1536,1024);
 drawPhotoLineup(g,{avatar,pose,x:585,y:570,spacing:76,scale:5.15});g.restore();
}
export function mountPhotoStyle(host,{avatar='player',backdrop,style={pose:'classic',frame:'gold'},onChange=()=>{}}={}){
 host.className='activity photo-style';let selected={...style};
 const preview=make('canvas','pose-preview');preview.width=480;preview.height=416;preview.setAttribute('role','img');preview.setAttribute('aria-label','Live preview of your crew pose and photo frame.');const g=preview.getContext('2d');
 const render=()=>{g.fillStyle=photoFrames[selected.frame];g.fillRect(0,0,480,416);g.imageSmoothingEnabled=true;
  drawVipPhoto(g,{backdrop,avatar,pose:selected.pose,x:8,y:8,width:464,height:400});};
 host.append(preview);
 for(const [key,label,options] of [['pose','PICK YOUR POSE',{classic:'CLASSIC',lean:'LEAN IN',peace:'PEACE SIGN'}],['frame','PICK YOUR FRAME',{gold:'GOLD',mint:'MINT',rose:'ROSE'}]]){
  const group=make('div','photo-options');group.setAttribute('role','group');group.setAttribute('aria-label',label);host.append(make('p','activity-caption',label),group);
  for(const [value,text] of Object.entries(options)){const b=button(text,()=>{selected[key]=value;group.querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',el===b));render();onChange({...selected});});b.setAttribute('aria-pressed',selected[key]===value);group.append(b);}
 }
 render();return()=>{};
}
