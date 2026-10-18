// Respond to low-frequency transients in the actual recording, not a canned beat timer.
export function createBassDetector(){
 let average=0,previous=0,lastHit=-Infinity;
 return {
  sample(energy,time){
   const hit=energy>.03&&energy>average*1.18&&energy>previous*1.04&&time-lastHit>260;
   average=average*.88+energy*.12;previous=energy;
   if(hit)lastHit=time;
   return hit;
  },
  reset(){average=0;previous=0;lastHit=-Infinity;}
 };
}

// Animate the whole game panel in CSS pixels so phones get a visible bass kick.
export function createBassPulse(targets,{mobile=false,reduceMotion=false,vibrate=pattern=>navigator.vibrate?.(pattern)}={}){
 let animations=[],enabled=!reduceMotion;
 const distance=mobile?14:8,tilt=mobile?.7:.35;
 const frames=[[0,0,0],[-1,.5,-1],[.9,-.45,1],[-.65,-.3,-.7],[.45,.3,.4],[-.2,0,-.2],[0,0,0]]
  .map(([x,y,r])=>({transform:`translate(${x*distance}px,${y*distance}px) rotate(${r*tilt}deg)`}));
 function clear(){animations.splice(0).forEach(a=>a.cancel());try{vibrate(0);}catch{}}
 return {
  hit(){
   if(!enabled)return false;
   clear();
   for(const target of new Set(targets.filter(Boolean)))animations.push(target.animate(frames,{duration:280,easing:'ease-out'}));
   // Longer double kick, rather than the old barely perceptible 12ms buzz.
   try{vibrate([70,30,45]);}catch{}
   return true;
  },
  clear,
  setEnabled(value){enabled=!!value&&!reduceMotion;clear();return enabled;}
 };
}

export function createBassEffects(music,container,{gain=1,reduceMotion=false}={}){
 let context,analyser,source,boost,limiter,bins,raf=0,disposed=false;
 const detector=createBassDetector(),panel=container.closest('dialog')||container;
 const viewport=document.querySelector('.viewport');let hits=0;
 const pulse=createBassPulse([panel,viewport],{reduceMotion,mobile:matchMedia('(pointer: coarse), (max-width: 700px)').matches});
 function clear(){
  cancelAnimationFrame(raf);raf=0;
  pulse.clear();
 }
 function tick(time){
  if(disposed||music.paused||music.ended){clear();return;}
  if(analyser){
   analyser.getFloatFrequencyData(bins);
   const hz=context.sampleRate/analyser.fftSize;let power=0,count=0;
   for(let i=Math.max(1,Math.ceil(35/hz));i<=Math.floor(170/hz);i++){power+=10**(bins[i]/10);count++;}
   if(detector.sample(Math.sqrt(power/Math.max(1,count)),time)){
    container.dataset.bassHits=String(++hits);pulse.hit();
   }
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
  setEnabled(value){return pulse.setEnabled(value);},
  dispose(){disposed=true;clear();source?.disconnect();analyser?.disconnect();boost?.disconnect();limiter?.disconnect();context?.close().catch(()=>{});}
 };
}
