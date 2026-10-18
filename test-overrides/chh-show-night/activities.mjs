import {drawPerson} from './sprites.mjs?v=show-12';

const make=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(text)el.textContent=text;return el;};
const button=(label,fn,cls='')=>{const b=make('button',cls,label);b.type='button';b.onclick=fn;return b;};
export const photoFrames={gold:'#fff1d7',mint:'#bcebd6',rose:'#efc1c1'};
export function drawPhotoLineup(g,{avatar='player',pose='classic',x=335,y=610,spacing=107,scale=3.4}={}){
 const lineup=['jay',avatar,'mc','dj','singer','grace'];
 lineup.forEach((person,i)=>drawPerson(g,x+i*spacing,y,person,{scale,lean:pose==='lean'?(i<3?.07:-.07):0}));
}
export function mountPhotoStyle(host,{avatar='player',backdrop,style={pose:'classic',frame:'gold'},onChange=()=>{}}={}){
 host.className='activity photo-style';let selected={...style};
 const preview=make('canvas','pose-preview');preview.width=480;preview.height=300;preview.setAttribute('role','img');preview.setAttribute('aria-label','Live preview of your crew pose and photo frame.');const g=preview.getContext('2d');
 const render=()=>{g.fillStyle=photoFrames[selected.frame];g.fillRect(0,0,480,300);g.imageSmoothingEnabled=true;
  g.save();g.beginPath();g.rect(8,8,464,284);g.clip();const zoom=464/1110;g.translate(8-426*zoom,8);g.scale(zoom,zoom);if(backdrop)g.drawImage(backdrop,0,0,1536,1024);drawPhotoLineup(g,{avatar,pose:selected.pose,x:585,y:570,spacing:76,scale:5.15});g.restore();};
 host.append(preview);
 for(const [key,label,options] of [['pose','PICK YOUR POSE',{classic:'CLASSIC',lean:'LEAN IN'}],['frame','PICK YOUR FRAME',{gold:'GOLD',mint:'MINT',rose:'ROSE'}]]){
  const group=make('div','photo-options');group.setAttribute('role','group');group.setAttribute('aria-label',label);host.append(make('p','activity-caption',label),group);
  for(const [value,text] of Object.entries(options)){const b=button(text,()=>{selected[key]=value;group.querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',el===b));render();onChange({...selected});});b.setAttribute('aria-pressed',selected[key]===value);group.append(b);}
 }
 render();return()=>{};
}
