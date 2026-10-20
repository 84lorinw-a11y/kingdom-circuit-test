import {artistGames,createArtistRound} from './artist-arcade.mjs?v=apollo-19';
import {roundSchedule,roundScore,gameNames} from './scoring.mjs?v=apollo-19';
import {gameTracks} from './music-config.mjs?v=apollo-19';
import {drawScoreCard} from './round-records.mjs?v=apollo-19';
import {drawPerson} from './sprites.mjs?v=apollo-19';
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text)e.textContent=text;return e;};
const keyboard={marty:'Keys 1–3 stamp the three rows.',brenno:'Arrow keys steer.','ryan-ellis':'Up and down arrows ride the wave.','gavin-the-hotrod':'Left and right arrows change lanes.','lj-the-messenger':'Space sends an invitation.',dearis:'Arrows choose a card; Enter flips it.',tonyxtrotter:'Left and right arrows move.','andrew-prim':'Keys 1–3 sort the next asset.'};
export function mountArtistArcade(host,{game,audio,art,records,name,onFinish,onExit,onSoundToggle}){
 const config=artistGames[game],reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 let phase='ready',disposed=false,run=0,raf=0,last=0,elapsed=0,lastProgress=0,roundId='',seed=1,notes=[],events=[],engine=null,breakBefore=false,lastResult=null,cardUrl=null;
 host.className='round artist-round';host.dataset.game=game;host.dataset.phase=phase;
 const top=el('div','round-top'),exit=el('button','round-exit','← Leave'),brand=el('div','round-brand'),sound=el('button','round-sound');
 brand.append(el('small','',gameNames[game].toUpperCase()),el('strong','',config.title));
 const track=gameTracks[game],song=el('a','round-song',`♪ MARTY · ${track.title} · preview`);song.href=track.listenUrl;song.target='_blank';song.rel='noopener';brand.append(song);
 exit.onclick=onExit;function syncSound(){sound.textContent=audio.muted?'♪ Off':'♪ On';sound.setAttribute('aria-pressed',String(!audio.muted));sound.setAttribute('aria-label',audio.muted?'Enable sound':'Mute sound');}syncSound();sound.onclick=()=>{if(onSoundToggle)onSoundToggle();else audio.setMuted(!audio.muted);syncSound();};top.append(exit,brand,sound);
 const stats=el('div','round-stats'),points=el('b','','0'),time=el('b','',`${config.seconds}s`),combo=el('b','','0×');
 for(const [label,value] of [['POINTS',points],['TIME',time],['COMBO',combo]]){const group=el('div');group.append(el('small','',label),value);stats.append(group);}
 const progress=el('progress');progress.max=config.seconds;progress.value=0;progress.setAttribute('aria-label','Round progress');
 const arena=el('div','round-arena'),canvas=el('canvas');canvas.width=420;canvas.height=560;canvas.tabIndex=0;canvas.setAttribute('aria-label',`${config.instruction} ${keyboard[game]}`);arena.append(canvas);const g=canvas.getContext('2d');
 const overlay=el('div','round-overlay'),headline=el('h2','',config.title),message=el('p','',config.instruction),summary=el('p','round-results'),start=el('button','round-start','Start Game'),back=el('button','round-back','BACK TO THE SHOW'),extra=el('div','round-result-actions'),board=el('button','','GAME LEADERBOARD'),share=el('button','','SHARE SCORE'),details=el('div','round-local-board');
 summary.setAttribute('aria-live','polite');details.hidden=true;extra.hidden=true;back.onclick=onExit;extra.append(board,share);overlay.append(headline,message,summary,start,extra,details,back);arena.append(overlay);
 const hint=el('p','round-hint',config.instruction);host.append(top,stats,progress,arena,hint);
 function setPhase(value){phase=value;host.dataset.phase=value;}
 function releaseCard(){if(cardUrl){URL.revokeObjectURL(cardUrl);cardUrl=null;}}
 function createEngine(){return createArtistRound(game,{notes,seed,onResolve(note,hit,perfect){events.push({id:note.id,hit,perfect,breakBefore});breakBefore=false;points.textContent=roundScore(events).total;},onMistake(){breakBefore=true;}});}
 notes=roundSchedule(game,seed);engine=createEngine();
 async function begin(){
  const token=++run;setPhase('loading');start.disabled=true;start.textContent='Getting ready…';summary.textContent='';extra.hidden=true;details.hidden=true;details.replaceChildren();releaseCard();
  try{await Promise.all([audio.unlock(),audio.preload(game)]);if(disposed||token!==run)return;const ready=await audio.play(game);if(disposed||token!==run)return;if(!ready)throw Error('Music did not start');
   roundId=crypto.randomUUID();seed=crypto.getRandomValues(new Uint32Array(1))[0];notes=roundSchedule(game,seed);events=[];breakBefore=false;engine=createEngine();elapsed=0;lastResult=null;points.textContent='0';combo.textContent='0×';progress.value=0;time.textContent=`${config.seconds}s`;overlay.hidden=true;setPhase('playing');last=lastProgress=performance.now();canvas.focus({preventScroll:true});
  }catch{if(!disposed&&token===run)retry('Tap Start Game to turn on the music.');}
 }
 function retry(reason){run++;audio.stop();setPhase('ready');overlay.hidden=false;headline.textContent='READY WHEN YOU ARE';message.textContent=reason;start.disabled=false;start.textContent='Start Game';extra.hidden=true;details.hidden=true;}
 start.onclick=begin;
 function finish(){
  if(phase!=='playing')return;for(const n of notes)if(!n.done){n.done=true;events.push({id:n.id,hit:false,perfect:false,breakBefore});breakBefore=false;}
  audio.stop();setPhase('result');overlay.hidden=false;headline.textContent=config.result;lastResult=roundScore(events);points.textContent=lastResult.total;combo.textContent='0×';time.textContent='0s';
  message.textContent=`${lastResult.total.toLocaleString()} points added to your session.`;summary.textContent=`${lastResult.hits}/20 ${config.unit} · ${lastResult.perfect} clean · best streak ${lastResult.bestCombo}`;
  start.disabled=false;start.textContent='Play Again';extra.hidden=false;details.hidden=true;
  const data={game,id:roundId,seed,events:[...events],meta:engine.meta()};records.record(name,data);onFinish(data);
 }
 board.onclick=()=>{details.replaceChildren();details.hidden=false;const label=el('strong','','BEST ROUNDS · ON THIS DEVICE'),list=el('ol');for(const row of records.board(game)){const item=el('li');item.append(el('span','',row.name),el('b','',`${row.total} pts`));list.append(item);}details.append(label,list);share.textContent='SHARE SCORE';};
 share.onclick=async()=>{
  if(!lastResult)return;share.disabled=true;
  try{const card=document.createElement('canvas');drawScoreCard(card,{name,game,title:config.title,result:lastResult,drawPortrait:(g,x,y,who,scale)=>drawPerson(g,x,y,who,{scale})});const blob=await new Promise(resolve=>card.toBlob(resolve,'image/png'));if(disposed||!blob)return;
   const file=new File([blob],`apollo-${game}-score.png`,{type:'image/png'});
   releaseCard();cardUrl=URL.createObjectURL(blob);details.replaceChildren();details.hidden=false;const preview=el('img','score-card-preview');preview.src=cardUrl;preview.alt=`${name}: ${lastResult.total} points in ${config.title}`;const link=el('a','score-card-save','SAVE SCORE CARD');link.href=cardUrl;link.download=file.name;details.append(preview,link);
  }finally{share.disabled=false;}
 };
 function point(e){const r=canvas.getBoundingClientRect(),scale=Math.min(r.width/420,r.height/560);return {x:(e.clientX-r.left-(r.width-420*scale)/2)/scale,y:(e.clientY-r.top-(r.height-560*scale)/2)/scale};}
 canvas.onpointerdown=e=>{if(phase!=='playing')return;e.preventDefault();canvas.setPointerCapture(e.pointerId);engine.point('down',point(e));};
 canvas.onpointermove=e=>{if(phase==='playing'&&canvas.hasPointerCapture(e.pointerId))engine.point('move',point(e));};
 for(const type of ['up','cancel'])canvas['onpointer'+type]=e=>{if(phase==='playing')engine.point(type,point(e));if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);};
 const keydown=e=>{if(phase!=='playing'||e.target!==canvas)return;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' ','Enter','1','2','3'].includes(e.key)){e.preventDefault();engine.key(e.key);}};
 canvas.addEventListener('keydown',keydown);
 const visibility=()=>{if(document.hidden&&['loading','playing'].includes(phase))retry('Welcome back. Restart this round with the music.');};document.addEventListener('visibilitychange',visibility);
 function tick(now){if(disposed)return;const dt=Math.min(.05,Math.max(0,(now-last)/1000));last=now;
  if(phase==='playing'){const current=audio.time;if(audio.running===false||(current<=elapsed&&now-lastProgress>2000))retry('The music paused. Tap Start Game to restart.');else{if(current>elapsed)lastProgress=now;elapsed=current;engine.step(elapsed,dt);combo.textContent=`${engine.snapshot().combo}×`;time.textContent=`${Math.max(0,Math.ceil(config.seconds-elapsed))}s`;progress.value=elapsed;}}
  engine.draw(g,{art,reduced});if(phase==='playing'&&elapsed>=config.seconds)finish();raf=requestAnimationFrame(tick);
 }
 raf=requestAnimationFrame(tick);
 return()=>{disposed=true;run++;cancelAnimationFrame(raf);audio.stop();releaseCard();document.removeEventListener('visibilitychange',visibility);canvas.removeEventListener('keydown',keydown);};
}
