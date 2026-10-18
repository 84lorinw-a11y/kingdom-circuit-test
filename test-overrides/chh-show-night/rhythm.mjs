import {djTrack} from './music-config.mjs';
import {createBassEffects} from './bass-fx.mjs?v=bass-10';
export function beatNotes(bpm=100,firstBeatMs=null){const step=60000/bpm;return Array.from({length:10},(_,i)=>({letter:'BIBLE'[i%5],at:(firstBeatMs??step*4)+step*i,status:'pending'}));}
export function judgeTap(notes,elapsed){const target=notes.filter(n=>n.status==='pending').sort((a,b)=>Math.abs(a.at-elapsed)-Math.abs(b.at-elapsed))[0];if(!target||Math.abs(target.at-elapsed)>210)return null;target.status='hit';return{target,perfect:Math.abs(target.at-elapsed)<=95};}
export function mountRhythm(container,{best=0,rewardEarned=false,onFinish=()=>{},onActivity=()=>{}}={}){
 let notes=[],running=false,loading=false,raf=0,hit=0,combo=0,lastBeat=-1,disposed=false,generation=0;
 const music=document.createElement('audio');music.src=djTrack.src;music.preload='metadata';music.hidden=true;music.dataset.track='eli-original';music.setAttribute('aria-label','Eli Williams original B–I–B–L–E recording');
 const reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const bass=createBassEffects(music,container,{gain:djTrack.gain,reduceMotion});
 const header=document.createElement('p');header.className='rhythm-intro';header.textContent=`${djTrack.title} · Eli’s original recording`;
 const reward=document.createElement('p');reward.className='beat-reward';reward.textContent=rewardEarned?'ELI COMPLETE · +25 XP EARNED':'FINISH THIS ROUND · +25 SHOW NIGHT XP';
 const score=document.createElement('div');score.className='rhythm-score';score.innerHTML=`<span>HITS <b data-hits>0 / 10</b></span><span>YOUR BEST <b data-best>${best} / 10</b></span>`;
 const stage=document.createElement('div');stage.className='rhythm-stage';stage.setAttribute('aria-label','Beat lane. Tap when a letter reaches the gold line.');
 const target=document.createElement('div');target.className='beat-target';target.innerHTML='<span>TAP HERE</span>';stage.append(target);
 const feedback=document.createElement('p');feedback.className='beat-feedback';feedback.setAttribute('aria-live','polite');feedback.textContent='Ready? Start Game plays Eli’s song and begins the round.';
 const hint=document.createElement('p');hint.className='beat-hint';hint.textContent='Tap when a letter hits the gold line. Use TAP THE BEAT, Space, or E.';
 const tap=document.createElement('button');tap.className='beat-tap';tap.textContent='TAP THE BEAT';tap.disabled=true;
 const buttons=document.createElement('div');buttons.className='beat-start-buttons';const start=document.createElement('button');start.className='start-dj-game';start.textContent='START GAME';buttons.append(start);
 const musicRow=document.createElement('div');musicRow.className='song-controls';
 const musicStatus=document.createElement('span');musicStatus.setAttribute('aria-live','polite');musicStatus.textContent='Sound on for this game.';
 const stopMusic=document.createElement('button');stopMusic.className='secondary';stopMusic.textContent='STOP MUSIC';stopMusic.disabled=true;musicRow.append(musicStatus,stopMusic);
 const effects=document.createElement('button');effects.className='bass-toggle secondary';effects.type='button';effects.setAttribute('aria-pressed',String(!reduceMotion));effects.textContent=reduceMotion?'BASS FX OFF · REDUCED MOTION':'BASS FX · STRONG';effects.disabled=reduceMotion;
 effects.onclick=()=>{const enabled=bass.setEnabled(effects.getAttribute('aria-pressed')!=='true');effects.setAttribute('aria-pressed',String(enabled));effects.textContent=enabled?'BASS FX · STRONG':'BASS FX OFF';};
 container.append(music,header,reward,buttons,score,stage,feedback,hint,tap,musicRow,effects);
 const elapsed=()=>(music.currentTime-djTrack.offsetSeconds)*1000;
 function render(){
  if(!running||disposed)return;
  const time=elapsed(),step=60000/djTrack.bpm,beat=Math.floor(time/step);
  // Notes follow the media clock, so buffering cannot throw off the timing.
  if(beat!==lastBeat){lastBeat=beat;onActivity(beat);if(time<notes[0].at-300)feedback.textContent=`GET READY · ${Math.max(1,Math.ceil((notes[0].at-time)/step))}`;}
  notes.forEach((n,i)=>{if(n.status==='pending'&&time>n.at+210){n.status='miss';combo=0;feedback.textContent='KEEP GOING — NEXT BEAT!';}const x=22+(n.at-time)/1800*74;const el=stage.querySelector(`[data-note="${i}"]`);el.style.left=`${x}%`;el.hidden=x>105||x< -10;el.className=`beat-note ${n.status}`;});
  if(time>notes.at(-1).at+650){
   running=false;tap.disabled=true;const medal=hit===10?'PERFECT CROWD!':hit>=8?'FRONT ROW LEGEND':hit>=5?'YOU’VE GOT THE GROOVE':'GOOD VIBES. GO AGAIN!';feedback.textContent=`${medal} · ${hit}/10`;best=Math.max(best,hit);score.querySelector('[data-best]').textContent=`${best} / 10`;onFinish(hit);rewardEarned=true;reward.textContent='ELI COMPLETE · +25 XP EARNED';start.textContent='PLAY AGAIN';buttons.hidden=false;stopMusic.textContent='STOP MUSIC';
   if(!music.paused)musicStatus.textContent='Round complete. Enjoy the rest of Eli’s clip.';return;
  }
  raf=requestAnimationFrame(render);
 }
 async function begin(){
  if(running||loading||disposed)return;const id=++generation;loading=true;start.disabled=true;start.textContent='STARTING…';hit=0;combo=0;lastBeat=-1;
  music.pause();bass.stop();notes=beatNotes(djTrack.bpm,djTrack.firstBeatSeconds==null?null:djTrack.firstBeatSeconds*1000);score.querySelector('[data-hits]').textContent='0 / 10';stage.querySelectorAll('.beat-note').forEach(el=>el.remove());notes.forEach((n,i)=>{const el=document.createElement('span');el.className='beat-note';el.dataset.note=i;el.textContent=n.letter;el.hidden=true;stage.append(el);});
  try{feedback.textContent='LOADING ELI’S RECORDING…';music.currentTime=djTrack.offsetSeconds;music.muted=false;music.volume=djTrack.volume??1;await bass.prepare();if(disposed||id!==generation)return;await music.play();}
  catch{if(disposed||id!==generation)return;loading=false;start.disabled=false;start.textContent='START GAME';tap.disabled=true;musicStatus.textContent='Recording could not start.';stopMusic.disabled=true;feedback.textContent='Couldn’t play Eli’s recording. Press Start Game to retry.';return;}
  if(disposed||id!==generation){music.pause();return;}
  loading=false;start.disabled=false;buttons.hidden=true;tap.disabled=false;running=true;musicStatus.textContent='PLAYING · ELI WILLIAMS';stopMusic.disabled=false;stopMusic.textContent='STOP ROUND & MUSIC';bass.start();raf=requestAnimationFrame(render);tap.focus();
 }
 function input(){if(!running||music.paused||music.readyState<3)return;const result=judgeTap(notes,elapsed());if(result){hit++;combo++;score.querySelector('[data-hits]').textContent=`${hit} / 10`;feedback.textContent=`${result.perfect?'PERFECT!':'ON BEAT!'} ${result.target.letter} · ${combo} IN A ROW`;tap.classList.remove('hit');void tap.offsetWidth;tap.classList.add('hit');}else{combo=0;feedback.textContent='WAIT FOR THE GOLD LINE';}}
 function interrupt(message){generation++;loading=false;const wasRunning=running;running=false;cancelAnimationFrame(raf);music.pause();bass.stop();tap.disabled=true;buttons.hidden=false;start.disabled=false;start.textContent='START GAME';stopMusic.disabled=true;musicStatus.textContent=message;if(wasRunning)feedback.textContent='ROUND STOPPED. START AGAIN WHEN YOU’RE READY.';}
 stopMusic.onclick=()=>interrupt('Music stopped.');music.onended=()=>{bass.stop();musicStatus.textContent='Original clip finished.';stopMusic.disabled=true;};music.onerror=()=>{if(!disposed)interrupt('Recording unavailable. Press Start Game to retry.');};
 const keyboard=e=>{if(!running||e.repeat||![' ','e','E'].includes(e.key))return;const control=e.target.closest?.('button,a,input,select,textarea,[contenteditable="true"]');if(control&&control!==tap)return;e.preventDefault();e.stopImmediatePropagation();input();};
 const blur=()=>{if(running||loading||!music.paused)interrupt('Music paused. Press Start Game when you’re ready.');};
 tap.onpointerdown=e=>{e.preventDefault();input();};tap.onclick=e=>{if(e.detail===0)input();};start.onclick=begin;document.addEventListener('keydown',keyboard,true);window.addEventListener('blur',blur);document.addEventListener('visibilitychange',blur);
 return()=>{disposed=true;generation++;running=false;loading=false;cancelAnimationFrame(raf);music.onended=null;music.onerror=null;music.pause();bass.dispose();music.removeAttribute('src');music.load();music.remove();document.removeEventListener('keydown',keyboard,true);window.removeEventListener('blur',blur);document.removeEventListener('visibilitychange',blur);};
}
