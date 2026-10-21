import {stageTracks} from './music-config.mjs?v=apollo-25';
import {createStagePlayback} from './stage-audio.mjs?v=apollo-25';
import {apolloCrew} from './apollo-crew.mjs?v=apollo-25';
export const stageSpots=[
 {id:'brenno',x:360,y:449,label:'Brenno',tag:'BRENNO · PLAY',hideLabel:true},
 {id:'marty',x:465,y:449,label:'Marty',tag:'MARTY · PLAY',hideLabel:true},
 ...apolloCrew.filter(p=>['gavin-the-hotrod','tonyxtrotter','ryan-ellis','lj-the-messenger','dearis'].includes(p.id)).map(p=>({id:p.id,x:p.stageX,y:449,label:p.name,tag:p.name,hideLabel:true}))
];
export function stageArtistAt({x,y}){
 return stageSpots.find(spot=>{const person=apolloCrew.find(p=>p.id===spot.id);return Math.abs(x-person.stageX)<30&&y>person.stageY-145&&y<person.stageY;})?.id||null;
}
export const stageSpotAt=s=>s.room==='show'&&s.y>=462&&s.y<508?stageSpots.filter(p=>Math.abs(s.x-p.x)<34).sort((a,b)=>Math.abs(s.x-a.x)-Math.abs(s.x-b.x))[0]?.id||null:null;
export const inFrontRow=s=>!!stageSpotAt(s);
// Both listening spots are free movement zones, never a minigame or a movement lock.
export function createWorshipMusic(host){
 const bar=document.createElement('div');bar.className='worship-music';bar.hidden=true;
 const title=document.createElement('span');
 const control=document.createElement('button');control.type='button';control.textContent='PAUSE SONG';
 bar.append(title,control);host.append(bar);let resumeOnVisible=false;
 const playback=createStagePlayback({tracks:stageTracks,onState:(state,id)=>{
  bar.dataset.playback=state;bar.dataset.track=id||'';
  control.textContent={idle:'PLAY SONG',waiting:'TAP TO ENABLE MUSIC',loading:'LOADING…',playing:'PAUSE SONG',paused:'PLAY SONG',ended:'PLAY AGAIN',error:'RETRY SONG'}[state];
 }});
 // Mobile Safari requires activation in the tap itself, not the later walk/RAF.
 const unlock=event=>{if(event.isTrusted&&!control.contains(event.target))playback.unlock();};
 for(const event of ['pointerdown','pointerup','touchend','click','keydown'])document.addEventListener(event,unlock,{capture:true,passive:true});
 control.onclick=()=>{if(playback.wantsPlay&&playback.status!=='waiting'&&playback.status!=='error')playback.pause();else{playback.unlock();playback.play();}};
 document.addEventListener('visibilitychange',()=>{
  if(document.hidden){resumeOnVisible=playback.wantsPlay;playback.pause();}
  else if(resumeOnVisible){resumeOnVisible=false;playback.unlock();playback.play();}
 });
 return{
  enter(id){const track=stageTracks[id];if(!track){playback.leave();bar.hidden=true;return;}title.textContent=`♪ ${track.title} · ${track.artist} · ${track.durationSeconds}-second excerpt`;bar.hidden=false;control.disabled=!track.src;playback.enter(id);if(!track.src)control.textContent='CLIP COMING SOON';},
  leave(){resumeOnVisible=false;playback.leave();bar.hidden=true;},
  pause(){resumeOnVisible=false;playback.pause();},
  get playing(){return playback.playing;}
 };
}
