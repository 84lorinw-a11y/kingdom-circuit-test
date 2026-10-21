import {screenPlacement,stageScreen} from './stage-screen.mjs?v=apollo-22';

// Owner-supplied draft recording, exported without an audio stream.
export const stageFilm={
 src:'/play/assets/video/apollo-stage-draft-v2.mp4',
 poster:'/play/assets/video/apollo-stage-draft-v1.jpg',
};
export const stageCanPlay=({room,ready,blocked,hidden,visible=0,reduced=false,requested=false,paused=false})=>
 room==='show'&&ready&&!blocked&&!hidden&&visible>=.5&&!paused&&(!reduced||requested);

export function createStageVideos({root,tools,reduced=false}){
 const play=tools.querySelector('#stage-video-toggle'),status=tools.querySelector('#stage-video-status');
 let context={},visible=0,screenFraction=1,video,poster,paused=false,requested=false;
 let geometry='',lastLabel='',lastCommand=null,playAttempt=0,blockedAutoplay=false,failed=false;
 function allowed(){return stageCanPlay({...context,visible:Math.min(visible,screenFraction),reduced,requested,paused:paused||blockedAutoplay||failed});}
 function silence(){
  if(!video)return;
  if(!video.muted)video.muted=true;
  if(video.volume!==0)video.volume=0;
 }
 function label(){
  const key=[paused,blockedAutoplay,failed,requested,reduced].join(':');if(key===lastLabel)return;lastLabel=key;
  const stopped=paused||blockedAutoplay||failed||(!requested&&reduced);
  play.textContent=failed?'Retry video':stopped?'Play screen':'Pause screen';
  play.setAttribute('aria-pressed',String(!stopped));
  status.textContent=failed?'Video unavailable':blockedAutoplay?'Tap Play screen':'Silent loop';
 }
 function command(){
  label();if(!video)return;
  silence();
  const wanted=allowed()?'play':'pause';if(wanted===lastCommand)return;
  lastCommand=wanted;const attempt=++playAttempt;
  if(wanted==='pause'){video.pause();return;}
  Promise.resolve(video.play()).then(()=>{
   // A pending play can finish after a room change or while the menu is open.
   if(!allowed()){video.pause();lastCommand='pause';}
  }).catch(error=>{
   if(attempt!==playAttempt||!allowed())return;
   lastCommand=null;
   if(error.name==='NotAllowedError'){blockedAutoplay=true;label();}
   else if(error.name==='AbortError'){paused=true;label();}
   else unavailable();
  });
 }
 function unavailable(){
  failed=true;video.hidden=true;command();
 }
 function ensureVideo(){
  if(video)return;
  poster=document.createElement('img');
  poster.src=stageFilm.poster;poster.alt='';poster.draggable=false;
  video=document.createElement('video');
  video.src=stageFilm.src;video.poster=stageFilm.poster;
  video.preload='none';video.loop=true;video.defaultMuted=true;video.muted=true;video.volume=0;
  video.playsInline=true;video.controls=false;video.disablePictureInPicture=true;
  video.setAttribute('muted','');video.setAttribute('playsinline','');
  video.setAttribute('aria-hidden','true');video.tabIndex=-1;
  video.addEventListener('volumechange',silence);
  video.addEventListener('play',()=>{silence();if(!allowed())video.pause();});
  video.addEventListener('error',unavailable);
  root.replaceChildren(poster,video);
 }
 const observer=new IntersectionObserver(entries=>{visible=entries[0]?.intersectionRatio||0;command();},{threshold:[0,.5,1]});
 observer.observe(root);
 play.onclick=()=>{
  if(failed){failed=false;video.hidden=false;video.load();paused=false;requested=true;}
  else if(paused||blockedAutoplay||(!requested&&reduced)){paused=false;requested=true;}
  else paused=true;
  blockedAutoplay=false;lastCommand=null;command();
 };
 document.addEventListener('visibilitychange',()=>{context.hidden=document.hidden;command();});
 window.addEventListener('pagehide',()=>{context.hidden=true;command();});
 label();
 return {
  update(value){
   context={...value};
   const shown=value.room==='show'&&value.ready&&!value.blocked&&!value.hidden;
   root.hidden=!shown;
   if(shown){
    const box=screenPlacement(value);
    const visibleWidth=Math.max(0,Math.min(value.width,box.left+box.width)-Math.max(0,box.left));
    screenFraction=visibleWidth/box.width;root.hidden=visibleWidth<=0;
    // Keep the picture fixed to the wall as the phone camera pans past it.
    const key=[box.left,box.top,box.width,box.height,value.offsetLeft].join(':');
    if(key!==geometry){
     geometry=key;root.style.left=`${box.left+(value.offsetLeft||0)}px`;root.style.top=`${box.top}px`;
     root.style.width=`${stageScreen.width}px`;
     root.style.transform=`scale(${box.width/stageScreen.width},${box.height/stageScreen.height})`;
    }
    if(visibleWidth>0)ensureVideo();
   }
   command();
  },
  get frame(){
   if(video?.readyState>=2&&!failed)return video;
   return poster?.complete&&poster.naturalWidth?poster:null;
  },
  get controls(){return tools;},
  suspend(){context.hidden=true;command();},
  mute:silence,
 };
}
