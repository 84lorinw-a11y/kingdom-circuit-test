import {stageTracks} from './music-config.mjs';
export const stageSpots=[
 {id:'steven',x:335,y:475,label:'Steven · OUTSIDE',tag:'STEVEN · OUTSIDE'},
 {id:'joz',x:720,y:475,label:'Joz · BIRKENSTOCK',tag:'JOZ · BIRKENSTOCK'}
];
export const stageSpotAt=s=>s.room==='show'&&s.y>=462&&s.y<508?stageSpots.find(p=>Math.abs(s.x-p.x)<54)?.id||null:null;
export const inFrontRow=s=>!!stageSpotAt(s);
// Both listening spots are free movement zones, never a minigame or a movement lock.
export function createWorshipMusic(host){
 const bar=document.createElement('div');bar.className='worship-music';bar.hidden=true;
 const title=document.createElement('span');
 const control=document.createElement('button');control.type='button';control.textContent='PAUSE SONG';
 const audio=document.createElement('audio');audio.preload='metadata';audio.hidden=true;
 bar.append(title,control,audio);host.append(bar);let active=null,attempt=0;
 const pause=()=>{attempt++;audio.pause();control.textContent='PLAY SONG';};
 async function play(){
  const track=stageTracks[active];if(!track?.src)return;
  const id=++attempt;control.textContent='LOADING…';
  try{audio.volume=track.volume??.8;if(audio.ended)audio.currentTime=0;await audio.play();if(id!==attempt)return;if(!active){audio.pause();return;}control.textContent='PAUSE SONG';}
  catch{if(id===attempt)control.textContent='PLAY SONG';}
 }
 control.onclick=()=>audio.paused?play():pause();audio.onended=()=>{control.textContent='PLAY AGAIN';};
 document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
 return{
  enter(id){pause();active=id;const track=stageTracks[id];if(!track){bar.hidden=true;return;}title.textContent=`♪ ${track.title} · ${track.artist} · ${track.durationSeconds}-second excerpt`;audio.dataset.track=id;bar.hidden=false;control.disabled=false;if(track.src){audio.src=track.src;audio.currentTime=0;play();}else{control.disabled=true;control.textContent='CLIP COMING SOON';}},
  leave(){active=null;pause();bar.hidden=true;},pause,
  get playing(){return active&&!audio.paused&&!audio.ended?active:null;}
 };
}
