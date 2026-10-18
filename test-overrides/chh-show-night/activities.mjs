import {drawPerson} from './sprites.mjs';

const teeNames={cream:'JESUS IS KING',mint:'ALL FOR THE KING',black:'KINGDOM CIRCUIT'};
const make=(tag,cls,text)=>{const el=document.createElement(tag);if(cls)el.className=cls;if(text)el.textContent=text;return el;};
const button=(label,fn,cls='')=>{const b=make('button',cls,label);b.type='button';b.onclick=fn;return b;};

// Each activity owns its timers/listeners. Closing the room cancels it without a reward.
export function mountMerch(host,{owned=null,onFinish=()=>{},onCue=()=>{}}={}){
 let selected=owned||'cream',phase='browse',packed=0,started=0,raf=0,timer=0,disposed=false,busy=false,x=8;
 host.className='activity merch-activity';
 const status=make('p','activity-status');status.setAttribute('aria-live','polite');
 const shirts=make('div','shirts');
 const choice=make('p','activity-caption');
 const primary=button('PACK MY TOTE →',begin);
 const arena=make('div','merch-arena');arena.hidden=true;
 const token=make('div','merch-token');
 const bag=make('div','merch-tote','@thekingdomcircuit');bag.setAttribute('aria-hidden','true');
 const bagLabel=make('span','bag-label','DROP ZONE');arena.append(token,bag,bagLabel);
 const progress=make('div','activity-progress');
 const items=['SHIRT 1','SHIRT 2','SHIRT 3'];
 for(const color of Object.keys(teeNames)){
  const b=button('',()=>{selected=color;updateChoice();});b.dataset.shirt=color;
  const icon=make('span',`shirt-icon ${color}`);icon.setAttribute('aria-hidden','true');icon.append(make('span','',teeNames[color]));
  b.append(icon,make('strong','',teeNames[color]),make('small','',`${color.toUpperCase()} · 10 COINS`));
  b.setAttribute('aria-label',`${teeNames[color]} tee`);b.disabled=!!owned&&color!==owned;shirts.append(b);
 }
 function updateChoice(){shirts.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.shirt===selected));choice.textContent=owned?'Your tee is already yours. Pack another tote for fun—free.':`${teeNames[selected]} · 10 game coins. Help pack three shirts to earn your tee.`;}
 function render(time){
  if(disposed||phase!=='pack')return;
  if(!busy){x=50-42*Math.cos((time-started)/3200*Math.PI*2);token.style.left=`${x}%`;const ready=Math.abs(x-50)<=14;arena.classList.toggle('ready',ready);primary.textContent=ready?'DROP NOW!':'DROP SHIRT';}
  raf=requestAnimationFrame(render);
 }
 function begin(){
  if(phase==='done'){if(disposed)return;disposed=true;onFinish(selected);return;}
  if(phase==='pack'){drop();return;}
  phase='pack';shirts.hidden=true;choice.hidden=true;arena.hidden=false;started=performance.now();
  status.textContent='Drop all 3 shirts into the tote. Space, E, or the button. Misses are free retries.';updateProgress();raf=requestAnimationFrame(render);primary.focus();
 }
 function updateProgress(){
  progress.textContent=`IN THE BAG · ${packed} / 3`;token.replaceChildren();token.setAttribute('aria-label',items[packed]||'Bag complete');
  if(packed<3){const tee=make('span',`drop-tee ${selected}`);tee.append(make('span','',teeNames[selected]));token.append(tee);}
  else token.append(make('span','drop-complete','✓'));
 }

 function drop(){
  if(phase!=='pack'||busy||disposed)return;busy=true;const hit=Math.abs(x-50)<=14;
  token.classList.add(hit?'landed':'missed');primary.disabled=true;
  status.textContent=hit?`${items[packed]} in the bag!`:'Off the edge! Same shirt—try again.';if(hit)onCue();
  timer=setTimeout(()=>{if(disposed)return;token.classList.remove('landed','missed');busy=false;primary.disabled=false;
   if(hit)packed++;updateProgress();
   if(packed===3){phase='done';cancelAnimationFrame(raf);arena.classList.add('complete');status.textContent='BAG SECURED. Ready to rep the movement?';primary.textContent=owned?'NICE CATCH · BACK TO THE SHOW':'TAKE MY BAG · 10 COINS';}
   else{started=performance.now();x=8;}
  },350);
 }
 const keyboard=e=>{if(phase!=='pack'||e.repeat||![' ','e','E'].includes(e.key))return;if(e.target.closest('button')&&e.target!==primary)return;e.preventDefault();e.stopImmediatePropagation();drop();};
 document.addEventListener('keydown',keyboard,true);
 status.textContent='Pick your message, then toss your haul into the tote.';
 host.append(status,shirts,choice,arena,progress,primary);updateChoice();
 return()=>{disposed=true;cancelAnimationFrame(raf);clearTimeout(timer);document.removeEventListener('keydown',keyboard,true);};
}

export const photoFrames={gold:'#fff1d7',mint:'#bcebd6',rose:'#efc1c1'};
export function drawPhotoLineup(g,{avatar='player',pose='classic',x=335,y=610,spacing=107,scale=3.4}={}){
 const lineup=['jay',avatar,'mc','dj','singer','grace'];
 lineup.forEach((person,i)=>drawPerson(g,x+i*spacing,y,person,{scale,lean:pose==='lean'?(i<3?.07:-.07):0}));
}
export function mountPhotoStyle(host,{avatar='player',style={pose:'classic',frame:'gold'},onChange=()=>{}}={}){
 host.className='activity photo-style';let selected={...style};
 const preview=make('canvas','pose-preview');preview.width=480;preview.height=210;preview.setAttribute('role','img');preview.setAttribute('aria-label','Live preview of your crew pose and photo frame.');const g=preview.getContext('2d');
 const render=()=>{g.fillStyle=photoFrames[selected.frame];g.fillRect(0,0,480,210);g.fillStyle='#101e32';g.fillRect(10,10,460,190);g.imageSmoothingEnabled=false;g.fillStyle='#fff2db';g.font='bold 13px monospace';g.textAlign='center';g.fillText('YOUR CREW. ALL FOR THE KING.',240,35);drawPhotoLineup(g,{avatar,pose:selected.pose,x:80,y:186,spacing:64,scale:2.3});};
 host.append(preview);
 for(const [key,label,options] of [['pose','PICK YOUR POSE',{classic:'CLASSIC',lean:'LEAN IN'}],['frame','PICK YOUR FRAME',{gold:'GOLD',mint:'MINT',rose:'ROSE'}]]){
  const group=make('div','photo-options');group.setAttribute('role','group');group.setAttribute('aria-label',label);host.append(make('p','activity-caption',label),group);
  for(const [value,text] of Object.entries(options)){const b=button(text,()=>{selected[key]=value;group.querySelectorAll('button').forEach(el=>el.setAttribute('aria-pressed',el===b));render();onChange({...selected});});b.setAttribute('aria-pressed',selected[key]===value);group.append(b);}
 }
 render();return()=>{};
}
