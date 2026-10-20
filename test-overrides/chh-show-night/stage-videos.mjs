import {screenPlacement,stageScreen} from './stage-screen.mjs?v=apollo-13';

export const stageVideos=Object.freeze([
 {id:'igVFE1_Dl1A',title:'We just hit 100k'},
 {id:'a0lIU4jiL6M',title:'NOT 4 $ALE — Apollo Records'},
 {id:'XyZJtJ3t0Vc',title:'no coworker music allowed'},
]);
// Shorts can wrap internally without emitting ENDED. Detect that completed loop via the public API.
export const didVideoWrap=(previous,current,duration)=>Number.isFinite(duration)&&duration>1&&previous>=duration-.8&&current<1&&previous-current>1;
export const nextVideoIndex=index=>(index+1)%stageVideos.length;
export const stageCanPlay=({room,ready,blocked,hidden,visible=0,reduced=false,requested=false,paused=false})=>
 room==='show'&&ready&&!blocked&&!hidden&&visible>=.5&&!paused&&(!reduced||requested);
export function stageEmbedUrl(index,origin){
 const params=new URLSearchParams({enablejsapi:'1',playsinline:'1',controls:'1',rel:'0',origin});
 return `https://www.youtube-nocookie.com/embed/${stageVideos[index].id}?${params}`;
}
let apiPromise;
export function loadYouTubeAPI(){
 if(window.YT?.Player)return Promise.resolve(window.YT);
 if(apiPromise)return apiPromise;
 apiPromise=new Promise((resolve,reject)=>{
  const script=document.createElement('script');let timer;
  const previous=window.onYouTubeIframeAPIReady;
  const fail=()=>{clearTimeout(timer);script.remove();apiPromise=null;window.onYouTubeIframeAPIReady=previous;reject(new Error('YouTube did not load'));};
  window.onYouTubeIframeAPIReady=()=>{clearTimeout(timer);previous?.();resolve(window.YT);};
  script.src='https://www.youtube.com/iframe_api';script.onerror=fail;
  timer=setTimeout(fail,15000);document.head.append(script);
 });
 return apiPromise;
}

// A single muted player, loaded only on entry. Its native controls stay unobscured.
export function createStageVideos({root,tools,reduced=false,loadAPI=loadYouTubeAPI,now=()=>performance.now()}){
 const play=tools.querySelector('#stage-video-toggle'),next=tools.querySelector('#stage-video-next');
 const status=tools.querySelector('#stage-video-status'),link=tools.querySelector('#stage-video-link');
 let context={},visible=0,screenFraction=1,index=0,player,ready=false,loading=false,paused=false,requested=false;
 let previousTime=0,nextSample=0,pendingMute=true;
 let geometry='',starting=false,lastLabel='',lastCommand=null,failed=new Set(),blockedAutoplay=false,loadFailed=false;
 function label(){
  const key=[index,paused,blockedAutoplay,loadFailed,requested,reduced].join(':');if(key===lastLabel)return;lastLabel=key;
  link.href=`https://www.youtube.com/shorts/${stageVideos[index].id}`;
  link.setAttribute('aria-label',`Watch ${stageVideos[index].title} on YouTube`);
  const stopped=paused||blockedAutoplay||loadFailed||(!requested&&reduced);
  play.textContent=stopped?'Play screen':'Pause screen';play.setAttribute('aria-pressed',String(!stopped));
  status.textContent=loadFailed?'Video unavailable':blockedAutoplay?'Tap Play screen':`${index+1} / 3`;
  next.disabled=loadFailed;
 }
 function allowed(){return stageCanPlay({...context,visible:Math.min(visible,screenFraction),reduced,requested,paused:paused||blockedAutoplay||loadFailed});}
 function command(){
  label();if(!ready)return;
  const wanted=allowed()?'play':'pause';if(wanted===lastCommand)return;
  lastCommand=wanted;
  if(wanted==='play'){starting=true;player.mute();player.playVideo();}else player.pauseVideo();
 }
 function select(newIndex){
  index=newIndex;previousTime=0;pendingMute=true;blockedAutoplay=false;lastCommand=null;label();
  if(!ready)return;
  player.mute();
  if(allowed()){starting=true;player.loadVideoById(stageVideos[index].id);}
  else player.cueVideoById(stageVideos[index].id);
  command();
 }
 function unavailable(){
  failed.add(index);
  if(failed.size===stageVideos.length){loadFailed=true;command();return;}
  let nextIndex=nextVideoIndex(index);while(failed.has(nextIndex))nextIndex=nextVideoIndex(nextIndex);
  select(nextIndex);
 }
 async function ensurePlayer(){
  if(player||loading||loadFailed)return;loading=true;
  try{
   const YT=await loadAPI();
   const iframe=document.createElement('iframe');iframe.title='Apollo stage films';
   iframe.src=stageEmbedUrl(index,location.origin);
   iframe.allow='autoplay; encrypted-media; fullscreen; picture-in-picture';
   iframe.referrerPolicy='strict-origin-when-cross-origin';iframe.allowFullscreen=true;
   root.replaceChildren(iframe);
   player=new YT.Player(iframe,{events:{
    onReady(){ready=true;loading=false;player.mute();command();},
    onStateChange(event){
     if(event.data===0){failed.delete(index);select(nextVideoIndex(index));}
     // Native player pause remains a user choice; room pauses do not overwrite it.
     if(event.data===2&&!starting&&lastCommand==='play'&&allowed()){paused=true;lastCommand='pause';label();}
     if(event.data===1){
      starting=false;if(pendingMute){player.mute();pendingMute=false;}
      if(!stageCanPlay({...context,visible:Math.min(visible,screenFraction),reduced:false})){lastCommand=null;command();}
      else{paused=false;requested=true;blockedAutoplay=false;lastCommand='play';label();}
     }
    },
    onAutoplayBlocked(){blockedAutoplay=true;lastCommand=null;label();},
    onError:unavailable,
   }});
  }catch{loading=false;loadFailed=true;label();}
 }
 const observer=new IntersectionObserver(entries=>{visible=entries[0]?.intersectionRatio||0;command();},{threshold:[0,.5,1]});
 observer.observe(root);
 play.onclick=()=>{
  if(loadFailed){loadFailed=false;failed.clear();paused=false;blockedAutoplay=false;requested=true;if(player)select(index);else ensurePlayer();command();return;}
  if(paused||blockedAutoplay||(!requested&&reduced)||lastCommand!=='play'){
   paused=false;blockedAutoplay=false;requested=true;
  }else paused=true;
  lastCommand=null;command();
 };
 next.onclick=()=>{failed.clear();select(nextVideoIndex(index));};
 document.addEventListener('visibilitychange',()=>{context.hidden=document.hidden;command();});
 window.addEventListener('pagehide',()=>{context.hidden=true;command();});
 label();
 return {
  update(value){
   context={...value};
   const shown=value.room==='show'&&value.ready&&!value.blocked;
   root.hidden=!shown;tools.hidden=!shown;
   if(shown){
    const box=screenPlacement(value);
    // Fit the player inside the visible part of the wall on a phone, so controls never get cut off.
    const left=Math.max(0,box.left),right=Math.min(value.width,box.left+box.width),displayWidth=Math.max(0,right-left);
    screenFraction=displayWidth/box.width;
    root.hidden=displayWidth<200;
    if(root.hidden)screenFraction=0;
    const key=[left,box.top,displayWidth,box.height,value.offsetLeft].join(':');
    if(key!==geometry){
     geometry=key;root.style.left=`${left+(value.offsetLeft||0)}px`;root.style.width=`${displayWidth/(box.width/stageScreen.width)}px`;root.style.top=`${box.top}px`;
     root.style.transform=`scale(${box.width/stageScreen.width},${box.height/stageScreen.height})`;
    }
    ensurePlayer();
   }
   command();
   const time=now();
   if(ready&&allowed()&&!starting&&player.getPlayerState()===1&&time>=nextSample){
    nextSample=time+250;
    const current=player.getCurrentTime(),duration=player.getDuration();
    status.title=`${stageVideos[index].title} · ${Math.floor(current)} / ${Math.floor(duration)} seconds`;
    if(didVideoWrap(previousTime,current,duration)){failed.delete(index);select(nextVideoIndex(index));}
    else previousTime=current;
   }
  },
  suspend(){context.hidden=true;command();},
  mute(){if(ready)player.mute();},
  get audible(){return ready&&player.getPlayerState()===1&&!player.isMuted();},
 };
}
