import {roundSeconds,roundSchedule,roundScore,gameNames} from './scoring.mjs?v=save-28';
import {merchTrack} from './music-config.mjs?v=save-28';
import {stevenFan,collectedFans} from './crowds.mjs?v=save-28';
import {drawPerson} from './sprites.mjs?v=save-28';
import {createBassDetector,createBassPulse} from './bass-fx.mjs?v=save-28';
import {drawBeatBoard,beatLayout,beatLane,laneColors,judgeBeat} from './eli-board.mjs?v=save-28';
import {merchDrop,merchCatch} from './merch-motion.mjs?v=save-28';
const titles={eli:'B–I–B–L–E',joz:'SOLE PURPOSE',steven:'WE OUTSIDE',chamblissnation:'FAMILY HAUL'};
const instructions={eli:'Tap the matching pad when the letter hits the gold line.',joz:'Drag Joz. Catch the sandals. Let the bags pass.',steven:'Drag Steven. Bring people into the crew. We outside!',chamblissnation:'Drag the tote left and right. Catch the fast shirts in the middle!'};
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text)e.textContent=text;return e;};
export function mountRound(host,{game,audio,art,online,onFinish,onExit,onSoundToggle,autostart=true}){
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 let disposed=false,phase='ready',raf=0,elapsed=0,started=0,last=0,px=210,target=210,notes=[],events=[],particles=[],roundId='',seed=1,run=0,ranked=false,combo=0,feedback='',feedbackUntil=0,lastAudioProgress=0,bassGlow=0,laneFlashes=[0,0,0,0],held=new Set();
 host.className='round';host.dataset.game=game;host.dataset.phase=phase;
 const top=el('div','round-top'),exit=el('button','round-exit','← Leave'),brand=el('div','round-brand'),artist=el('small','',gameNames[game].toUpperCase()),title=el('strong','',titles[game]);brand.append(artist,title);exit.onclick=onExit;
 if(game==='chamblissnation')brand.append(el('small','',`${merchTrack.artist} · ${merchTrack.title}`));
 const fx=el('button','round-fx',reduced?'FX reduced':'Bass FX on');fx.hidden=game!=='eli';fx.disabled=reduced;fx.setAttribute('aria-pressed',!reduced);const sound=el('button','round-sound');function syncSound(){sound.textContent=audio.muted?'♪ Off':'♪ On';sound.setAttribute('aria-pressed',!audio.muted);sound.setAttribute('aria-label',audio.muted?'Sound off. Tap to enable':'Sound on. Tap to mute');}sound.onclick=()=>{if(onSoundToggle)onSoundToggle();else audio.setMuted(!audio.muted);syncSound();};syncSound();top.append(exit,brand,sound,fx);
 const stats=el('div','round-stats'),points=el('b','','0'),time=el('b','',`${roundSeconds[game]}s`),streak=el('b','','0×');
 for(const [label,v] of [['POINTS',points],['TIME',time],[game==='eli'?'STREAK':'COMBO',streak]]){const group=el('div');group.append(el('small','',label),v);stats.append(group);}
 const arena=el('div','round-arena'),canvas=el('canvas');canvas.width=420;canvas.height=560;canvas.setAttribute('aria-label',instructions[game]);canvas.setAttribute('tabindex','0');arena.append(canvas);const g=canvas.getContext('2d');
 const overlay=el('div','round-overlay'),headline=el('h2','',titles[game]),message=el('p','',instructions[game]),start=el('button','round-start','Start Game'),results=el('p','round-results');results.setAttribute('aria-live','polite');overlay.append(headline,message,results,start);arena.append(overlay);
 const back=el('button','round-back','BACK TO THE SHOW');back.hidden=true;back.onclick=onExit;overlay.append(back);
 const callout=el('div','round-callout');callout.hidden=true;arena.append(callout);
 const hint=el('p','round-hint',instructions[game]),pads=el('div','round-pads');pads.hidden=game!=='eli';
 for(let i=0;i<4;i++){const b=el('button','pad'),letter=el('span','pad-letter','·'),key=el('small','pad-key',String(i+1));b.style.setProperty('--pad-color',laneColors[i]);b.append(letter,key);b.setAttribute('aria-label',`Beat pad ${i+1}`);b.onpointerdown=e=>{e.preventDefault();tap(i);};b.onclick=e=>{if(e.detail===0)tap(i);};pads.append(b);}
 const progress=el('progress');progress.max=roundSeconds[game];progress.value=0;progress.setAttribute('aria-label','Round progress');host.append(top,stats,progress,arena,pads,hint);
 const detector=createBassDetector(),pulse=createBassPulse([arena],{mobile:matchMedia('(pointer:coarse),(max-width:700px)').matches,reduceMotion:reduced});let enabled=!reduced;
 fx.onclick=()=>{enabled=pulse.setEnabled(!enabled);fx.textContent=enabled?'Bass FX on':'Bass FX off';fx.setAttribute('aria-pressed',enabled);};
 const bins=new Float32Array(1024);
 function report(text,color='#7ed9b1',x=px,y=game==='eli'?beatLayout(canvas.height).hitY:432){feedback=text;feedbackUntil=elapsed+.7;callout.textContent=text;callout.style.color=color;if(!reduced)for(let i=0;i<12;i++)particles.push({x,y,vx:(Math.random()-.5)*140,vy:-100-Math.random()*90,life:.7,color});}
 function settle(note,hit,perfect=false){
  if(note.done)return;note.done=true;events.push({id:note.id,hit,perfect:hit&&perfect});combo=hit?combo+1:0;
  const x=game==='eli'?note.lane*105+52.5:px;
  if(hit){const reward=perfect?'CLEAN +50':'NICE +40';report(game==='eli'&&combo%5===0?`${combo} STREAK · ${reward}`:reward,perfect?'#ffe1a0':'#7ed9b1',x);if(game==='eli'){laneFlashes[note.lane]=elapsed+.32;if(!reduced){points.classList.remove('score-bump');void points.offsetWidth;points.classList.add('score-bump');}}}
  else report('NEXT ONE!','#ff987f',x);
  const score=roundScore(events);points.textContent=score.total;streak.textContent=game==='eli'?String(combo):`${combo}×`;
 }
 function tap(lane){if(phase!=='playing')return;const hit=judgeBeat(notes,lane,audio.time);if(hit)settle(hit.note,true,hit.perfect);else report('WAIT FOR THE GOLD LINE','#ffcf76',lane*105+52.5);}
 async function begin(){
  const token=++run;phase='loading';host.dataset.phase=phase;start.disabled=true;start.textContent='Loading music…';results.textContent='';back.hidden=true;
  audio.unlock().catch(()=>{});
  try{const ticket=await online?.start(game).catch(()=>null);ranked=!!ticket;if(disposed||token!==run)return;const ready=await audio.play(game);if(disposed||token!==run)return;if(!ready)throw Error('Music did not start');
   roundId=ticket?.id||crypto.randomUUID();seed=crypto.getRandomValues(new Uint32Array(1))[0];notes=roundSchedule(game,seed);events=[];particles=[];combo=0;px=target=210;elapsed=0;feedback='';feedbackUntil=0;bassGlow=0;laneFlashes=[0,0,0,0];callout.hidden=true;host.dataset.bassHits='0';detector.reset();points.textContent='0';streak.textContent=game==='eli'?'0':'0×';phase='playing';host.dataset.phase=phase;overlay.hidden=true;started=performance.now();last=lastAudioProgress=started;canvas.focus({preventScroll:true});
  }catch{if(disposed||token!==run)return;retry('Tap Start Game to turn on the music.');}
 }
 function retry(text){run++;audio.stop();pulse.clear();phase='ready';host.dataset.phase=phase;overlay.hidden=false;headline.textContent='READY WHEN YOU ARE.';message.textContent=text;start.disabled=false;start.textContent='Start Game';back.hidden=true;callout.hidden=true;held.clear();}
 start.onclick=begin;
 function finish(){
  if(phase!=='playing')return;for(const note of notes)if(!note.done)settle(note,false);audio.stop();pulse.clear();phase='result';host.dataset.phase=phase;overlay.hidden=false;
  const result=roundScore(events),completedRun=run;
  headline.textContent=game==='eli'?(result.hits===20?'ALL FOR THE KING.':'THAT’S YOUR SET.'):result.total>=800?'THAT’S YOUR SET.':'GOOD NIGHT. GREAT CREW.';
  message.textContent=`${result.total.toLocaleString()} points added to your session.`;
  const summary=`${result.hits}/20 ${game==='eli'?'beats hit':'caught'} · ${result.perfect} clean · best streak ${result.bestCombo}`;
  results.textContent=summary;start.disabled=false;start.textContent='Play Again';back.hidden=false;callout.hidden=true;
  const resultData={game,id:roundId,seed,events:[...events]};onFinish(resultData);
  if(online?.enabled&&!ranked)results.textContent+=' · Saved on this device; online board unavailable.';
  if(ranked){
   results.textContent+=' · Saving to the scoreboard…';
   online.finish(resultData).then(()=>{if(!disposed&&run===completedRun)results.textContent=summary+' · Saved to the shared scoreboard.';}).catch(()=>{if(!disposed&&run===completedRun)results.textContent=summary+(online.pendingCount?' · Waiting to save. We’ll retry automatically.':' · Online save failed; score kept on this device.');});
  }
 }
 function move(e){if(game==='eli'||phase!=='playing')return;const r=canvas.getBoundingClientRect();const scale=Math.min(r.width/420,r.height/560),left=r.left+(r.width-420*scale)/2;target=Math.max(42,Math.min(378,(e.clientX-left)/scale));}
 canvas.onpointerdown=e=>{e.preventDefault();canvas.setPointerCapture(e.pointerId);if(game==='eli'){const r=canvas.getBoundingClientRect(),y=(e.clientY-r.top)/r.height*canvas.height;if(y>=beatLayout(canvas.height).laneTop)tap(beatLane(e.clientX,r.left,r.width));}else move(e);};canvas.onpointermove=e=>{if(e.buttons||e.pointerType==='touch')move(e);};
 const keydown=e=>{if(phase!=='playing')return;if(e.target.closest?.('.pad')&&['Enter',' '].includes(e.key))return;if(['ArrowLeft','ArrowRight','a','d'].includes(e.key)){e.preventDefault();held.add(e.key);}if(game==='eli'&&!e.repeat){const lane=Number(e.key)-1;if(lane>=0&&lane<4){e.preventDefault();tap(lane);}else if(e.key===' '){e.preventDefault();const n=notes.filter(n=>!n.done).sort((a,b)=>Math.abs(a.at-elapsed)-Math.abs(b.at-elapsed))[0];if(n)tap(n.lane);}}};
 const keyup=e=>held.delete(e.key);document.addEventListener('keydown',keydown);document.addEventListener('keyup',keyup);
 const visibility=()=>{if(document.hidden&&['playing','loading'].includes(phase))retry('Welcome back. Restart this round with the music.');};document.addEventListener('visibilitychange',visibility);
 function shirt(x,y,size,kind){const img=art.merch;if(!img)return;const w=img.width/3;g.drawImage(img,w*kind,0,w,img.height,x-size/2,y-size/2,size,size*img.height/w);}
 function sandal(x,y,bag=false){const im=art.items;if(!im)return;const w=im.width/2;g.save();g.translate(x,y);g.rotate(reduced?0:Math.sin(y/55)*.12);g.drawImage(im,bag?w:0,0,w,im.height,-30,-30,60,60*im.height/w);g.restore();}
 function scene(t,dt){
  const bg=g.createLinearGradient(0,0,0,560);bg.addColorStop(0,game==='steven'?'#f0a272':'#13263a');bg.addColorStop(1,'#07131e');g.fillStyle=bg;g.fillRect(0,0,420,560);if(art[game+'Bg']){g.drawImage(art[game+'Bg'],0,0,420,560);g.fillStyle='#07131e33';g.fillRect(0,0,420,560);}
  if(game==='eli'){
   bassGlow=Math.max(0,bassGlow-dt*3);
   drawBeatBoard(g,{height:canvas.height,art,time:t,phase,notes,reduced,combo,bass:enabled?bassGlow:0,flashes:laneFlashes});
   if(phase==='playing')for(const n of notes)if(!n.done&&t>n.at+.32)settle(n,false);
   const next=notes.find(n=>!n.done);
   for(let i=0;i<4;i++){const pad=pads.children[i],active=phase==='playing'&&next?.lane===i&&next.at-t<1.3;pad.classList.toggle('active',active);pad.classList.toggle('hit',phase==='playing'&&laneFlashes[i]>t);pad.querySelector('.pad-letter').textContent=active?'BIBLE'[next.id%5]:'·';}
   callout.hidden=phase!=='playing'||t>=feedbackUntil;
   const a=audio.analyser;if(a&&phase==='playing'){a.getFloatFrequencyData(bins);const hz=audio.sampleRate/a.fftSize;let power=0,count=0;for(let i=Math.ceil(35/hz);i<=Math.floor(170/hz);i++){power+=10**(bins[i]/10);count++;}if(detector.sample(Math.sqrt(power/Math.max(1,count)),t*1000)){pulse.hit();bassGlow=1;host.dataset.bassHits=String(Number(host.dataset.bassHits||0)+1);}}
  }else{
   if(game==='steven'){
    g.textAlign='center';g.font='bold 23px monospace';g.fillStyle='#fff7e1';g.fillText('BRING YOUR PEOPLE',210,40);
   }else if(game==='chamblissnation'){
    if(art.logo)g.drawImage(art.logo,45,16,330,97);g.fillStyle='#f5ddaf';g.font='bold 10px monospace';g.textAlign='center';g.fillText('YOUR PEOPLE MY PEOPLE WE FAMILY',210,130);

   }else{
    g.fillStyle='#07131ec9';g.fillRect(50,16,320,70);g.fillStyle='#ffcf76';g.font='bold 28px monospace';g.textAlign='center';g.fillText('BIRKENSTOCK',210,46);g.font='12px monospace';g.fillStyle='#f5e8ce';g.fillText('MORE SOLE. LESS STATUS.',210,70);
   }
   for(const n of notes){if(n.done)continue;const drop=game==='chamblissnation'?merchDrop(n,t):{x:n.x,y:430-(n.at-t)*170},y=drop.y;
    if(y>=140&&y<=520){if(game==='joz')sandal(drop.x,y);else if(game==='steven')drawPerson(g,drop.x,y,stevenFan(n.id),{scale:1.1,walking:true,frame:t*8});else {g.save();g.translate(drop.x,y-40);g.rotate(reduced?0:drop.rotation);shirt(0,0,102,n.kind);g.restore();}}
    // Judge even after a slow phone skips past the visible catch line.
    if(phase==='playing'&&t>=n.at)settle(n,Math.abs(px-n.x)<(game==='chamblissnation'?merchCatch.hit:52),Math.abs(px-n.x)<(game==='chamblissnation'?merchCatch.clean:23));
   }
   if(game==='joz')for(let i=0;i<7;i++){const at=3.1+i*2.4,y=430-(at-t)*170,x=60+(i*133)%300;if(y>120&&y<480)sandal(x,y,true);if(t>=at&&t-dt<at&&Math.abs(px-x)<40){combo=0;streak.textContent='0×';report('BAGS? LET THEM PASS.','#ff987f');}}
   if(game==='chamblissnation'){g.fillStyle='#e2c197';g.strokeStyle='#c19b65';g.lineWidth=5;g.strokeRect(px-23,454,46,35);g.fillRect(px-42,475,84,65);g.fillStyle='#403323';g.font='bold 7px monospace';g.textAlign='center';g.fillText('@thekingdomcircuit',px,509);}
   else {
    if(game==='steven'){
     const crew=collectedFans(events);
     // Keep the people actually caught, in a moving crew behind Steven.
     crew.map((who,i)=>({who,i})).reverse().forEach(({who,i})=>{const row=Math.floor(i/7),slot=i%7,center=Math.max(130,Math.min(290,px)),offset=slot===6?0:(slot%2?1:-1)*(46+Math.floor(slot/2)*28);drawPerson(g,center+offset,535-row*22,who,{scale:1.5-row*.12,walking:Math.abs(target-px)>2,frame:t*8+i});});
     if(crew.length){g.fillStyle='#0b1928de';g.fillRect(125,88,170,28);g.fillStyle='#ffcf76';g.textAlign='center';g.font='bold 14px monospace';g.fillText(`${crew.length} IN YOUR CREW`,210,107);}
    }
    drawPerson(g,px,546,game==='joz'?'singer':'mc',{scale:2.3,walking:Math.abs(target-px)>2||game==='steven',frame:t*8});
   }
   g.strokeStyle='#7ed9b1';g.lineWidth=2;g.beginPath();g.ellipse(px,550,41,6,0,0,7);g.stroke();
  }
  if(game!=='eli'&&t<feedbackUntil){g.textAlign='center';g.fillStyle='#ffcf76';g.font='bold 20px monospace';g.fillText(feedback,210,game==='eli'?500:230);}
  for(const p of particles){p.x+=p.vx*dt;p.y+=p.vy*dt;p.life-=dt;g.globalAlpha=Math.max(0,p.life);g.fillStyle=p.color;g.fillRect(p.x,p.y,4,4);}g.globalAlpha=1;particles=particles.filter(p=>p.life>0);
 }
 function tick(now){if(disposed)return;if(game==='eli'){const r=canvas.getBoundingClientRect(),height=Math.max(360,Math.round(420*r.height/Math.max(1,r.width)));if(canvas.height!==height)canvas.height=height;}const dt=Math.min(.05,(now-last)/1000)||.016;last=now;if(phase==='playing'){
  const playTime=audio.time;
  if(audio.running===false||(playTime<=elapsed&&now-lastAudioProgress>2000))retry('The music paused. Tap Start Game to restart.');
  else {if(playTime>elapsed)lastAudioProgress=now;elapsed=playTime;
  if(held.has('ArrowLeft')||held.has('a'))target-=320*dt;if(held.has('ArrowRight')||held.has('d'))target+=320*dt;target=Math.max(42,Math.min(378,target));px+=(target-px)*Math.min(1,dt*24);
  time.textContent=`${Math.max(0,Math.ceil(roundSeconds[game]-elapsed))}s`;progress.value=elapsed;
 }}
 scene(elapsed,dt);if(phase==='playing'&&elapsed>=roundSeconds[game])finish();raf=requestAnimationFrame(tick);}
 raf=requestAnimationFrame(tick);if(autostart)begin();
 return()=>{disposed=true;run++;cancelAnimationFrame(raf);audio.stop();pulse.clear();document.removeEventListener('keydown',keydown);document.removeEventListener('keyup',keyup);document.removeEventListener('visibilitychange',visibility);};
}
