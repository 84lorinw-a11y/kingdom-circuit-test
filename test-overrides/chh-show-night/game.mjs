import {MAX_SCORE,initialState,score,coins,objective,pointsToGo,act,restore} from './state.mjs?v=scores-27';
import {drawPerson,loadPeople} from './sprites.mjs?v=scores-27';
import {crowdActors,crowdCounts} from './crowds.mjs?v=scores-27';
import {createCelebration} from './celebration.mjs?v=scores-27';
import {pitPhotographers,drawCameraFlash} from './pit.mjs?v=scores-27';
import {avatars,avatarFor,playerName} from './avatars.mjs?v=scores-27';
import {mountRound} from './rounds.mjs?v=scores-27';
import {createRoundAudio} from './round-audio.mjs?v=scores-27';
import {createScoreStore,createOnlineScores} from './leaderboard.mjs?v=scores-27';
import {createScoreTable} from './scoreboard-view.mjs?v=scores-27';
import {gameIds,gameNames} from './scoring.mjs?v=scores-27';
import {mountPhotoStyle,drawVipPhoto,photoFrames} from './activities.mjs?v=scores-27';
import {findPath,clampPosition,stepToward} from './navigation.mjs?v=scores-27';
import {practiceSpot,drawPracticeBooth} from './practice-booth.mjs?v=scores-27';
import {createWorshipMusic,inFrontRow,stageSpotAt,stageSpots} from './worship.mjs?v=scores-27';
import {hasVisited,nextStop} from './journey-guide.mjs?v=scores-27';
import {createDialogLifecycle} from './dialog-lifecycle.mjs?v=scores-27';
import {breakProgress,drawWaterSip} from './water-break.mjs?v=scores-27';
const $=s=>document.querySelector(s), canvas=$('#world'),ctx=canvas.getContext('2d'),dialog=$('#dialog');
const worshipMusic={leave(){},get playing(){return null;}};const roundAudio=createRoundAudio();const scoreStore=createScoreStore(),onlineScores=createOnlineScores();let atFront=null;
const unlockAudio=e=>{if(e.isTrusted)roundAudio.unlock().catch(()=>{});};
for(const event of ['pointerdown','pointerup','touchend','click','keydown'])document.addEventListener(event,unlockAudio,{capture:true,passive:true});
const storageKey='kc-show-night-v1', W=1024,H=683;
let state;try{state=restore(localStorage.getItem(storageKey));}catch{state=initialState();}
state.sessionId ||= crypto.randomUUID();let playerEntryPending=true;
const modal=createDialogLifecycle(dialog,$('#dialog-content'));
let waterBreak=null,photoRun=0;
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
 const n=score(state);$('#xp-value').textContent=n.toLocaleString();if(state.profileReady)scoreStore.record(state);$('#session-rounds').textContent=`${state.rounds} ROUNDS`;
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
 {id:'enter',x:740,y:385,label:'Enter show',tag:'THE SHOW',action:'enter'}];
 if(state.room==='show')return [
 {id:'merch',x:105,y:455,label:'Merch',tag:'MERCH',action:'merch',done:!!state.merch},
 {id:'dj',...practiceSpot,label:'Eli',tag:'ELI · B–I–B–L–E',action:'dj',done:!!state.eli},
 ...stageSpots.map(p=>({...p,label:p.id==='joz'?'Joz':'Steven',action:'artist',done:state.totals[p.id]>0})),
 {id:'vip',x:940,y:447,label:'VIP',tag:'VIP →',action:'vip'},
 {id:'outside',x:75,y:625,label:'← Outside',tag:'EXIT',action:'outside'}];
 return [
 {id:'photo',x:505,y:442,label:state.photo?'Another VIP photo':'VIP photo',tag:'VIP PHOTO',action:'photo',done:state.photo},
 {id:'show',x:105,y:310,label:'← Main stage',tag:'← SHOW',action:'show'},
 {id:'refresh',x:875,y:410,label:'Take a breather',tag:'TAKE A BREATHER',action:'refresh'}];
}
function renderDestinations(){const wrap=$('#destinations'),next=nextStop(state);wrap.replaceChildren();hotspots().forEach(h=>{const b=document.createElement('button'),visited=hasVisited(state,h.id);b.textContent=h.label;b.dataset.destination=h.id;b.classList.toggle('done',visited);b.classList.toggle('unvisited',!visited);b.classList.toggle('next-stop',next===h.id);b.setAttribute('aria-label',`${h.label}${next===h.id?' — next stop':!visited?' — not visited':''}`);b.onclick=()=>goTo(h);wrap.append(b);});}
function goTo(h){if(photoBusy||dialog.open)return;endBreak();keys.clear();autoAction=h;route=findPath(state.room,state,h);
 const track=h.action==='dj'?'eli':h.action==='merch'?'chamblissnation':h.action==='artist'?h.id:null;if(track)roundAudio.preload(track).catch(()=>{});
 if(!route.length){autoAction=null;notify('Choose a spot on the open floor.');return;}
 notify(`Walking to ${h.label.toLowerCase().replace(' ✓','')}…`);canvas.focus({preventScroll:true});
}
function nearest(limit=83){return hotspots().map(h=>({...h,d:Math.hypot(state.x-h.x,state.y-h.y)})).filter(h=>h.d<limit).sort((a,b)=>a.d-b.d)[0];}
function interactButton(){if(dialog.open||photoBusy)return;const nearby=nearest();if(nearby)interact(nearby);else{const h=nearest(Infinity);if(h)goTo(h);}}
function openDialog(title,body,buttons=[],eyebrow='CHH SHOW NIGHT'){
 endBreak();route=[];autoAction=null;keys.clear();dragPointer=null;const content=modal.prepare();const over=document.createElement('p');over.className='overline';over.textContent=eyebrow;const heading=document.createElement('h2');heading.textContent=title;const text=document.createElement('p');text.textContent=body;content.append(over,heading,text);const actions=document.createElement('div');actions.className='dialog-actions';buttons.forEach(({label,fn,secondary=false})=>{const b=document.createElement('button');b.textContent=label;if(secondary)b.className='secondary';b.onclick=()=>{modal.close();fn?.();};actions.append(b);});content.append(actions);if(!dialog.open)dialog.showModal();return content;
}
function interact(h=nearest()){
 if(dialog.open||photoBusy)return;
 if(!h){notify('Click the A button, or use E / Space near a glowing marker.');return;}
 if(h.action==='invite'){
 const name=h.value==='jay'?'Jay':'Grace';openDialog(`Bring ${name} to the show?`,`${name} is ready! Choose “Bring ${name} along” to add them to your crew. Invite both friends, then head inside.`,[{label:`BRING ${name.toUpperCase()} ALONG · +15`,fn:()=>{apply('invite',h.value);notify(`${name} joined you! ${state.friends.length===2?'Next: Enter show.':`Next: Invite ${name==='Jay'?'Grace':'Jay'}.`}`);}},{label:'KEEP EXPLORING — INVITE LATER',secondary:true,fn:()=>notify(`${name} is still waiting. Tap ${name} or their button when you’re ready.`)}],`MEET ${name.toUpperCase()}`);
 }else if(h.action==='enter'){
 if(state.friends.length<2){const missing=['jay','grace'].filter(id=>!state.friends.includes(id));openDialog('Bring your two friends first.','Tap a friend below. Walk over, then choose Bring them along. Once both join you, Enter show takes you inside.',[...missing.map(id=>({label:`GO TO ${id.toUpperCase()}`,fn:()=>goTo(hotspots().find(h=>h.id===id))})),{label:'BACK TO EXPLORING',secondary:true}],'YOUR NEXT STEP');return;}apply('enter');
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
 startBreak();
 }else apply(h.action);
}
function startBreak(){
 route=[];autoAction=null;keys.clear();dragPointer=null;waterBreak={started:performance.now()};apply('visit','refresh');tone('step');
 $('#break-status').hidden=false;$('#break-count').textContent='WATER BREAK · 6s';$('#objective').textContent='Your crew is taking a sip. Tap anywhere to leave early.';
}
function endBreak(finished=false){if(!waterBreak)return;waterBreak=null;$('#break-status').hidden=true;$('#objective').textContent=objective(state);if(finished)notify('Crew refreshed! Tap Main stage or keep exploring.');}
$('#end-break').onclick=()=>endBreak(true);
function activityHost(content){const host=document.createElement('div');content.insertBefore(host,content.lastElementChild);return host;}
function openMerch(){openArtistGame('chamblissnation');}
function raiseHands(id){if(!id)return;apply('worship');raisingUntil=performance.now()+10000;atFront=id;}
function openArtistGame(game){
 if(dialog.open)return;
 endBreak();route=[];autoAction=null;keys.clear();dragPointer=null;
 apply('visit',game==='chamblissnation'?'merch':game==='eli'?'dj':game);
 const content=modal.prepare();dialog.classList.add('game-dialog');dialog.showModal();
 modal.attach(mountRound(content,{game,audio:roundAudio,art:images,online:onlineScores,onSoundToggle:toggleSound,onExit:()=>modal.close(),onFinish:result=>{apply('round',result);}}));
}
function openPhotoStyle(){
 const content=openDialog('Make this one yours.','Choose a crew pose and frame. Then we’ll count you in: 3, 2, 1.',[{label:'TAKE THE PHOTO',fn:takePhoto},{label:'BACK TO VIP — NO PHOTO',secondary:true}],'VIP PHOTO · YOUR CREW');
 let chosen={...state.photoStyle};
 modal.attach(mountPhotoStyle(activityHost(content),{avatar:avatarFor(state).sprite,backdrop:images.vip,style:chosen,onChange:value=>{chosen=value;}}));
 content.querySelector('.dialog-actions button').onclick=()=>{apply('photoStyle',chosen);modal.close();takePhoto();};
}
function openBeatChallenge(){openArtistGame('eli');}
function startFreshNight(){
 endBreak();cancelPhoto();
 if(state.profileReady)scoreStore.record(state);
 state={...initialState(),sessionId:crypto.randomUUID()};playerEntryPending=true;
 route=[];autoAction=null;keys.clear();trail=[];followerPositions=[];atFront=null;raisingUntil=0;victoryPending=false;celebration.stop();
 if(photoURL){URL.revokeObjectURL(photoURL);photoURL=null;}
 sync();openPlayerSetup({entry:true});
}
function openPlayerSetup({entry=false}={}){
 const returning=state.profileReady;
 const content=openDialog('Pick your player.',entry&&returning?'Continue your saved night, or start a new game.':'Enter your name. Choose your look.',[],'CHH SHOW NIGHT');
 const form=document.createElement('form');form.className='player-form';
 const nameLabel=document.createElement('label');nameLabel.htmlFor='player-name';nameLabel.textContent='YOUR NAME';
 const input=document.createElement('input');input.id='player-name';input.name='player-name';input.maxLength=18;input.required=true;input.autocomplete='nickname';input.placeholder='Enter your name';input.value=state.name||'';
 let selected=returning?state.avatar:'';
 const grid=document.createElement('div');grid.className='avatar-grid';grid.setAttribute('role','group');grid.setAttribute('aria-label','Choose your character');
 const hint=document.createElement('p');hint.className='player-choice-hint';hint.id='player-choice-hint';hint.setAttribute('aria-live','polite');grid.setAttribute('aria-describedby',hint.id);
 const updateHint=()=>{const choice=avatars.find(a=>a.id===selected);hint.textContent=choice?`${choice.label} selected`:'Tap a character to choose.';};updateHint();
 avatars.forEach(a=>{const b=document.createElement('button');b.type='button';b.className='avatar-choice';b.dataset.avatar=a.id;b.setAttribute('aria-pressed',a.id===selected);const portrait=document.createElement('canvas');portrait.width=140;portrait.height=180;portrait.setAttribute('aria-hidden','true');const g=portrait.getContext('2d');g.imageSmoothingEnabled=true;drawPerson(g,70,172,a.sprite,{scale:2.7});const label=document.createElement('span');label.textContent=a.label;b.append(portrait,label);b.onclick=()=>{selected=a.id;grid.querySelectorAll('button').forEach(button=>button.setAttribute('aria-pressed',button===b));updateHint();};grid.append(b);});
 const submit=document.createElement('button');submit.type='submit';submit.className='player-start';submit.textContent=entry&&returning?'CONTINUE MY NIGHT →':returning?'SAVE MY PLAYER →':'START MY NIGHT →';
 form.append(nameLabel,input,grid,hint,submit);
 form.onsubmit=e=>{e.preventDefault();if(!playerName(input.value)){input.setCustomValidity('Enter your name to start.');input.reportValidity();return;}input.setCustomValidity('');if(!avatars.some(a=>a.id===selected)){hint.textContent='Choose a character before starting.';grid.querySelector('button').focus();return;}apply('profile',{name:input.value,avatar:selected});playerEntryPending=false;modal.close();announceRoom();notify(`Welcome, ${state.name}. Bring your people!`);};input.oninput=()=>input.setCustomValidity('');content.insertBefore(form,content.lastElementChild);
 if(entry&&returning){const fresh=document.createElement('button');fresh.className='secondary';fresh.textContent='NEW PLAYER / NEW GAME';fresh.onclick=startFreshNight;content.lastElementChild.append(fresh);}
 else if(returning){const cancel=document.createElement('button');cancel.className='secondary';cancel.textContent='Keep my player';cancel.onclick=()=>modal.close();content.lastElementChild.append(cancel);}
 // Focus the title so the phone keyboard does not hide the character choices.
 const heading=content.querySelector('h2');heading.tabIndex=-1;heading.focus({preventScroll:true});
}
const pause=ms=>new Promise(r=>setTimeout(r,ms));
function cancelPhoto(){photoRun++;photoBusy=false;$('#countdown').textContent='';}
async function takePhoto(){
 const token=++photoRun;photoBusy=true;route=[];autoAction=null;keys.clear();
 try{for(const n of ['3','2','1']){if(token!==photoRun)return;$('#countdown').textContent=n;tone('step');await pause(700);}if(token!==photoRun)return;
 $('#countdown').textContent='';if(!reduceMotion){$('#flash').classList.remove('firing');void $('#flash').offsetWidth;$('#flash').classList.add('firing');}apply('photo');tone('photo');await pause(200);if(token===photoRun)await showPhoto(token);
 }finally{if(token===photoRun){photoBusy=false;$('#countdown').textContent='';}}
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
 return new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(Error('Photo took too long')),6000);c.toBlob(blob=>{clearTimeout(timeout);resolve(blob);},'image/png');});
}
async function showPhoto(token=photoRun){
 try{const blob=await makePhoto();if(token!==photoRun)return;if(!blob)throw new Error('Photo unavailable');if(photoURL)URL.revokeObjectURL(photoURL);photoURL=URL.createObjectURL(blob);const content=openDialog('All glory to Jesus.','Your crew, backstage with the band. Keep the memory, then head back out and enjoy the show. All glory to Jesus.',[{label:'KEEP HANGING OUT',secondary:true}],`VIP MEMORY · ${score(state)} SHOW NIGHT XP`);const img=document.createElement('img');img.className='photo-preview';img.src=photoURL;img.alt='Your player and two friends posing with the Steven Malcolm-inspired vocalist, Eli-inspired DJ, and Joz-inspired performer at the VIP backdrop.';content.insertBefore(img,content.lastElementChild);const a=document.createElement('a');a.href=photoURL;a.download='Kingdom-Circuit-CHH-Show-Night-VIP.png';a.textContent='↓ DOWNLOAD PHOTO';const full=document.createElement('a');full.href=photoURL;full.target='_blank';full.rel='noopener';full.className='photo-full';full.textContent='OPEN FULL SIZE';content.lastElementChild.prepend(a,full);}catch{notify('Could not create the photo. Tap Your VIP Photo to try again.');}
}
function label(x,y,text,{active=false,color='#ffca6c',size=16,scale=1}={}){
 ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);ctx.font=`bold ${size}px monospace`;const width=ctx.measureText(text).width+20;ctx.fillStyle=active?'#ffca6c':'#08182bea';ctx.strokeStyle=color;ctx.lineWidth=1.5;ctx.fillRect(-width/2,-size-3,width,size+9);ctx.strokeRect(-width/2,-size-3,width,size+9);ctx.fillStyle=active?'#101926':'#fff2d8';ctx.textAlign='center';ctx.fillText(text,0,-2);ctx.restore();
}
function drawBag(x,y){ctx.fillStyle='#0b1625';ctx.fillRect(x+22,y-39,19,26);ctx.fillStyle='#dcaa6a';ctx.fillRect(x+24,y-37,15,22);ctx.strokeStyle='#d9ae73';ctx.lineWidth=3;ctx.strokeRect(x+27,y-43,9,8);ctx.fillStyle='#684825';ctx.save();ctx.translate(x+31.5,y-24);ctx.scale(.12,.3);ctx.font='bold 10px monospace';ctx.textAlign='center';ctx.fillText('@thekingdomcircuit',0,0);ctx.restore();}
function render(time){
 const dt=Math.min((time-last)/1000,.04)||.016;last=time;frame+=dt;
 if(!dialog.open&&!photoBusy&&!paused)update(dt,time);else walking=false;
 const rect=canvas.getBoundingClientRect();if(rect.width<1||rect.height<1){requestAnimationFrame(render);return;}const ratio=Math.min(devicePixelRatio||1,2),cw=Math.round(rect.width*ratio),ch=Math.round(rect.height*ratio);
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
 const unvisited=!hasVisited(state,h.id),stage=state.room==='show'&&['dj','steven','joz'].includes(h.id),wave=reduceMotion?1:(Math.sin(time/900)+1)/2,rx=stage?40:34,ry=stage?15:12;
 ctx.save();
 if(unvisited){ctx.globalAlpha=.18+wave*.2;ctx.fillStyle='#ffcb6c';ctx.beginPath();ctx.ellipse(h.x,h.y,rx+7+wave*5,ry+6,0,0,Math.PI*2);ctx.fill();ctx.globalAlpha=1;ctx.shadowColor='#ffcb6c';ctx.shadowBlur=reduceMotion?0:9+wave*9;}
 ctx.strokeStyle=unvisited?'#ffda83':h.id===target?.id?'#fff0c5':'#7ed9b1';ctx.lineWidth=unvisited?3.5:2;ctx.beginPath();ctx.ellipse(h.x,h.y,rx+(unvisited?wave*3:0),ry,0,0,Math.PI*2);ctx.fillStyle=unvisited?'#ffcb6c30':'#08182b50';ctx.fill();ctx.stroke();ctx.shadowBlur=0;
 if(unvisited){ctx.fillStyle='#ffda83';ctx.beginPath();ctx.moveTo(h.x-7,h.y-34-wave*3);ctx.lineTo(h.x+7,h.y-34-wave*3);ctx.lineTo(h.x,h.y-24-wave*3);ctx.closePath();ctx.fill();}ctx.restore();
 }
 const actors=crowdActors(state.room,time,reduceMotion,state);
 if(state.room==='show')actors.push(...pitPhotographers);

 if(state.room==='outside'){
 if(!state.friends.includes('jay'))actors.push({x:210,y:590,who:'jay',npc:true});
 if(!state.friends.includes('grace'))actors.push({x:348,y:578,who:'grace',npc:true});
 }else if(state.room==='vip'){
 [['mc',446],['dj',525],['singer',604]].forEach(([who,x])=>actors.push({x,y:346,who,scale:2.25}));
 }
 const resting=waterBreak?breakProgress(waterBreak.started,time):null;
 if(resting?.done)endBreak(true);else if(resting)$('#break-count').textContent=`WATER BREAK · ${resting.remaining}s`;
 const pose=photoBusy,handsHigh=state.room==='show'&&(inFrontRow(state)||time<raisingUntil);actors.push({x:pose?480:state.x,y:pose?382:state.y,who:avatarFor(state).sprite,player:true,hands:handsHigh,back:handsHigh,walking});
 state.friends.forEach((who,i)=>{const p=followerPositions[i]||{x:state.x-50*(i+1),y:state.y+8};actors.push({x:pose?390+i*285:p.x,y:pose?380:p.y,who,walking:walking&&!waterBreak,drinking:!!waterBreak,hands:handsHigh,back:handsHigh});});
 actors.sort((a,b)=>a.y-b.y).forEach(a=>{
 drawPerson(ctx,a.x,a.y,a.who,{scale:a.scale||2.25,frame:time/100,walking:a.walking,back:a.back,hands:a.hands,alpha:a.alpha??1,flip:a.flip,lean:a.lean||0});
 if(a.drinking)drawWaterSip(ctx,a,resting.elapsed,reduceMotion);
 if(a.photographer!==undefined)drawCameraFlash(ctx,a,time,reduceMotion);
 if(a.player&&state.merch)drawBag(a.x,a.y);
 });
 // Half-size activity signs reduce clutter; world tap zones and quick buttons stay full size.
 for(const h of hotspots())if(h.action!=='invite'){const stage=state.room==='show'&&['dj','steven','joz'].includes(h.id);label(h.x,stage?414:h.y-27,h.tag,{active:target?.id===h.id,color:hasVisited(state,h.id)?'#86e2b1':'#ffca6c',scale:state.room==='show'&&(stage||h.id==='merch')?.5:1});}
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
 Object.assign(state,clampPosition(state,state.room));
 let dx=0,dy=0;const old={x:state.x,y:state.y};if(keys.has('up'))dy--;if(keys.has('down'))dy++;if(keys.has('left'))dx--;if(keys.has('right'))dx++;
 let arrivedAction=null;
 if(dx||dy){route=[];autoAction=null;const d=Math.hypot(dx,dy);Object.assign(state,clampPosition({x:state.x+dx/d*180*dt,y:state.y+dy/d*180*dt},state.room));}
 else if(route.length){const step=stepToward(state.room,state,route[0],180*dt);state.x=step.x;state.y=step.y;if(step.arrived){route.shift();if(!route.length){arrivedAction=autoAction;autoAction=null;}}}
 walking=Math.hypot(old.x-state.x,old.y-state.y)>.05;
 if(arrivedAction){interact(arrivedAction);return;}
 const nowAtFront=stageSpotAt(state);
 // A walk past an artist must not interrupt a route or a drag. Intentional taps still auto-start on arrival.
 if(nowAtFront&&nowAtFront!==atFront&&!route.length&&!dragPointer&&!walking&&!autoAction){raiseHands(nowAtFront);openArtistGame(nowAtFront);}
 else if(!nowAtFront&&atFront){atFront=null;raisingUntil=0;worshipMusic.leave();}
 if(walking){trail.unshift({x:state.x,y:state.y});if(trail.length>100)trail.pop();}
 state.friends.forEach((_,i)=>{const desired=waterBreak?{x:state.x+(i===0?-64:62),y:state.y+27}:walking?(trail[Math.min(trail.length-1,19+22*i)]||{x:state.x-40*(i+1),y:state.y+10}):{x:state.x-45*(i+1),y:Math.min(640,state.y+15+i*3)};const p=followerPositions[i]||{...desired};p.x+=(desired.x-p.x)*Math.min(1,dt*5);p.y+=(desired.y-p.y)*Math.min(1,dt*5);Object.assign(p,clampPosition(p,state.room));p.y=Math.min(640,p.y);followerPositions[i]=p;});

}
let dragPointer=null;
function pointFromTouch(e){const r=canvas.getBoundingClientRect();return {x:camera+(e.clientX-r.left)/r.width*viewWidth,y:(e.clientY-r.top)/r.height*H};}
function walkToPoint(point){endBreak();autoAction=null;route=findPath(state.room,state,point);keys.clear();}
canvas.addEventListener('pointerdown',e=>{
 if(dialog.open||photoBusy)return;e.preventDefault();canvas.focus({preventScroll:true});dragPointer={id:e.pointerId,x:e.clientX,y:e.clientY};canvas.setPointerCapture(e.pointerId);
 const {x,y}=pointFromTouch(e),h=hotspots().find(h=>(h.id==='dj'&&x>420&&x<605&&y>220&&y<370)||(Math.abs(x-h.x)<56&&y>h.y-155&&y<h.y+25));
 if(h)goTo(h);else walkToPoint({x,y});
});
canvas.addEventListener('pointermove',e=>{if(!dragPointer||e.pointerId!==dragPointer.id||dialog.open||photoBusy)return;if(Math.hypot(e.clientX-dragPointer.x,e.clientY-dragPointer.y)<6)return;walkToPoint(pointFromTouch(e));});
for(const event of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(event,()=>{dragPointer=null;});
const keyMap={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'up',s:'down',a:'left',d:'right'};
window.addEventListener('keydown',e=>{if(dialog.open||e.target.matches('input,textarea'))return;const key=e.key.length===1?e.key.toLowerCase():e.key;if(keyMap[key]){e.preventDefault();endBreak();keys.add(keyMap[key]);}else if((key==='e'||key===' ')&&!e.repeat&&!e.target.closest('button,a')){e.preventDefault();interactButton();}});
window.addEventListener('keyup',e=>{const key=e.key.length===1?e.key.toLowerCase():e.key;if(keyMap[key])keys.delete(keyMap[key]);});
function resumeWorld(){keys.clear();dragPointer=null;paused=document.hidden;last=0;}
window.addEventListener('blur',()=>{keys.clear();dragPointer=null;});window.addEventListener('pageshow',resumeWorld);document.addEventListener('visibilitychange',()=>{resumeWorld();safeSave();});
document.querySelectorAll('[data-dir]').forEach(b=>{const release=()=>{keys.delete(b.dataset.dir);b.classList.remove('held');};b.onpointerdown=e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(b.dataset.dir);b.classList.add('held');};b.onpointerup=release;b.onpointercancel=release;b.onlostpointercapture=release;});
$('#interact').onclick=interactButton;$('#menu').onclick=openMenu;$('#scoreboard').onclick=openBoard;
$('#sound').onclick=toggleSound;
$('#player-profile').onclick=()=>openPlayerSetup();
function openMenu(){
 cancelPhoto();
 const content=openDialog('Your night.','Follow the gold circles and Next prompt. Tap or drag to walk. The stage and merch table are off limits; the crowd and grass won’t block you. Each game has 20 chances: +40 for a hit, +10 for a clean hit. Replay for more points. Friends +30, hands high +25, VIP photo +25. Desktop: arrows/WASD, E or Space. All glory to Jesus.',[
 {label:'SCOREBOARD',fn:openBoard},{label:'YOUR PLAYER',fn:openPlayerSetup},
 ...(state.photo?[{label:'VIP PHOTO',fn:showPhoto}]:[]),
 {label:'FIREWORKS',fn:()=>celebration.play()},
 {label:'NEW GAME',secondary:true,fn:()=>openDialog('Start a new night?','Choose a new name and player. Your best session stays saved.',[{label:'CHOOSE MY PLAYER',fn:startFreshNight},{label:'KEEP THIS NIGHT',secondary:true}])},
 {label:'BACK TO THE SHOW',secondary:true}],'CHH SHOW NIGHT · TEST PREVIEW');
}
async function openBoard(){
 const content=openDialog('Scoreboard','',[{label:'BACK TO SHOW',secondary:true}],'CHH SHOW NIGHT');
 dialog.classList.add('score-dialog');
 const [eyebrow,heading,description,actions]=content.children;
 const header=document.createElement('header');header.className='score-header';
 const logo=document.createElement('img');logo.src='/play/assets/kingdom-circuit-instagram.webp';logo.alt='Kingdom Circuit';logo.width=72;logo.height=72;
 const title=document.createElement('div');title.append(eyebrow,heading);header.append(logo,title);description.remove();
 const status=document.createElement('p');status.className='score-status';status.setAttribute('role','status');status.textContent='Loading players…';
 const host=document.createElement('div');host.className='board';const row=scoreStore.record(state);
 const current=document.createElement('p');current.className='score-current';current.textContent=`Your current session · ${row.nickname} · ${row.total.toLocaleString()} points`;
 const swipe=document.createElement('p');swipe.className='score-swipe';swipe.textContent='Swipe for artist scores →';
 const more=document.createElement('button');more.className='score-more';more.textContent='SHOW MORE PLAYERS';more.hidden=true;
 const share=document.createElement('button');share.textContent='SHARE MY SCORE';share.onclick=()=>shareScore(row);actions.prepend(share);
 content.replaceChildren(header,status,current,swipe,host,more,actions);
 let table=null,nextOffset=null,loaded=0,busy=false;
 async function load(offset=0){
  if(busy)return;busy=true;more.disabled=true;
  try{
   const board=await(onlineScores.enabled?onlineScores.board(offset):scoreStore.board());if(!host.isConnected)return;
   if(!table){table=createScoreTable(board.mode==='online'?'All players · best session':'Players saved on this device');host.append(table.element);}
   table.append(board.rows);loaded+=board.rows.length;nextOffset=board.nextOffset;
   status.textContent=board.mode==='online'?`${board.totalPlayers.toLocaleString()} players · Highest total first · Showing ${loaded.toLocaleString()}`:'Shared scores are not connected yet. These players are saved only in this browser.';
   if(onlineScores.pendingCount)status.textContent+=` · ${onlineScores.pendingCount} round(s) waiting to save. We’ll retry automatically.`;
   if(onlineScores.rejectedCount)status.textContent+=` · ${onlineScores.rejectedCount} earlier round(s) could not be verified and remain on this device.`;
   if(!board.rows.length&&!loaded){const empty=document.createElement('p');empty.className='score-empty';empty.textContent='Be the first to start a night.';host.append(empty);}
   more.hidden=nextOffset===null;more.textContent='SHOW MORE PLAYERS';
  }catch{if(host.isConnected){status.textContent=onlineScores.enabled?'The shared scoreboard could not load. Your score is still saved on this device.':'Shared scores are not connected yet.';more.hidden=false;more.textContent='TRY AGAIN';}}
  finally{busy=false;more.disabled=false;}
 }
 more.onclick=()=>load(nextOffset??0);await load();
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
dialog.addEventListener('cancel',e=>{if(playerEntryPending||!state.profileReady)e.preventDefault();});
dialog.addEventListener('keydown',e=>{if(e.key==='Escape'&&(playerEntryPending||!state.profileReady)){e.preventDefault();e.stopPropagation();}});
dialog.addEventListener('close',()=>{if(playerEntryPending&&!dialog.open&&dialog.querySelector('.player-form')){dialog.showModal();return;}if(!modal.onNativeClose())return;keys.clear();dragPointer=null;canvas.focus({preventScroll:true});});
async function start(){
 try{await loadPeople();await Promise.all(Object.entries({venueLogo:'venue-logo-v14.webp',booth:'dj-booth-v12.webp',merch:'merch-chamblissnation-v1.webp',logo:'chamblissnation-logo.webp',kcLogo:'kingdom-circuit-instagram.webp',items:'joz-items-v1.webp',jozBg:'joz-game-v1.webp',stevenBg:'steven-game-v1.webp',chamblissnationBg:'merch-game-v1.webp'}).map(async([key,file])=>{const image=new Image();image.src=`/play/assets/${file}`;await image.decode();images[key]=image;}));await Promise.all(['outside','show','vip'].map(name=>new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>{images[name]=img;resolve();};img.onerror=reject;img.src=`/play/assets/${name}-${name==='show'?'v12':'v8'}.webp`;})));sync();requestAnimationFrame(render);openPlayerSetup({entry:true});}
 catch{openDialog('The room didn’t load.','The connection was interrupted. Reload to try again; your saved progress stays on this device.',[{label:'RELOAD',fn:()=>location.reload()}],'CONNECTION CHECK');}
}
start();
