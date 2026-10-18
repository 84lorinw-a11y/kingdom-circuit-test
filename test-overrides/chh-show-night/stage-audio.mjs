// Unlock one long-lived audio context during a real tap/key press. Arrival at a
// listening circle happens later, after the movement animation has finished.
export function createStagePlayback({tracks,contextFactory=()=>new (window.AudioContext||window.webkitAudioContext)(),fetchAudio=src=>fetch(src),onState=()=>{}}){
 let context=null,source=null,gain=null,active=null,offset=0,startedAt=0,generation=0,wanted=false,status='idle';
 const buffers=new Map();
 const report=value=>{status=value;onState(value,active);};
 function load(id){
  if(!buffers.has(id)){
   const promise=fetchAudio(tracks[id].src).then(response=>{
    if(!response.ok)throw new Error('Track unavailable');
    return response.arrayBuffer();
   }).then(bytes=>context.decodeAudioData(bytes)).catch(error=>{buffers.delete(id);throw error;});
   buffers.set(id,promise);
  }
  return buffers.get(id);
 }
 function stop(){
  generation++;
  if(source){source.onended=null;source.stop();source.disconnect();source=null;}
  gain?.disconnect();gain=null;
 }
 async function start(){
  const id=active,version=++generation;
  if(!wanted||!tracks[id]?.src)return;
  if(!context||context.state!=='running'){report('waiting');return;}
  report('loading');
  try{
   const buffer=await load(id);
   if(version!==generation||!wanted||active!==id)return;
   if(context.state!=='running'){report('waiting');return;}
   if(offset>=buffer.duration)offset=0;
   source=context.createBufferSource();source.buffer=buffer;
   gain=context.createGain();gain.gain.value=tracks[id].volume??.8;
   source.connect(gain);gain.connect(context.destination);
   source.onended=()=>{
    if(version!==generation)return;
    source.disconnect();gain.disconnect();source=null;gain=null;
    offset=0;wanted=false;report('ended');
   };
   startedAt=context.currentTime-offset;
   source.start(0,offset);report('playing');
  }catch{if(version===generation){stop();wanted=false;report('error');}}
 }
 function pause(){
  if(source)offset=Math.max(0,context.currentTime-startedAt);
  wanted=false;stop();report(active?'paused':'idle');
 }
 return{
  // Call synchronously inside the user gesture, before fetching/decoding audio.
  unlock(){
   try{
    context??=contextFactory();
    const resumed=context.resume();
    for(const id of Object.keys(tracks))if(tracks[id].src)load(id).catch(()=>{});
    return Promise.resolve(resumed).then(()=>{
     if(wanted&&!source)return start();
    }).catch(()=>{if(wanted&&!source)report('waiting');});
   }catch{if(wanted)report('error');return Promise.resolve();}
  },
  enter(id){stop();active=tracks[id]?.src?id:null;offset=0;wanted=!!active;if(active)return start();report('idle');},
  play(){if(!active||source)return;wanted=true;return start();},
  pause,
  leave(){pause();active=null;offset=0;report('idle');},
  get playing(){return active&&source&&context?.state==='running'?active:null;},
  get wantsPlay(){return wanted;},
  get status(){return status;}
 };
}
