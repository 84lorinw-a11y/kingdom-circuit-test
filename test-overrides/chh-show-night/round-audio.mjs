import {djTrack,stageTracks} from './music-config.mjs?v=show-12';
// A single context is unlocked by the first real gesture and reused on every replay.
export function createRoundAudio(){
 let context,source,gain,analyser,limiter,generation=0,started=0,offset=0,active=null;const buffers=new Map();
 const tracks={eli:djTrack,...stageTracks};
 async function buffer(id){if(!buffers.has(id))buffers.set(id,fetch(tracks[id].src).then(r=>{if(!r.ok)throw Error('Music unavailable');return r.arrayBuffer();}).then(b=>context.decodeAudioData(b)).catch(e=>{buffers.delete(id);throw e;}));return buffers.get(id);}
 function unlock(){try{context??=new(window.AudioContext||window.webkitAudioContext)();const promise=context.resume();Object.keys(tracks).forEach(id=>buffer(id).catch(()=>{}));return promise;}catch{return Promise.reject(Error('Audio unavailable'));}}
 function stop(){generation++;if(source){source.onended=null;source.stop();source.disconnect();source=null;}gain?.disconnect();analyser?.disconnect();limiter?.disconnect();active=null;}
 return {unlock,stop,
 async play(id){stop();const token=generation;await unlock();if(!tracks[id])return true;const b=await buffer(id);if(token!==generation)return false;if(context.state!=='running')throw Error('Tap Start Game to enable music');source=context.createBufferSource();source.buffer=b;gain=context.createGain();gain.gain.value=id==='eli'?1.18:(tracks[id].volume??.8);analyser=context.createAnalyser();analyser.fftSize=2048;source.connect(gain);gain.connect(analyser);limiter=context.createDynamicsCompressor();limiter.threshold.value=-3;limiter.knee.value=3;limiter.ratio.value=12;limiter.attack.value=.003;limiter.release.value=.12;analyser.connect(limiter);limiter.connect(context.destination);started=context.currentTime;offset=0;active=id;source.start();return true;},
 get time(){return active?context.currentTime-started+offset:0;},get analyser(){return analyser;},get sampleRate(){return context?.sampleRate||48000;}
 };
}
