import {drawPerson} from './sprites.mjs?v=apollo-03';
import {photoLineup} from './apollo-crew.mjs?v=apollo-03';
import {drawRoomArtwork} from './venue-art.mjs?v=apollo-03';

const make=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(text)el.textContent=text;return el;};
const button=(label,fn,cls='')=>{const b=make('button',cls,label);b.type='button';b.onclick=fn;return b;};
export const photoFrames={gold:'#fff1d7',mint:'#bcebd6',rose:'#efc1c1'};
export function drawPhotoLineup(g,{avatar='player',pose='classic'}={}){
 photoLineup(avatar).forEach(p=>drawPerson(g,p.x,p.y,p.who,{scale:p.scale,peace:pose==='peace',lean:pose==='lean'?(p.x<765?.04:-.04):0}));
}
// One camera composition for the live preview and the saved memory.
export function drawVipPhoto(g,{backdrop,artwork={},avatar='player',pose='classic',x=0,y=0,width=480,height=265}={}){
 const crop={x:80,y:60,width:1376,height:760},zoom=Math.min(width/crop.width,height/crop.height);
 g.save();g.beginPath();g.rect(x,y,width,height);g.clip();
 g.translate(x+(width-crop.width*zoom)/2-crop.x*zoom,y+(height-crop.height*zoom)/2-crop.y*zoom);g.scale(zoom,zoom);
 // Reframe the same lounge around its open floor, keeping the sofa outside the lineup.
 g.save();g.translate(-430,-60);g.scale(1.35,1.35);
 if(backdrop)g.drawImage(backdrop,0,0,1536,1024);
 g.save();g.scale(1.5,1.5);drawRoomArtwork(g,'vip',artwork);g.restore();g.restore();
 drawPhotoLineup(g,{avatar,pose});g.restore();
}
export function mountPhotoStyle(host,{avatar='player',backdrop,artwork,style={pose:'classic',frame:'gold'},onChange=()=>{}}={}){
 host.className='activity photo-style';let selected={...style};
 const preview=make('canvas','pose-preview');preview.width=480;preview.height=280;preview.setAttribute('role','img');preview.setAttribute('aria-label','Live preview of your crew pose and photo frame.');const g=preview.getContext('2d');
 const render=()=>{g.fillStyle=photoFrames[selected.frame];g.fillRect(0,0,480,280);g.imageSmoothingEnabled=true;
  drawVipPhoto(g,{backdrop,artwork,avatar,pose:selected.pose,x:8,y:8,width:464,height:256});};
 host.append(preview);
 for(const [key,label,options] of [['pose','PICK YOUR POSE',{classic:'CLASSIC',lean:'LEAN IN',peace:'PEACE SIGN'}],['frame','PICK YOUR FRAME',{gold:'GOLD',mint:'MINT',rose:'ROSE'}]]){
  const group=make('div','photo-options');group.setAttribute('role','group');group.setAttribute('aria-label',label);host.append(make('p','activity-caption',label),group);
  for(const [value,text] of Object.entries(options)){const b=button(text,()=>{selected[key]=value;group.querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',el===b));render();onChange({...selected});});b.setAttribute('aria-pressed',selected[key]===value);group.append(b);}
 }
 render();return()=>{};
}
