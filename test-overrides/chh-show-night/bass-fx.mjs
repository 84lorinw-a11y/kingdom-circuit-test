// Respond to low-frequency transients in the actual recording, not a canned beat timer.
export function createBassDetector(){
 let average=0,previous=0,lastHit=-Infinity;
 return {
  sample(energy,time){
   const hit=energy>.045&&energy>average*1.22&&energy>previous*1.06&&time-lastHit>280;
   average=average*.88+energy*.12;previous=energy;
   if(hit)lastHit=time;
   return hit;
  },
  reset(){average=0;previous=0;lastHit=-Infinity;}
 };
}

export function createBassEffects(music,container,{gain=1,reduceMotion=false}={}){
 let context,analyser,source,boost,limiter,bins,raf=0,enabled=!reduceMotion,disposed=false;
 const detector=createBassDetector(),panel=container.closest('dialog')||container;
 const viewport=document.querySelector('.viewport');let hits=0;
 const animations=[];
 function clear(){
  cancelAnimationFrame(raf);raf=0;
  animations.splice(0).forEach(a=>a.cancel());
  container.classList.remove('bass-hit');
 }
 function pulse(){
  container.dataset.bassHits=String(++hits);
  if(!enabled||reduceMotion)return;
  animations.splice(0).forEach(a=>a.cancel());
  for(const el of [panel,viewport].filter(Boolean))animations.push(el.animate([
   {transform:'translate(0,0)'},{transform:'translate(-3px,2px)'},
   {transform:'translate(3px,-1px)'},{transform:'translate(-1px,1px)'},{transform:'translate(0,0)'}
  ],{duration:140,easing:'ease-out'}));
  animations.push(container.animate([{filter:'brightness(1.13)'},{filter:'brightness(1)'}],{duration:180}));
  // A short tactile hit where supported; the visual pulse works on all devices.
  try{navigator.vibrate?.(12);}catch{}
 }
 function tick(time){
  if(disposed||music.paused||music.ended){clear();return;}
  if(analyser){
   analyser.getFloatFrequencyData(bins);
   const hz=context.sampleRate/analyser.fftSize;let power=0,count=0;
   for(let i=Math.max(1,Math.ceil(35/hz));i<=Math.floor(170/hz);i++){power+=10**(bins[i]/10);count++;}
   if(detector.sample(Math.sqrt(power/Math.max(1,count)),time))pulse();
  }
  raf=requestAnimationFrame(tick);
 }
 return {
  async prepare(){
   if(disposed)return;
   const AudioContext=window.AudioContext||window.webkitAudioContext;
   if(!AudioContext)return;
   if(!context){
    context=new AudioContext();analyser=context.createAnalyser();analyser.fftSize=2048;analyser.smoothingTimeConstant=.35;
    bins=new Float32Array(analyser.frequencyBinCount);boost=context.createGain();boost.gain.value=gain;
    limiter=context.createDynamicsCompressor();limiter.threshold.value=-3;limiter.knee.value=3;
    limiter.ratio.value=12;limiter.attack.value=.003;limiter.release.value=.12;
    source=context.createMediaElementSource(music);source.connect(analyser);analyser.connect(boost);boost.connect(limiter);limiter.connect(context.destination);
   }
   await context.resume();
  },
  start(){clear();detector.reset();if(!disposed)raf=requestAnimationFrame(tick);},
  stop:clear,
  setEnabled(value){enabled=!!value&&!reduceMotion;clear();if(!music.paused&&!music.ended)raf=requestAnimationFrame(tick);return enabled;},
  dispose(){disposed=true;clear();source?.disconnect();analyser?.disconnect();boost?.disconnect();limiter?.disconnect();context?.close().catch(()=>{});}
 };
}
