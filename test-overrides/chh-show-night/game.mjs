import {MAX_SCORE,initialState,score,coins,objective,pointsToGo,act,restore} from './state.mjs';
import {drawPerson,loadPeople} from './sprites.mjs';
import {crowdActors,crowdCounts} from './crowds.mjs';
import {createCelebration} from './celebration.mjs';
import {pitPhotographers,drawCameraFlash} from './pit.mjs';
import {avatars,avatarFor,playerName} from './avatars.mjs';
import {mountDjBooth} from './dj-booth.mjs';
import {mountMerch,mountPhotoStyle,drawPhotoLineup,photoFrames} from './activities.mjs';
import {walkable as canWalk,findPath} from './navigation.mjs';
import {practiceSpot,drawPracticeBooth} from './practice-booth.mjs';
import {createWorshipMusic,inFrontRow,stageSpotAt,stageSpots} from './worship.mjs?v=mobile-audio-1';
const $=s=>document.querySelector(s), canvas=$('#world'),ctx=canvas.getContext('2d'),dialog=$('#dialog');
const worshipMusic=createWorshipMusic($('.arcade'));let atFront=null;
const storageKey='kc-show-night-v1', W=1024,H=683;
let state;try{state=restore(localStorage.getItem(storageKey));}catch{state=initialState();}
let stopBeat=null,stopActivity=null;
let keys=new Set(),route=[],autoAction=null,walking=false,frame=0,last=0,camera=0,viewWidth=W,paused=false,raisingUntil=0,photoBusy=false,photoURL=null,toastTimer,introTimer,soundOn=false,audio=null,particles=[],trail=[],followerPositions=[];
const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const celebration=createCelebration({reduceMotion});let victoryPending=false;
const roomInfo={outside:['01','OUTSIDE THE VENUE','BRING YOUR PEOPLE.'],show:['02','THE MAIN STAGE','GOOD MUSIC. GREATER PURPOSE.'],vip:['03','THE VIP LOUNGE','MAKE A MEMORY.']};
const images={};
const safeSave=()=>{try{localStorage.setItem(storageKey,JSON.stringify(state));}catch{}};
function notify(message){$('#toast').textContent=message;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),3600);}
function tone(kind='up'){
 if(!soundOn)return;try{audio??=new (window.AudioContext||window.webkitAudioContext)();audio.resume();const notes=kind==='photo'?[440,554,659,880]:kind==='step'?[180]:[523,659,784];notes.forEach((hz,i)=>{const o=audio.createOscillator(),g=audio.createGain(),t=audio.currentTime+i*.09;o.type='triangle';o.frequency.value=hz;g.gain.setValueAtTime(.045,t);g.gain.exponentialRampToValueAtTime(.001,t+.15);o.connect(g);g.connect(audio.destination);o.start(t);o.stop(t+.16);});}catch{}
}
function burst(x=state.x,y=state.y-60){if(reduceMotion)return;for(let i=0;i<35;i++)particles.push({x,y,vx:(Math.random()-.5)*180,vy:-70-Math.random()*130,life:1.2,color:['#ffc45b','#ff7053','#79d8ae','#c7a0f4'][i%4]});}
function sync(){
 $('#player-tag').textContent=state.name?`${state.name.toUpperCase()} · THAT’S YOU`:'FOLLOW YOUR NAME TAG';
 const n=score(state);$('#xp-value').textContent=n;$('#xp-fill').style.width=`${n/MAX_SCORE*100}%`;$('#xp-meter').setAttribute('aria-valuenow',n);$('#xp-rank').textContent=n===MAX_SCORE?'ALL GLORY TO JESUS.':state.worship?'HANDS HIGH':state.merch?'REPPING THE MOVEMENT':n>=30?'CREW’S ALL HERE':'JUST PULLED UP';
 $('#friends').textContent=`${state.friends.length}/2`;$('#coins').textContent=coins(state);$('#objective').textContent=objective(state);$('#room-name').textContent=`${roomInfo[state.room][0]} / ${roomInfo[state.room][1]}`;
 let activeFound=false;document.querySelectorAll('#checklist li').forEach(li=>{const k=li.dataset.step,done=k==='friends'?state.friends.length===2:!!state[k];li.classList.toggle('done',done);li.classList.toggle('active',!done&&!activeFound);if(!done)activeFound=true;li.querySelector('.step-icon').textContent=done?'✓':String([...li.parentElement.children].indexOf(li)+1).padStart(2,'0');});
 $('#photo-button').hidden=!state.photo;$('#celebrate-button').hidden=n<MAX_SCORE;$('#xp-next').textContent=pointsToGo(state);renderDestinations();safeSave();
}
function apply(action,value){const oldRoom=state.room,oldScore=score(state);state=act(state,action,value);if(state.room!==oldRoom){worshipMusic.leave();atFront=null;raisingUntil=0;route=[];autoAction=null;trail=[];followerPositions=[];announceRoom();}if(score(state)>oldScore){tone();burst();}if(oldScore<MAX_SCORE&&score(state)===MAX_SCORE)victoryPending=true;sync();}
function announceRoom(){const info=roomInfo[state.room];$('#room-intro small').textContent=`CHAPTER ${info[0]}`;$('#room-intro strong').textContent=info[2];$('#room-intro').classList.add('visible');clearTimeout(introTimer);introTimer=setTimeout(()=>$('#room-intro').classList.remove('visible'),1500);}
function hotspots(){
 if(state.room==='outside')return [
 ...(!state.friends.includes('jay')?[{id:'jay',x:210,y:590,label:'Invite Jay',tag:'JAY',action:'invite',value:'jay'}]:[]),
 ...(!state.friends.includes('grace')?[{id:'grace',x:348,y:578,label:'Invite Grace',tag:'GRACE',action:'invite',value:'grace'}]:[]),
 {id:'enter',x:740,y:385,label:'Venue entrance',tag:'THE SHOW',action:'enter'}];
 if(state.room==='show')return [
 {id:'merch',x:105,y:455,label:state.merch?'Merch ✓':'Merch · 10 coins',tag:'MERCH',action:'merch',done:!!state.merch},
 {id:'dj',...practiceSpot,label:'Eli · B–I–B–L–E',tag:'ELI · B–I–B–L–E',action:'dj',done:!!state.eli},
 ...stageSpots.map(p=>({...p,action:'worship',done:state.worship})),
 {id:'vip',x:940,y:447,label:'VIP · open to everyone',tag:'VIP →',action:'vip'},
 {id:'outside',x:75,y:625,label:'← Outside',tag:'EXIT',action:'outside'}];
 return [
 {id:'photo',x:505,y:442,label:state.photo?'Another VIP photo':'Meet the band',tag:'PHOTO SPOT',action:'photo',done:state.photo},
 {id:'show',x:105,y:310,label:'← Main stage',tag:'← SHOW',action:'show'},
 {id:'refresh',x:875,y:410,label:'Refreshments',tag:'TAKE A BREATHER',action:'refresh'}];
}
function renderDestinations(){const wrap=$('#destinations');wrap.replaceChildren();hotspots().forEach(h=>{const b=document.createElement('button');b.textContent=h.label;b.dataset.destination=h.id;b.classList.toggle('done',!!h.done);b.onclick=()=>goTo(h);wrap.append(b);});}
const walkable=(x,y)=>canWalk(state.room,x,y);
function goTo(h){if(photoBusy)return;keys.clear();autoAction=h;route=findPath(state.room,state,h);
 if(!route.length){autoAction=null;notify('Choose a spot on the open floor.');return;}
 notify(`Walking to ${h.label.toLowerCase().replace(' ✓','')}…`);canvas.focus({preventScroll:true});
}
function nearest(limit=83){return hotspots().map(h=>({...h,d:Math.hypot(state.x-h.x,state.y-h.y)})).filter(h=>h.d<limit).sort((a,b)=>a.d-b.d)[0];}
function interactButton(){if(dialog.open||photoBusy)return;const nearby=nearest();if(nearby)interact(nearby);else{const h=nearest(Infinity);if(h)goTo(h);}}
function openDialog(title,body,buttons=[],eyebrow='CHH SHOW NIGHT'){
 route=[];autoAction=null;keys.clear();const content=$('#dialog-content');content.replaceChildren();const over=document.createElement('p');over.className='overline';over.textContent=eyebrow;const heading=document.createElement('h2');heading.textContent=title;const text=document.createElement('p');text.textContent=body;content.append(over,heading,text);const actions=document.createElement('div');actions.className='dialog-actions';buttons.forEach(({label,fn,secondary=false})=>{const b=document.createElement('button');b.textContent=label;if(secondary)b.className='secondary';b.onclick=()=>{dialog.close();fn?.();};actions.append(b);});content.append(actions);if(!dialog.open)dialog.showModal();return content;
}
function interact(h=nearest()){
 if(dialog.open||photoBusy)return;
 if(!h){notify('Click the A button, or use E / Space near a glowing marker.');return;}
 if(h.action==='invite'){
 const isJay=h.value==='jay';openDialog(isJay?'“You know I’m coming!”':'“A show AND the VIP photo? I’m in!”',isJay?'Jay is ready for a night of music and faith. Bring him along!':'Grace wouldn’t miss it. Everything is better with your people.',[{label:isJay?'INVITE JAY · +15 XP':'INVITE GRACE · +15 XP',fn:()=>{apply('invite',h.value);notify(`${isJay?'Jay':'Grace'} joined your crew! +15 XP`);}},{label:'In a minute',secondary:true}],isJay?'MEET JAY':'MEET GRACE');
 }else if(h.action==='enter'){
 if(state.friends.length<2){notify('Bring your people! Invite both Jay and Grace first.');return;}apply('enter');
 }else if(h.action==='merch'){
 openMerch();
 }else if(h.action==='worship'){
 raiseHands(h.id);
 }else if(h.action==='vip'){
 apply('vip');
 }else if(h.action==='dj'){
 openBeatChallenge();
 }else if(h.action==='photo'){
 openPhotoStyle();
 }else if(h.action==='refresh'){
 openDialog('Catch your breath.','Water, snacks, and good company. What a night! Your crew is waiting by the photo backdrop.',[{label:'BACK TO THE NIGHT'}],'VIP LOUNGE');
 }else apply(h.action);
}
function activityHost(content){const host=document.createElement('div');content.insertBefore(host,content.lastElementChild);return host;}
function openMerch(){
 const content=openDialog('Rep the movement.','Pick a tee. Land your haul in the tote. Then get back to the music.',[{label:'BACK TO THE SHOW',secondary:true}],state.merch?'MERCH BOOTH · FREE REPLAY':'MERCH BOOTH · +20 XP');
 stopActivity=mountMerch(activityHost(content),{owned:state.merch,onCue:()=>tone('step'),onFinish:color=>{const owned=!!state.merch;apply('merch',color);dialog.close();notify(owned?'Clean catch! Your original tee and coins stay yours.':'Merch secured! +20 XP. See you up front.');}});
}
function raiseHands(id=stageSpotAt(state)){
 if(!id)return;const done=state.worship;apply('worship');raisingUntil=performance.now()+10000;
 if(atFront!==id){atFront=id;worshipMusic.enter(id);}
 notify(done?'Hands high. All glory to Jesus!':'Hands high. All glory to Jesus! +25 XP.');
}
function openPhotoStyle(){
 const content=openDialog('Make this one yours.','Choose a crew pose and frame. Then we’ll count you in: 3, 2, 1.',[{label:'TAKE THE PHOTO',fn:takePhoto},{label:'Not quite ready',secondary:true}],'VIP PHOTO · YOUR CREW');
 let chosen={...state.photoStyle};
 stopActivity=mountPhotoStyle(activityHost(content),{avatar:avatarFor(state).sprite,style:chosen,onChange:value=>{chosen=value;}});
 content.querySelector('.dialog-actions button').onclick=()=>{apply('photoStyle',chosen);dialog.close();takePhoto();};
}
function openBeatChallenge(){
 worshipMusic.leave();
 const content=openDialog('B–I–B–L–E with Eli',state.eli?'Your +25 XP is earned. Play again to improve your beat score.':'Press Start Game, then tap each letter at the gold line. Finish the round to earn +25 XP.',[{label:'BACK TO THE SHOW',secondary:true}],state.eli?'ELI · +25 XP EARNED':'ELI · +25 SHOW NIGHT XP');
 const exitBar=document.createElement('div');exitBar.className='dj-exit-bar';const exit=document.createElement('button');exit.type='button';exit.className='secondary';exit.textContent='← LEAVE DJ BOOTH';exit.onclick=()=>{stopBeat?.();stopBeat=null;dialog.close();};const hint=document.createElement('span');hint.textContent='LEAVE ANYTIME · ESC';exitBar.append(exit,hint);content.prepend(exitBar);
 const host=document.createElement('div');host.className='dj-booth';content.insertBefore(host,content.lastElementChild);
 stopBeat=mountDjBooth(host,{best:state.beatBest,rewardEarned:state.eli,onFinish:n=>{const earned=state.eli;apply('beat',n);if(!earned)notify('Eli’s set complete! +25 XP.');if(n>=8)burst();},onActivity:()=>{raisingUntil=performance.now()+700;}});
 dialog.scrollTop=0;host.querySelector('.beat-start-buttons button').focus({preventScroll:true});
}
function openPlayerSetup(){
 const content=openDialog(state.profileReady?'Your player. Your vibe.':'Who’s coming to the show?','Choose your character and the name your crew will know you by.',[],'PLAYER SELECT · CHH SHOW NIGHT');
 const form=document.createElement('form');form.className='player-form';
 const nameLabel=document.createElement('label');nameLabel.htmlFor='player-name';nameLabel.textContent='YOUR NAME';
 const input=document.createElement('input');input.id='player-name';input.name='player-name';input.maxLength=18;input.required=true;input.autocomplete='nickname';input.placeholder='Enter your name';input.value=state.name||'';
 let selected=state.avatar||'red';const grid=document.createElement('div');grid.className='avatar-grid';grid.setAttribute('role','group');grid.setAttribute('aria-label','Choose your character');
 avatars.forEach(a=>{const b=document.createElement('button');b.type='button';b.className='avatar-choice';b.dataset.avatar=a.id;b.setAttribute('aria-pressed',a.id===selected);const portrait=document.createElement('canvas');portrait.width=140;portrait.height=180;portrait.setAttribute('aria-hidden','true');const g=portrait.getContext('2d');g.imageSmoothingEnabled=false;drawPerson(g,70,172,a.sprite,{scale:2.7});const label=document.createElement('span');label.textContent=a.label;b.append(portrait,label);b.onclick=()=>{selected=a.id;grid.querySelectorAll('button').forEach(button=>button.setAttribute('aria-pressed',button===b));};grid.append(b);});
 const submit=document.createElement('button');submit.type='submit';submit.className='player-start';submit.textContent=state.profileReady?'SAVE MY PLAYER →':'LET’S MAKE A NIGHT →';
 form.append(nameLabel,input,grid,submit);form.onsubmit=e=>{e.preventDefault();if(!playerName(input.value)){input.setCustomValidity('Enter your name to start.');input.reportValidity();return;}input.setCustomValidity('');apply('profile',{name:input.value,avatar:selected});dialog.close();notify(`Welcome, ${state.name}. Bring your people!`);};input.oninput=()=>input.setCustomValidity('');content.insertBefore(form,content.lastElementChild);if(state.profileReady){const cancel=document.createElement('button');cancel.className='secondary';cancel.textContent='Keep my player';cancel.onclick=()=>dialog.close();content.lastElementChild.append(cancel);}input.focus();
}
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function takePhoto(){
 photoBusy=true;route=[];keys.clear();for(const n of ['3','2','1']){$('#countdown').textContent=n;tone('step');await pause(700);}$('#countdown').textContent='';if(!reduceMotion){$('#flash').classList.remove('firing');void $('#flash').offsetWidth;$('#flash').classList.add('firing');}apply('photo');tone('photo');await pause(200);await showPhoto();photoBusy=false;
}
async function makePhoto(){
 const c=document.createElement('canvas');c.width=1200;c.height=900;const g=c.getContext('2d');g.fillStyle=photoFrames[state.photoStyle.frame];g.fillRect(0,0,1200,900);g.drawImage(images.vip,20,20,1160,770);
 drawPhotoLineup(g,{avatar:avatarFor(state).sprite,pose:state.photoStyle.pose});
 g.fillStyle='#101b2c';g.fillRect(38,692,1124,79);g.textAlign='center';g.fillStyle='#ffc363';g.font='bold 27px monospace';g.fillText('YOUR CREW. YOUR FAITH. YOUR MEMORY.',600,726);g.fillStyle='#e9efed';g.font='16px monospace';g.fillText('KINGDOM CIRCUIT  /  CHH SHOW NIGHT  /  VIP',600,753);
 g.textAlign='left';g.fillStyle='#101b2c';g.font='bold 32px monospace';g.fillText('NIGHT MADE.',42,840);g.font='15px monospace';g.fillText(`JAY + ${(state.name||'YOU').toUpperCase()} + GRACE • BACKSTAGE WITH THE BAND`,42,870);g.textAlign='right';g.font='bold 26px monospace';g.fillText(`${score(state)} / ${MAX_SCORE} XP`,1158,840);g.font='14px monospace';g.fillText('ALL GLORY TO JESUS.',1158,868);
 return new Promise(resolve=>c.toBlob(resolve,'image/png'));
}
async function showPhoto(){
 try{const blob=await makePhoto();if(!blob)throw new Error('Photo unavailable');if(photoURL)URL.revokeObjectURL(photoURL);photoURL=URL.createObjectURL(blob);const content=openDialog('All glory to Jesus.','Your crew, backstage with the band. Keep the memory, then head back out and enjoy the show. All glory to Jesus.',[{label:'KEEP HANGING OUT',secondary:true}],`VIP MEMORY · ${score(state)} SHOW NIGHT XP`);const img=document.createElement('img');img.className='photo-preview';img.src=photoURL;img.alt='Your player and two friends posing with the Steven Malcolm-inspired vocalist, Eli-inspired DJ, and Joz-inspired performer at the VIP backdrop.';content.insertBefore(img,content.lastElementChild);const a=document.createElement('a');a.href=photoURL;a.download='Kingdom-Circuit-CHH-Show-Night-VIP.png';a.textContent='↓ DOWNLOAD PHOTO';const full=document.createElement('a');full.href=photoURL;full.target='_blank';full.rel='noopener';full.className='photo-full';full.textContent='OPEN FULL SIZE';content.lastElementChild.prepend(a,full);}catch{notify('Could not create the photo. Tap Your VIP Photo to try again.');}
}
function label(x,y,text,{active=false,color='#ffca6c'}={}){
 ctx.save();ctx.font='bold 16px monospace';const width=ctx.measureText(text).width+20;ctx.fillStyle=active?'#ffca6c':'#08182bea';ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.fillRect(x-width/2,y-19,width,25);ctx.strokeRect(x-width/2,y-19,width,25);ctx.fillStyle=active?'#101926':'#fff2d8';ctx.textAlign='center';ctx.fillText(text,x,y-2);ctx.restore();
}
function drawBag(x,y){ctx.fillStyle='#0b1625';ctx.fillRect(x+22,y-39,19,26);ctx.fillStyle='#dcaa6a';ctx.fillRect(x+24,y-37,15,22);ctx.strokeStyle='#d9ae73';ctx.lineWidth=3;ctx.strokeRect(x+27,y-43,9,8);ctx.fillStyle='#684825';ctx.save();ctx.translate(x+31.5,y-24);ctx.scale(.12,.3);ctx.font='bold 10px monospace';ctx.textAlign='center';ctx.fillText('@thekingdomcircuit',0,0);ctx.restore();}
function render(time){
 const dt=Math.min((time-last)/1000,.04)||.016;last=time;frame+=dt;
 if(!dialog.open&&!photoBusy&&!paused)update(dt,time);else walking=false;
 const rect=canvas.getBoundingClientRect(),ratio=Math.min(devicePixelRatio||1,2),cw=Math.round(rect.width*ratio),ch=Math.round(rect.height*ratio);
 if(canvas.width!==cw||canvas.height!==ch){canvas.width=cw;canvas.height=ch;}
 viewWidth=H*(rect.width/rect.height);camera=Math.max(0,Math.min(W-viewWidth,state.x-viewWidth/2));if(viewWidth>=W){camera=0;viewWidth=W;}
 ctx.setTransform(canvas.width/viewWidth,0,0,canvas.height/H,-camera*canvas.width/viewWidth,0);ctx.imageSmoothingEnabled=false;
 ctx.clearRect(camera,0,viewWidth,H);ctx.drawImage(images[state.room],0,0,W,H);
 if(state.room==='show'&&!reduceMotion){ctx.save();ctx.globalAlpha=.03+Math.sin(time/800)*.018;ctx.fillStyle='#ffd079';ctx.fillRect(0,0,W,400);ctx.restore();}
 if(state.room==='show'){
  drawPracticeBooth(ctx,time);
  for(const [id,who,x] of [['steven','mc',335],['joz','singer',720]]){const singing=worshipMusic.playing===id;drawPerson(ctx,x,363,who,{scale:2.9,lean:singing&&!reduceMotion?Math.sin(time/240)*.025:0});if(singing)label(x,219,'♪ '+(id==='steven'?'OUTSIDE':'BIRKENSTOCK'),{color:'#7ed9b1'});}
 }
 const target=nearest();
 if(victoryPending&&!photoBusy){victoryPending=false;celebration.play();}
 for(const h of hotspots()){
 const pulse=reduceMotion?0:Math.sin(time/350)*3,stage=state.room==='show'&&['dj','steven','joz'].includes(h.id);
 ctx.strokeStyle=h.done?'#86e2b1':h.id===target?.id?'#ffce67':'#ffe0a4';ctx.lineWidth=stage?3:2;ctx.setLineDash(stage?[]:[6,4]);ctx.beginPath();ctx.ellipse(h.x,h.y,(stage?40:32)+pulse,stage?15:11,0,0,Math.PI*2);ctx.fillStyle=stage?'#08182b70':'#08182b30';ctx.fill();ctx.stroke();ctx.setLineDash([]);
 if(stage){ctx.fillStyle='#ffce67';ctx.beginPath();ctx.moveTo(h.x-9,h.y-33);ctx.lineTo(h.x+9,h.y-33);ctx.lineTo(h.x,h.y-21);ctx.closePath();ctx.fill();}
 }
 const actors=crowdActors(state.room,time,reduceMotion,state);
 if(state.room==='show')actors.push(...pitPhotographers);

 if(state.room==='outside'){
 if(!state.friends.includes('jay'))actors.push({x:210,y:590,who:'jay',npc:true});
 if(!state.friends.includes('grace'))actors.push({x:348,y:578,who:'grace',npc:true});
 }else if(state.room==='vip'){
 [['mc',446],['dj',525],['singer',604]].forEach(([who,x])=>actors.push({x,y:346,who,scale:2.25}));
 }
 const pose=photoBusy,handsHigh=state.room==='show'&&(inFrontRow(state)||time<raisingUntil);actors.push({x:pose?480:state.x,y:pose?382:state.y,who:avatarFor(state).sprite,player:true,hands:handsHigh,back:handsHigh,walking});
 state.friends.forEach((who,i)=>{const p=followerPositions[i]||{x:state.x-50*(i+1),y:state.y+8};actors.push({x:pose?390+i*285:p.x,y:pose?380:p.y,who,walking,hands:handsHigh,back:handsHigh});});
 actors.sort((a,b)=>a.y-b.y).forEach(a=>{
 drawPerson(ctx,a.x,a.y,a.who,{scale:a.scale||2.25,frame:time/100,walking:a.walking,back:a.back,hands:a.hands,alpha:a.alpha??1,flip:a.flip,lean:a.lean||0});
 if(a.photographer!==undefined)drawCameraFlash(ctx,a,time,reduceMotion);
 if(a.player&&state.merch)drawBag(a.x,a.y);
 });
 // Destination labels stay readable above the crowd.
 for(const h of hotspots())if(h.action!=='invite'){const stage=state.room==='show'&&['dj','steven','joz'].includes(h.id);label(h.x,stage?414:h.y-27,h.tag,{active:target?.id===h.id,color:h.done?'#86e2b1':'#ffca6c'});}
 // Labels stay above the crowd, so your crew never disappears in a packed room.
 const heroX=pose?480:state.x,heroY=pose?382:state.y;
 ctx.strokeStyle='#ffe7a4';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(heroX,heroY+2,29,8,0,0,Math.PI*2);ctx.stroke();
 const name=(state.name||'YOU').toUpperCase();let nameY=heroY-144;
 // A player standing behind a listening spot should not hide its circle with their name.
 if(state.room==='show'&&hotspots().some(h=>['dj','steven','joz'].includes(h.id)&&Math.abs(heroX-h.x)<name.length*4.8+55&&nameY+6>h.y-18&&nameY-19<h.y+18))nameY=Math.min(H-12,heroY+32);
 label(heroX,nameY,name,{active:true});
 for(const a of actors.filter(a=>a.npc))label(a.x,a.y-146,a.who==='jay'?'JAY +15':'GRACE +15',{active:target?.id===a.who});

 for(const p of particles){p.x+=p.vx*dt;p.y+=p.vy*dt;p.vy+=190*dt;p.life-=dt;ctx.globalAlpha=Math.max(0,p.life);ctx.fillStyle=p.color;ctx.fillRect(p.x,p.y,5,5);}ctx.globalAlpha=1;particles=particles.filter(p=>p.life>0);
 if(route.length){const end=route[route.length-1];ctx.strokeStyle='#fff4c4';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(end.x-5,end.y);ctx.lineTo(end.x+5,end.y);ctx.moveTo(end.x,end.y-5);ctx.lineTo(end.x,end.y+5);ctx.stroke();}
 $('#action-label').textContent=target?{invite:'INVITE FRIEND',enter:'ENTER SHOW',merch:'GET MERCH',dj:'DJ BOOTH',worship:'HANDS UP',vip:'ENTER VIP',photo:'TAKE PHOTO',outside:'GO OUTSIDE',show:'MAIN STAGE',refresh:'SAY HELLO'}[target.action]:'WALK & INTERACT';
 requestAnimationFrame(render);
}
function update(dt,time){
 let dx=0,dy=0;const old={x:state.x,y:state.y};if(keys.has('up'))dy--;if(keys.has('down'))dy++;if(keys.has('left'))dx--;if(keys.has('right'))dx++;
 if(dx||dy){route=[];autoAction=null;}else if(route.length){const p=route[0],d=Math.hypot(p.x-state.x,p.y-state.y);if(d<5){state.x=p.x;state.y=p.y;route.shift();if(!route.length&&autoAction){const h=autoAction;autoAction=null;interact(h);}return;}dx=(p.x-state.x)/d;dy=(p.y-state.y)/d;}
 const d=Math.hypot(dx,dy);if(d){dx/=d;dy/=d;const speed=180*dt;if(walkable(state.x+dx*speed,state.y))state.x+=dx*speed;if(walkable(state.x,state.y+dy*speed))state.y+=dy*speed;}
 walking=Math.hypot(old.x-state.x,old.y-state.y)>.05;
 const nowAtFront=stageSpotAt(state);if(nowAtFront&&nowAtFront!==atFront)raiseHands(nowAtFront);else if(!nowAtFront&&atFront){atFront=null;raisingUntil=0;worshipMusic.leave();}
 if(walking){trail.unshift({x:state.x,y:state.y});if(trail.length>100)trail.pop();}
 state.friends.forEach((_,i)=>{const desired=walking?(trail[Math.min(trail.length-1,19+22*i)]||{x:state.x-40*(i+1),y:state.y+10}):{x:state.x-45*(i+1),y:Math.min(640,state.y+15+i*3)};const p=followerPositions[i]||{...desired};p.x+=(desired.x-p.x)*Math.min(1,dt*5);p.y+=(desired.y-p.y)*Math.min(1,dt*5);p.x=Math.max(32,p.x);p.y=Math.min(640,p.y);followerPositions[i]=p;});
 if(route.length&&!walking&&d){route=[];autoAction=null;notify('Try the open floor, or choose a destination below.');}
}
canvas.addEventListener('pointerdown',e=>{if(dialog.open||photoBusy)return;e.preventDefault();canvas.focus({preventScroll:true});const r=canvas.getBoundingClientRect(),x=camera+(e.clientX-r.left)/r.width*viewWidth,y=(e.clientY-r.top)/r.height*H;const h=hotspots().find(h=>(h.id==='dj'&&x>420&&x<605&&y>220&&y<370)||(Math.abs(x-h.x)<56&&y>h.y-155&&y<h.y+25));if(h){goTo(h);return;}if(walkable(x,y)){autoAction=null;route=findPath(state.room,state,{x,y});keys.clear();}else notify('Tap the open floor or a destination button to walk there.');});
const keyMap={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right'};
window.addEventListener('keydown',e=>{if(dialog.open||e.target.matches('input,textarea'))return;const key=e.key.length===1?e.key.toLowerCase():e.key;if(keyMap[key]){e.preventDefault();keys.add(keyMap[key]);}else if((key==='e'||key===' ')&&!e.repeat&&!e.target.closest('button,a')){e.preventDefault();interactButton();}});
window.addEventListener('keyup',e=>{const key=e.key.length===1?e.key.toLowerCase():e.key;if(keyMap[key])keys.delete(keyMap[key]);});
window.addEventListener('blur',()=>keys.clear());document.addEventListener('visibilitychange',()=>{keys.clear();paused=document.hidden;safeSave();});
document.querySelectorAll('[data-dir]').forEach(b=>{const release=()=>{keys.delete(b.dataset.dir);b.classList.remove('held');};b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(b.dataset.dir);b.classList.add('held');};b.onpointerup=release;b.onpointercancel=release;b.onlostpointercapture=release;});
$('#interact').onclick=interactButton;$('#photo-button').onclick=showPhoto;$('#celebrate-button').onclick=()=>celebration.play();
$('#sound').onclick=()=>{soundOn=!soundOn;$('#sound').setAttribute('aria-pressed',soundOn);$('#sound span').textContent=soundOn?'Sound on':'Sound off';tone();};
$('#player-profile').onclick=()=>openPlayerSetup();
$('#help').onclick=()=>openDialog('A little guide to a great night.','Move with arrow keys or WASD. Click the on-screen A button, or press E / Space, to interact or walk to the nearest activity. The keyboard A key moves left. Destination buttons also walk you there. Bring both friends to the show, then explore freely: merch, Eli’s B–I–B–L–E game, Steven’s OUTSIDE spot on the left, Joz’s BIRKENSTOCK spot on the right, and VIP in any order. Walk to either artist’s front-row ring and your crew raises their hands automatically. Eli’s ring is in the middle. Bring your two friends (+30 XP), finish merch and take your bag (+20), raise your hands (+25), finish Eli’s beat game (+25), and take your VIP photo (+25). At 125 XP you unlock fireworks; your VIP photo is yours to download. Each activity awards XP once per night. Replay Eli’s game to improve your best beat score. All glory to Jesus.',[{label:'LET’S PLAY'}],'HOW TO PLAY');
$('#restart').onclick=()=>openDialog('One more night?','This resets your game progress on this device. Download your current VIP photo first if you want to keep it.',[{label:'START FRESH',fn:()=>{state={...initialState(),name:state.name,avatar:state.avatar,profileReady:state.profileReady,beatBest:state.beatBest};trail=[];followerPositions=[];particles=[];victoryPending=false;celebration.stop();raisingUntil=0;atFront=null;worshipMusic.leave();sync();announceRoom();}},{label:'Keep this night',secondary:true}],'NEW GAME');
dialog.addEventListener('cancel',e=>{if(!state.profileReady)e.preventDefault();});
dialog.addEventListener('close',()=>{stopBeat?.();stopBeat=null;stopActivity?.();stopActivity=null;keys.clear();canvas.focus({preventScroll:true});});
async function start(){
 try{await loadPeople();await Promise.all(['outside','show','vip'].map(name=>new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>{images[name]=img;resolve();};img.onerror=reject;img.src=`/play/assets/${name==='show'?'show-stage-v6':name==='vip'?'vip-branded-v7':name}.webp`;})));sync();announceRoom();requestAnimationFrame(render);if(!state.profileReady)openPlayerSetup();}
 catch{openDialog('The room didn’t load.','The connection was interrupted. Reload to try again; your saved progress stays on this device.',[{label:'RELOAD',fn:()=>location.reload()}],'CONNECTION CHECK');}
}
start();
