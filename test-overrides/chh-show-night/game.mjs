import {MAX_SCORE,initialState,score,coins,objective,pointsToGo,act,restore} from './state.mjs?v=vip-18';
import {drawPerson,loadPeople} from './sprites.mjs?v=vip-18';
import {crowdActors,crowdCounts} from './crowds.mjs?v=vip-18';
import {createCelebration} from './celebration.mjs?v=vip-18';
import {pitPhotographers,drawCameraFlash} from './pit.mjs?v=vip-18';
import {avatars,avatarFor,playerName} from './avatars.mjs?v=vip-18';
import {mountRound} from './rounds.mjs?v=mobile-20';
import {createRoundAudio} from './round-audio.mjs?v=mobile-20';
import {createScoreStore,createOnlineScores} from './leaderboard.mjs?v=vip-18';
import {gameIds,gameNames} from './scoring.mjs?v=vip-18';
import {mountPhotoStyle,drawVipPhoto,photoFrames} from './activities.mjs?v=vip-18';
import {walkable as canWalk,findPath,clampPosition} from './navigation.mjs?v=mobile-20';
import {practiceSpot,drawPracticeBooth} from './practice-booth.mjs?v=vip-18';
import {createWorshipMusic,inFrontRow,stageSpotAt,stageSpots} from './worship.mjs?v=vip-18';
const $=s=>document.querySelector(s), canvas=$('#world'),ctx=canvas.getContext('2d'),dialog=$('#dialog');
const worshipMusic={leave(){},get playing(){return null;}};const roundAudio=createRoundAudio();const scoreStore=createScoreStore(),onlineScores=createOnlineScores();let atFront=null;
const unlockAudio=e=>{if(e.isTrusted)roundAudio.unlock().catch(()=>{});};
for(const event of ['pointerdown','pointerup','touchend','click','keydown'])document.addEventListener(event,unlockAudio,{capture:true,passive:true});
const storageKey='kc-show-night-v1', W=1024,H=683;
let state;try{state=restore(localStorage.getItem(storageKey));}catch{state=initialState();}
state.sessionId ||= crypto.randomUUID();onlineScores.connect(state).catch(()=>{});
let stopBeat=null,stopActivity=null;
let keys=new Set(),route=[],autoAction=null,walking=false,frame=0,last=0,camera=0,viewWidth=W,paused=false,raisingUntil=0,photoBusy=false,photoURL=null,toastTimer,introTimer,soundOn=true,particles=[],trail=[],followerPositions=[];
const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
const celebration=createCelebration({reduceMotion});let victoryPending=false;
const roomInfo={outside:['01','OUTSIDE THE VENUE','BRING YOUR PEOPLE.'],show:['02','THE MAIN STAGE','GOOD MUSIC. GREATER PURPOSE.'],vip:['03','THE VIP LOUNGE','MAKE A MEMORY.']};
const images={};
const safeSave=()=>{try{localStorage.setItem(storageKey,JSON.stringify(state));}catch{}};
function notify(message){$('#toast').textContent=message;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),3600);}
try{soundOn=localStorage.getItem('kc-show-night-sound')!=='off';}catch{}
roundAudio.setMuted(!soundOn);
function updateSoundButton(){const button=$('#sound');button.textContent=soundOn?'♪ On':'♪ Off';button.setAttribute('aria-pressed',soundOn);button.setAttribute('aria-label',soundOn?'Sound on. Tap to mute':'Sound off. Tap to enable');button.title=soundOn?'Sound on':'Sound off';}
function toggleSound(){soundOn=!soundOn;roundAudio.setMuted(!soundOn);updateSoundButton();try{localStorage.setItem('kc-show-night-sound',soundOn?'on':'off');}catch{}if(soundOn)roundAudio.unlock().then(()=>tone()).catch(()=>notify('Tap the sound button again to enable audio.'));notify(soundOn?'Sound on — music plays in the games.':'Sound off');return soundOn;}
function tone(kind='up'){if(soundOn)roundAudio.effect(kind);}
updateSoundButton();
function burst(x=state.x,y=state.y-60){if(reduceMotion)return;for(let i=0;i<35;i++)particles.push({x,y,vx:(Math.random()-.5)*180,vy:-70-Math.random()*130,life:1.2,color:['#ffc45b','#ff7053','#79d8ae','#c7a0f4'][i%4]});}
function sync(){
 $('#player-tag').textContent=state.name?`${state.name.toUpperCase()} · THAT’S YOU`:'FOLLOW YOUR NAME TAG';
 const n=score(state);$('#xp-value').textContent=n.toLocaleString();scoreStore.record(state);$('#session-rounds').textContent=`${state.rounds} ROUNDS`;
 $('#friends').textContent=`${state.friends.length}/2`;$('#coins').textContent=coins(state);$('#objective').textContent=objective(state);$('#room-name').textContent=`${roomInfo[state.room][0]} / ${roomInfo[state.room][1]}`;
 let activeFound=false;document.querySelectorAll('#checklist li').forEach(li=>{const k=li.dataset.step,done=k==='friends'?state.friends.length===2:!!state[k];li.classList.toggle('done',done);li.classList.toggle('active',!done&&!activeFound);if(!done)activeFound=true;li.querySelector('.step-icon').textContent=done?'✓':String([...li.parentElement.children].indexOf(li)+1).padStart(2,'0');});
 renderDestinations();safeSave();
}
function apply(action,value){if(['invite','enter','worship','vip','photo','show','outside'].includes(action))onlineScores.journey(action,value);const oldRoom=state.room,oldScore=score(state);state=act(state,action,value);if(state.room!==oldRoom){worshipMusic.leave();atFront=null;raisingUntil=0;route=[];autoAction=null;trail=[];followerPositions=[];announceRoom();}if(action==='profile')onlineScores.connect(state).catch(()=>{});if(score(state)>oldScore){tone();burst();}if(Math.floor(oldScore/MAX_SCORE)<Math.floor(score(state)/MAX_SCORE))victoryPending=true;sync();}
function announceRoom(){const info=roomInfo[state.room];$('#room-intro small').textContent=`CHAPTER ${info[0]}`;$('#room-intro strong').textContent=info[2];$('#room-intro').classList.add('visible');clearTimeout(introTimer);introTimer=setTimeout(()=>$('#room-intro').classList.remove('visible'),1500);}
function hotspots(){
 if(state.room==='outside')return [
 ...(!state.friends.includes('jay')?[{id:'jay',x:210,y:590,label:'Invite Jay',tag:'JAY',action:'invite',value:'jay'}]:[]),
 ...(!state.friends.includes('grace')?[{id:'grace',x:348,y:578,label:'Invite Grace',tag:'GRACE',action:'invite',value:'grace'}]:[]),
 {id:'enter',x:740,y:385,label:'Venue entrance',tag:'THE SHOW',action:'enter'}];
 if(state.room==='show')return [
 {id:'merch',x:105,y:455,label:'Merch',tag:'MERCH',action:'merch',done:!!state.merch},
 {id:'dj',...practiceSpot,label:'Eli',tag:'ELI · B–I–B–L–E',action:'dj',done:!!state.eli},
 ...stageSpots.map(p=>({...p,label:p.id==='joz'?'Joz':'Steven',action:'artist',done:state.totals[p.id]>0})),
 {id:'vip',x:940,y:447,label:'VIP',tag:'VIP →',action:'vip'},
 {id:'outside',x:75,y:625,label:'← Outside',tag:'EXIT',action:'outside'}];
 return [
 {id:'photo',x:505,y:442,label:state.photo?'Another VIP photo':'Meet the band',tag:'PHOTO SPOT',action:'photo',done:state.photo},
 {id:'show',x:105,y:310,label:'← Main stage',tag:'← SHOW',action:'show'},
 {id:'refresh',x:875,y:410,label:'Refreshments',tag:'TAKE A BREATHER',action:'refresh'}];
}
function renderDestinations(){const wrap=$('#destinations');wrap.replaceChildren();hotspots().forEach(h=>{const b=document.createElement('button');b.textContent=h.label;b.dataset.destination=h.id;b.classList.toggle('done',!!h.done);b.onclick=()=>goTo(h);wrap.append(b);});}
const walkable=(x,y)=>canWalk(state.room,x,y);
function goTo(h){if(photoBusy)return;keys.clear();autoAction=h;route=findPath(state.room,state,h);
 const track=h.action==='dj'?'eli':h.action==='merch'?'chamblissnation':h.action==='artist'?h.id:null;if(track)roundAudio.preload(track).catch(()=>{});
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
 }else if(h.action==='artist'){
 raiseHands(h.id);openArtistGame(h.id);
 }else if(h.action==='vip'){
 apply('vip');
 }else if(h.action==='dj'){
 openBeatChallenge();
 }else if(h.action==='photo'){
 openPhotoStyle();
 }else if(h.action==='refresh'){
 route=[];autoAction=null;keys.clear();tone('step');notify('Refreshed! Keep enjoying the night.');
 }else apply(h.action);
}
function activityHost(content){const host=document.createElement('div');content.insertBefore(host,content.lastElementChild);return host;}
function openMerch(){openArtistGame('chamblissnation');}
function raiseHands(id){if(!id)return;apply('worship');raisingUntil=performance.now()+10000;atFront=id;}
function openArtistGame(game){
 if(dialog.open)return;
 route=[];autoAction=null;keys.clear();
 const content=$('#dialog-content');content.replaceChildren();dialog.classList.add('game-dialog');dialog.showModal();
 stopActivity=mountRound(content,{game,audio:roundAudio,art:images,online:onlineScores,onSoundToggle:toggleSound,onExit:()=>dialog.close(),onFinish:result=>{apply('round',result);}});
}
function openPhotoStyle(){
 const content=openDialog('Make this one yours.','Choose a crew pose and frame. Then we’ll count you in: 3, 2, 1.',[{label:'TAKE THE PHOTO',fn:takePhoto},{label:'Not quite ready',secondary:true}],'VIP PHOTO · YOUR CREW');
 let chosen={...state.photoStyle};
 stopActivity=mountPhotoStyle(activityHost(content),{avatar:avatarFor(state).sprite,backdrop:images.vip,style:chosen,onChange:value=>{chosen=value;}});
 content.querySelector('.dialog-actions button').onclick=()=>{apply('photoStyle',chosen);dialog.close();takePhoto();};
}
function openBeatChallenge(){openArtistGame('eli');}
function openPlayerSetup(){
 const content=openDialog(state.profileReady?'Your player. Your vibe.':'Who’s coming to the show?','Choose your character and the name your crew will know you by.',[],'PLAYER SELECT · CHH SHOW NIGHT');
 const form=document.createElement('form');form.className='player-form';
 const nameLabel=document.createElement('label');nameLabel.htmlFor='player-name';nameLabel.textContent='YOUR NAME';
 const input=document.createElement('input');input.id='player-name';input.name='player-name';input.maxLength=18;input.required=true;input.autocomplete='nickname';input.placeholder='Enter your name';input.value=state.name||'';
 let selected=state.avatar||'red';const grid=document.createElement('div');grid.className='avatar-grid';grid.setAttribute('role','group');grid.setAttribute('aria-label','Choose your character');
 avatars.forEach(a=>{const b=document.createElement('button');b.type='button';b.className='avatar-choice';b.dataset.avatar=a.id;b.setAttribute('aria-pressed',a.id===selected);const portrait=document.createElement('canvas');portrait.width=140;portrait.height=180;portrait.setAttribute('aria-hidden','true');const g=portrait.getContext('2d');g.imageSmoothingEnabled=true;drawPerson(g,70,172,a.sprite,{scale:2.7});const label=document.createElement('span');label.textContent=a.label;b.append(portrait,label);b.onclick=()=>{selected=a.id;grid.querySelectorAll('button').forEach(button=>button.setAttribute('aria-pressed',button===b));};grid.append(b);});
 const submit=document.createElement('button');submit.type='submit';submit.className='player-start';submit.textContent=state.profileReady?'SAVE MY PLAYER →':'LET’S MAKE A NIGHT →';
 form.append(nameLabel,input,grid,submit);form.onsubmit=e=>{e.preventDefault();if(!playerName(input.value)){input.setCustomValidity('Enter your name to start.');input.reportValidity();return;}input.setCustomValidity('');apply('profile',{name:input.value,avatar:selected});dialog.close();notify(`Welcome, ${state.name}. Bring your people!`);};input.oninput=()=>input.setCustomValidity('');content.insertBefore(form,content.lastElementChild);if(state.profileReady){const cancel=document.createElement('button');cancel.className='secondary';cancel.textContent='Keep my player';cancel.onclick=()=>dialog.close();content.lastElementChild.append(cancel);}input.focus();
}
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function takePhoto(){
 photoBusy=true;route=[];keys.clear();for(const n of ['3','2','1']){$('#countdown').textContent=n;tone('step');await pause(700);}$('#countdown').textContent='';if(!reduceMotion){$('#flash').classList.remove('firing');void $('#flash').offsetWidth;$('#flash').classList.add('firing');}apply('photo');tone('photo');await pause(200);await showPhoto();photoBusy=false;
}
async function makePhoto(){
 const c=document.createElement('canvas');c.width=1200;c.height=1180;const g=c.getContext('2d');
 g.fillStyle=photoFrames[state.photoStyle.frame];g.fillRect(0,0,1200,1180);
 drawVipPhoto(g,{backdrop:images.vip,avatar:avatarFor(state).sprite,pose:state.photoStyle.pose,x:20,y:20,width:1160,height:1000});
 g.fillStyle='#101b2c';g.textAlign='center';
 const name=`${(state.name||'YOU').toUpperCase()}'S SHOW NIGHT`;
 g.font=`bold ${Math.min(52,1040/(name.length*.61))}px monospace`;g.fillText(name,600,1080);
 g.font='bold 22px monospace';g.fillText(`${score(state).toLocaleString()} POINTS · BACKSTAGE WITH YOUR CREW`,600,1124);
 g.font='16px monospace';g.fillText('KINGDOM CIRCUIT · ALL GLORY TO JESUS.',600,1158);
 return new Promise(resolve=>c.toBlob(resolve,'image/png'));
}
async function showPhoto(){
 try{const blob=await makePhoto();if(!blob)throw new Error('Photo unavailable');if(photoURL)URL.revokeObjectURL(photoURL);photoURL=URL.createObjectURL(blob);const content=openDialog('All glory to Jesus.','Your crew, backstage with the band. Keep the memory, then head back out and enjoy the show. All glory to Jesus.',[{label:'KEEP HANGING OUT',secondary:true}],`VIP MEMORY · ${score(state)} SHOW NIGHT XP`);const img=document.createElement('img');img.className='photo-preview';img.src=photoURL;img.alt='Your player and two friends posing with the Steven Malcolm-inspired vocalist, Eli-inspired DJ, and Joz-inspired performer at the VIP backdrop.';content.insertBefore(img,content.lastElementChild);const a=document.createElement('a');a.href=photoURL;a.download='Kingdom-Circuit-CHH-Show-Night-VIP.png';a.textContent='↓ DOWNLOAD PHOTO';const full=document.createElement('a');full.href=photoURL;full.target='_blank';full.rel='noopener';full.className='photo-full';full.textContent='OPEN FULL SIZE';content.lastElementChild.prepend(a,full);}catch{notify('Could not create the photo. Tap Your VIP Photo to try again.');}
}
function label(x,y,text,{active=false,color='#ffca6c',size=16,scale=1}={}){
 ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);ctx.font=`bold ${size}px monospace`;const width=ctx.measureText(text).width+20;ctx.fillStyle=active?'#ffca6c':'#08182bea';ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.fillRect(-width/2,-size-3,width,size+9);ctx.strokeRect(-width/2,-size-3,width,size+9);ctx.fillStyle=active?'#101926':'#fff2d8';ctx.textAlign='center';ctx.fillText(text,0,-2);ctx.restore();
}
function drawBag(x,y){ctx.fillStyle='#0b1625';ctx.fillRect(x+22,y-39,19,26);ctx.fillStyle='#dcaa6a';ctx.fillRect(x+24,y-37,15,22);ctx.strokeStyle='#d9ae73';ctx.lineWidth=3;ctx.strokeRect(x+27,y-43,9,8);ctx.fillStyle='#684825';ctx.save();ctx.translate(x+31.5,y-24);ctx.scale(.12,.3);ctx.font='bold 10px monospace';ctx.textAlign='center';ctx.fillText('@thekingdomcircuit',0,0);ctx.restore();}
function render(time){
 const dt=Math.min((time-last)/1000,.04)||.016;last=time;frame+=dt;
 if(!dialog.open&&!photoBusy&&!paused)update(dt,time);else walking=false;
 const rect=canvas.getBoundingClientRect(),ratio=Math.min(devicePixelRatio||1,2),cw=Math.round(rect.width*ratio),ch=Math.round(rect.height*ratio);
 if(canvas.width!==cw||canvas.height!==ch){canvas.width=cw;canvas.height=ch;}
 viewWidth=H*(rect.width/rect.height);camera=Math.max(0,Math.min(W-viewWidth,state.x-viewWidth/2));if(viewWidth>=W){camera=0;viewWidth=W;}
 ctx.setTransform(canvas.width/viewWidth,0,0,canvas.height/H,-camera*canvas.width/viewWidth,0);ctx.imageSmoothingEnabled=true;
 ctx.clearRect(camera,0,viewWidth,H);ctx.drawImage(images[state.room],0,0,W,H);
 if(state.room==='show'&&!reduceMotion){ctx.save();ctx.globalAlpha=.03+Math.sin(time/800)*.018;ctx.fillStyle='#ffd079';ctx.fillRect(0,0,W,400);ctx.restore();}
 if(state.room==='show'){
  drawVenueBranding();
  drawPracticeBooth(ctx,time,images.booth);
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
 // Half-size activity signs reduce clutter; world tap zones and quick buttons stay full size.
 for(const h of hotspots())if(h.action!=='invite'){const stage=state.room==='show'&&['dj','steven','joz'].includes(h.id);label(h.x,stage?414:h.y-27,h.tag,{active:target?.id===h.id,color:h.done?'#86e2b1':'#ffca6c',scale:state.room==='show'&&(stage||h.id==='merch')?.5:1});}
 // Labels stay above the crowd, so your crew never disappears in a packed room.
 const heroX=pose?480:state.x,heroY=pose?382:state.y;
 ctx.strokeStyle='#ffe7a4';ctx.lineWidth=2;ctx.beginPath();ctx.ellipse(heroX,heroY+2,29,8,0,0,Math.PI*2);ctx.stroke();
 const name=(state.name||'YOU').toUpperCase();let nameY=heroY-144;
 // A player standing behind a listening spot should not hide its circle with their name.
 if(state.room==='show'&&hotspots().some(h=>['dj','steven','joz'].includes(h.id)&&Math.abs(heroX-h.x)<name.length*6.6+55&&nameY+6>h.y-18&&nameY-25<h.y+18))nameY=Math.min(H-12,heroY+32);
 label(heroX,nameY,name,{active:true,size:22});
 for(const a of actors.filter(a=>a.npc))label(a.x,a.y-146,a.who==='jay'?'JAY +15':'GRACE +15',{active:target?.id===a.who});

 for(const p of particles){p.x+=p.vx*dt;p.y+=p.vy*dt;p.vy+=190*dt;p.life-=dt;ctx.globalAlpha=Math.max(0,p.life);ctx.fillStyle=p.color;ctx.fillRect(p.x,p.y,5,5);}ctx.globalAlpha=1;particles=particles.filter(p=>p.life>0);
 if(route.length){const end=route[route.length-1];ctx.strokeStyle='#fff4c4';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(end.x-5,end.y);ctx.lineTo(end.x+5,end.y);ctx.moveTo(end.x,end.y-5);ctx.lineTo(end.x,end.y+5);ctx.stroke();}
 $('#action-label').textContent=target?{artist:'PLAY ARTIST',invite:'INVITE FRIEND',enter:'ENTER SHOW',merch:'GET MERCH',dj:'DJ BOOTH',worship:'HANDS UP',vip:'ENTER VIP',photo:'TAKE PHOTO',outside:'GO OUTSIDE',show:'MAIN STAGE',refresh:'TAKE A BREAK'}[target.action]:'WALK & INTERACT';
 requestAnimationFrame(render);
}
function update(dt,time){
 Object.assign(state,clampPosition(state));
 let dx=0,dy=0;const old={x:state.x,y:state.y};if(keys.has('up'))dy--;if(keys.has('down'))dy++;if(keys.has('left'))dx--;if(keys.has('right'))dx++;
 if(dx||dy){route=[];autoAction=null;}else if(route.length){const p=route[0],d=Math.hypot(p.x-state.x,p.y-state.y);if(d<5){state.x=p.x;state.y=p.y;route.shift();if(!route.length&&autoAction){const h=autoAction;autoAction=null;interact(h);}return;}dx=(p.x-state.x)/d;dy=(p.y-state.y)/d;}
 const d=Math.hypot(dx,dy);if(d){dx/=d;dy/=d;const speed=180*dt;if(walkable(state.x+dx*speed,state.y))state.x+=dx*speed;if(walkable(state.x,state.y+dy*speed))state.y+=dy*speed;}
 walking=Math.hypot(old.x-state.x,old.y-state.y)>.05;
 const nowAtFront=stageSpotAt(state);if(nowAtFront&&nowAtFront!==atFront&&(!autoAction||autoAction.id===nowAtFront)){raiseHands(nowAtFront);openArtistGame(nowAtFront);}else if(!nowAtFront&&atFront){atFront=null;raisingUntil=0;worshipMusic.leave();}
 if(walking){trail.unshift({x:state.x,y:state.y});if(trail.length>100)trail.pop();}
 state.friends.forEach((_,i)=>{const desired=walking?(trail[Math.min(trail.length-1,19+22*i)]||{x:state.x-40*(i+1),y:state.y+10}):{x:state.x-45*(i+1),y:Math.min(640,state.y+15+i*3)};const p=followerPositions[i]||{...desired};p.x+=(desired.x-p.x)*Math.min(1,dt*5);p.y+=(desired.y-p.y)*Math.min(1,dt*5);p.x=Math.max(32,p.x);p.y=Math.min(640,p.y);followerPositions[i]=p;});
 if(route.length&&!walking&&d){route=[];autoAction=null;notify('Try the open floor, or choose a destination below.');}
}
let dragPointer=null;
function pointFromTouch(e){const r=canvas.getBoundingClientRect();return {x:camera+(e.clientX-r.left)/r.width*viewWidth,y:(e.clientY-r.top)/r.height*H};}
function walkToPoint(point){autoAction=null;route=findPath(state.room,state,point);keys.clear();}
canvas.addEventListener('pointerdown',e=>{
 if(dialog.open||photoBusy)return;e.preventDefault();canvas.focus({preventScroll:true});dragPointer={id:e.pointerId,x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);
 const {x,y}=pointFromTouch(e),h=hotspots().find(h=>(h.id==='dj'&&x>420&&x<605&&y>220&&y<370)||(Math.abs(x-h.x)<56&&y>h.y-155&&y<h.y+25));
 if(h)goTo(h);else walkToPoint({x,y});
});
canvas.addEventListener('pointermove',e=>{if(!dragPointer||e.pointerId!==dragPointer.id||dialog.open||photoBusy)return;if(Math.hypot(e.clientX-dragPointer.x,e.clientY-dragPointer.y)<6)return;walkToPoint(pointFromTouch(e));});
for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>{dragPointer=null;});
const keyMap={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right'};
window.addEventListener('keydown',e=>{if(dialog.open||e.target.matches('input,textarea'))return;const key=e.key.length===1?e.key.toLowerCase():e.key;if(keyMap[key]){e.preventDefault();keys.add(keyMap[key]);}else if((key==='e'||key===' ')&&!e.repeat&&!e.target.closest('button,a')){e.preventDefault();interactButton();}});
window.addEventListener('keyup',e=>{const key=e.key.length===1?e.key.toLowerCase():e.key;if(keyMap[key])keys.delete(keyMap[key]);});
window.addEventListener('blur',()=>keys.clear());document.addEventListener('visibilitychange',()=>{keys.clear();paused=document.hidden;safeSave();});
document.querySelectorAll('[data-dir]').forEach(b=>{const release=()=>{keys.delete(b.dataset.dir);b.classList.remove('held');};b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(b.dataset.dir);b.classList.add('held');};b.onpointerup=release;b.onpointercancel=release;b.onlostpointercapture=release;});
$('#interact').onclick=interactButton;$('#menu').onclick=openMenu;$('#scoreboard').onclick=openBoard;
$('#sound').onclick=toggleSound;
$('#player-profile').onclick=()=>openPlayerSetup();
function openMenu(){
 const content=openDialog('Your night.','Tap anywhere or drag to walk. Scenery won’t block you. Each game has 20 chances: +40 for a hit, +10 for a clean hit. Replay for more points. Friends +30, hands high +25, VIP photo +25. Desktop: arrows/WASD, E or Space. All glory to Jesus.',[
 {label:'SCOREBOARD',fn:openBoard},{label:'YOUR PLAYER',fn:openPlayerSetup},
 ...(state.photo?[{label:'VIP PHOTO',fn:showPhoto}]:[]),
 {label:'FIREWORKS',fn:()=>celebration.play()},
 {label:'FRESH SESSION',secondary:true,fn:()=>openDialog('Start a new night?','Your best session stays on this device. This starts a new total and journey.',[{label:'START FRESH',fn:()=>{scoreStore.record(state);state={...initialState(),sessionId:crypto.randomUUID(),name:state.name,avatar:state.avatar,profileReady:true};trail=[];followerPositions=[];atFront=null;onlineScores.connect(state).catch(()=>{});celebration.stop();sync();announceRoom();}},{label:'KEEP THIS NIGHT',secondary:true}])},
 {label:'BACK TO THE SHOW',secondary:true}],'CHH SHOW NIGHT · TEST PREVIEW');
}
async function openBoard(){
 const content=openDialog('Scoreboard','',[{label:'BACK TO SHOW',secondary:true}],'CHH SHOW NIGHT');
 dialog.classList.add('score-dialog');
 const [eyebrow,heading,description,actions]=content.children;
 const header=document.createElement('header');header.className='score-header';
 const logo=document.createElement('img');logo.src='/play/assets/kingdom-circuit-instagram.webp';logo.alt='Kingdom Circuit';logo.width=72;logo.height=72;
 const title=document.createElement('div');title.append(eyebrow,heading);header.append(logo,title);description.remove();
 const status=document.createElement('p');status.className='score-status';status.setAttribute('role','status');status.textContent='Loading scores…';
 const host=document.createElement('div');host.className='board';
 const row=scoreStore.record(state);
 function scoreCard(r,label){
  const card=document.createElement('section');card.className='score-card';card.setAttribute('aria-label',label);
  const top=document.createElement('div');top.className='score-card-top';const identity=document.createElement('div');
  const caption=document.createElement('h3');caption.textContent=label;const name=document.createElement('p');name.className='score-nickname';name.textContent=r.nickname||'Player';identity.append(caption,name);
  const total=document.createElement('div');total.className='score-total';const value=document.createElement('strong');value.textContent=r.total.toLocaleString();const unit=document.createElement('span');unit.textContent='POINTS';total.append(value,unit);top.append(identity,total);
  const games=document.createElement('dl');games.className='score-games';
  for(const id of gameIds){const item=document.createElement('div'),term=document.createElement('dt'),points=document.createElement('dd');term.textContent=gameNames[id];points.textContent=r[id].toLocaleString();item.append(term,points);games.append(item);}
  const journey=document.createElement('p');journey.className='score-journey';journey.textContent=`Journey +${r.journey.toLocaleString()}`;card.append(top,games,journey);return card;
 }
 host.append(scoreCard(row,'Current session'));
 const share=document.createElement('button');share.textContent='SHARE SCORECARD';share.onclick=()=>shareScore(row);actions.prepend(share);
 content.replaceChildren(header,status,host,actions);
 try{const board=await(onlineScores.enabled?onlineScores.board():scoreStore.board());if(!host.isConnected)return;status.textContent=board.mode==='device'?'Saved on this device':'Community best sessions';board.rows.forEach(r=>host.append(scoreCard(r,board.mode==='device'?'Best session':'Community best')));}
 catch{if(host.isConnected)status.textContent='Saved on this device · Online scores unavailable';}
}
async function shareScore(row){
 const c=document.createElement('canvas');c.width=720;c.height=1000;const g=c.getContext('2d');g.fillStyle='#0b1928';g.fillRect(0,0,720,1000);g.drawImage(images.kcLogo,275,40,170,170);g.textAlign='center';g.fillStyle='#ffcb6c';g.font='bold 38px monospace';g.fillText('CHH SHOW NIGHT',360,265);g.fillStyle='#f8efda';g.font='24px monospace';g.fillText(row.nickname,360,320);g.font='bold 88px monospace';g.fillText(row.total.toLocaleString(),360,435);g.font='20px monospace';g.fillText('SESSION POINTS',360,475);gameIds.forEach((id,i)=>{g.textAlign='left';g.fillStyle='#7ed9b1';g.fillText(gameNames[id],65,560+i*60);g.textAlign='right';g.fillStyle='#fff0d6';g.fillText(row[id].toLocaleString(),655,560+i*60);});g.textAlign='center';g.fillStyle='#ffcb6c';g.fillText('BUILT FOR THE FANS. ALL FOR THE KING.',360,870);g.fillStyle='#f8efda';g.fillText('@thekingdomcircuit · TEST PREVIEW',360,920);const blob=await new Promise(r=>c.toBlob(r));if(!blob)return;const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Kingdom-Circuit-Scorecard.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),60000);
}
function drawVenueBranding(){
 // Use the orange-rimmed emblem from the VIP room on the concert wall.
 ctx.drawImage(images.venueLogo,895,166,120,120);
 ctx.fillStyle='#0a1524';ctx.fillRect(13,44,174,70);if(images.logo)ctx.drawImage(images.logo,19,48,162,47);ctx.font='bold 5.6px monospace';ctx.textAlign='center';ctx.fillStyle='#fff0d8';ctx.fillText('YOUR PEOPLE MY PEOPLE WE FAMILY',100,105);
 // Enlarge the hanging display 20%, leaving the vendor's head clear below it.
 if(images.merch){for(let i=0;i<3;i++)ctx.drawImage(images.merch,images.merch.width/3*i,0,images.merch.width/3,images.merch.height,12+i*60,115,60,69.6);}

}
dialog.addEventListener('cancel',e=>{if(!state.profileReady)e.preventDefault();});
dialog.addEventListener('close',()=>{dialog.classList.remove('game-dialog','score-dialog');stopBeat?.();stopBeat=null;stopActivity?.();stopActivity=null;keys.clear();canvas.focus({preventScroll:true});});
async function start(){
 try{await loadPeople();await Promise.all(Object.entries({venueLogo:'venue-logo-v14.webp',booth:'dj-booth-v12.webp',merch:'merch-chamblissnation-v1.webp',logo:'chamblissnation-logo.webp',kcLogo:'kingdom-circuit-instagram.webp',items:'joz-items-v1.webp',jozBg:'joz-game-v1.webp',stevenBg:'steven-game-v1.webp',chamblissnationBg:'merch-game-v1.webp'}).map(async([key,file])=>{const image=new Image();image.src=`/play/assets/${file}`;await image.decode();images[key]=image;}));await Promise.all(['outside','show','vip'].map(name=>new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>{images[name]=img;resolve();};img.onerror=reject;img.src=`/play/assets/${name}-${name==='show'?'v12':'v8'}.webp`;})));sync();announceRoom();requestAnimationFrame(render);if(!state.profileReady)openPlayerSetup();}
 catch{openDialog('The room didn’t load.','The connection was interrupted. Reload to try again; your saved progress stays on this device.',[{label:'RELOAD',fn:()=>location.reload()}],'CONNECTION CHECK');}
}
start();
