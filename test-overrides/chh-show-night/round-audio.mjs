import {djTrack,stageTracks,merchTrack,crewTracks,venueTrack} from './music-config.mjs?v=apollo-25';
const bounded=(promise,ms,message)=>new Promise((resolve,reject)=>{
 const timer=setTimeout(()=>reject(Error(message)),ms);
 Promise.resolve(promise).then(value=>{clearTimeout(timer);resolve(value);},error=>{clearTimeout(timer);reject(error);});
});
// Music and effects share one context, unlocked inside a real tap on mobile.
export function createRoundAudio({contextFactory=()=>new(window.AudioContext||window.webkitAudioContext)({latencyHint:'interactive'}),fetchAudio=(...args)=>fetch(...args),resumeTimeoutMs=1800,loadTimeoutMs=15000}={}){
 let context,source,gain,analyser,limiter,master,generation=0,started=0,active=null,muted=false,primed=false;
 let roomSource=null,roomGain=null,roomWanted=false,roomLoading=false,roomGeneration=0,roomOffset=0,roomStarted=0;
 const buffers=new Map(),tracks={eli:djTrack,...stageTracks,...crewTracks,apollo:merchTrack,venue:venueTrack};
 function ensureContext(){
  if(!context||context.state==='closed'){
   context=contextFactory();master=context.createGain();master.gain.value=muted?0:1;master.connect(context.destination);primed=false;
  }
  return context;
 }
 function unlock(){
  try{
   // Use the phone's media playback channel where the browser supports it.
   try{if(globalThis.navigator?.audioSession)navigator.audioSession.type='playback';}catch{}
   const ctx=ensureContext(),resumed=ctx.resume();
   if(!primed&&ctx.createBuffer){const silence=ctx.createBufferSource();silence.buffer=ctx.createBuffer(1,1,ctx.sampleRate);silence.connect(master);silence.onended=()=>silence.disconnect();silence.start();primed=true;}
   return bounded(resumed,resumeTimeoutMs,'Tap Start Game to enable music').then(()=>{if(ctx.state!=='running')throw Error('Tap Start Game to enable music');startRoom();return true;});
  }catch(error){return Promise.reject(error);}
 }
 function buffer(id){
  if(!tracks[id])return Promise.reject(Error('Unknown song'));
  const key=tracks[id].src;
  if(!buffers.has(key)){
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),loadTimeoutMs),ctx=ensureContext();
   const pending=bounded(fetchAudio(tracks[id].src,{signal:controller.signal}).then(r=>{if(!r.ok)throw Error('Music unavailable');return r.arrayBuffer();}).then(data=>ctx.decodeAudioData(data)),loadTimeoutMs,'Music took too long to load');
   buffers.set(key,pending);pending.catch(()=>{if(buffers.get(key)===pending)buffers.delete(key);}).finally(()=>clearTimeout(timer));
  }
  return buffers.get(key);
 }
 function stop(){
  generation++;active=null;
  if(source){source.onended=null;try{source.stop();}catch{}source.disconnect();source=null;}
  gain?.disconnect();analyser?.disconnect();limiter?.disconnect();gain=analyser=limiter=null;
 }
 function pauseRoom(){
  roomGeneration++;roomLoading=false;
  if(roomSource){
   roomOffset=(roomOffset+Math.max(0,context.currentTime-roomStarted))%roomSource.buffer.duration;
   try{roomSource.stop();}catch{}roomSource.disconnect();roomSource=null;
  }
  roomGain?.disconnect();roomGain=null;
 }
 async function startRoom(){
  // A room change cannot unlock autoplay. The player's first real gesture does.
  if(!roomWanted||muted||active||roomSource||roomLoading||context?.state!=='running')return false;
  const token=++roomGeneration;roomLoading=true;
  try{
   const b=await buffer('venue');
   if(token!==roomGeneration||!roomWanted||muted||active||context.state!=='running')return false;
   roomSource=context.createBufferSource();roomSource.buffer=b;roomSource.loop=true;
   roomGain=context.createGain();roomGain.gain.value=venueTrack.volume;
   roomSource.connect(roomGain);roomGain.connect(master);
   roomOffset%=b.duration;roomStarted=context.currentTime;roomSource.start(0,roomOffset);return true;
  }catch{return false;}finally{if(token===roomGeneration)roomLoading=false;}
 }
 function setAmbience(value){
  const wanted=!!value;
  if(wanted===roomWanted)return;
  roomWanted=wanted;
  if(wanted)startRoom();else pauseRoom();
 }
 function effect(kind='up'){
  if(muted)return;
  try{
   const ctx=ensureContext();if(ctx.state!=='running')return;
   const notes=kind==='photo'?[440,554,659,880]:kind==='step'?[180]:[523,659,784];
   notes.forEach((hz,i)=>{const o=ctx.createOscillator(),g=ctx.createGain(),t=ctx.currentTime+i*.09;o.type='triangle';o.frequency.value=hz;g.gain.setValueAtTime(.045,t);g.gain.exponentialRampToValueAtTime(.001,t+.15);o.connect(g);g.connect(master);o.onended=()=>{o.disconnect();g.disconnect();};o.start(t);o.stop(t+.16);});
  }catch{}
 }
 return {unlock,stop,effect,setAmbience,preload:buffer,warmup:()=>Promise.allSettled(['eli'].map(buffer)),
  setMuted(value){muted=!!value;if(master)master.gain.value=muted?0:1;if(muted)pauseRoom();else startRoom();return muted;},
  get ambiencePlaying(){return !!roomSource&&!muted&&context?.state==='running';},
  get muted(){return muted;},get running(){return !!active&&context?.state==='running';},
  async play(id){
   setAmbience(false);stop();const token=generation;await unlock();if(token!==generation)return false;
   const b=await buffer(id);if(token!==generation)return false;if(context.state!=='running')throw Error('Tap Start Game to enable music');
   source=context.createBufferSource();source.buffer=b;source.loop=!!tracks[id].loop;gain=context.createGain();gain.gain.value=id==='eli'?1.18:(tracks[id].volume??.8);analyser=context.createAnalyser();analyser.fftSize=2048;
   source.connect(gain);gain.connect(analyser);limiter=context.createDynamicsCompressor();limiter.threshold.value=-3;limiter.knee.value=3;limiter.ratio.value=12;limiter.attack.value=.003;limiter.release.value=.12;analyser.connect(limiter);limiter.connect(master);
   started=context.currentTime;source.start();active=id;return true;
  },
  get time(){return active?context.currentTime-started:0;},get analyser(){return analyser;},get sampleRate(){return context?.sampleRate||48000;}
 };
}
