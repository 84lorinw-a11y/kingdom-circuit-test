import test from 'node:test';import assert from 'node:assert/strict';
import {createRoundAudio} from '../../test-overrides/chh-show-night/round-audio.mjs';
import {merchTrack,venueTrack} from '../../test-overrides/chh-show-night/music-config.mjs';
import {roundSeconds} from '../../test-overrides/chh-show-night/scoring.mjs';
const setup=()=>{let contexts=0,plays=0,stops=0;const context={state:'suspended',currentTime:0,destination:{},sampleRate:48000,resume(){this.state='running';return Promise.resolve();},decodeAudioData:async()=>({duration:30}),createBufferSource:()=>({connect(){},disconnect(){},start(){plays++;},stop(){stops++;}}),createGain:()=>({gain:{value:0},connect(){},disconnect(){}}),createDynamicsCompressor:()=>({threshold:{},knee:{},ratio:{},attack:{},release:{},connect(){},disconnect(){}}),createAnalyser:()=>({connect(){},disconnect(){}})};globalThis.window={AudioContext:class{constructor(){contexts++;return context;}}};globalThis.fetch=async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(8)});return {context,get contexts(){return contexts;},get plays(){return plays;},get stops(){return stops;}};};
test('Song replay reuses an unlocked context, resets time and stops the previous clip',async()=>{const env=setup(),a=createRoundAudio();await a.unlock();await a.play('eli');env.context.currentTime=7;assert.equal(a.time,7);await a.play('eli');assert.equal(a.time,0);assert.equal(env.contexts,1);assert.equal(env.plays,2);assert.equal(env.stops,1);a.stop();assert.equal(a.time,0);assert.equal(env.stops,2);});
test('Leaving while a recording decodes prevents stale audio starting',async()=>{const env=setup();let resolves=[];env.context.decodeAudioData=()=>new Promise(r=>{resolves.push(r);});const a=createRoundAudio();const pending=a.play('eli');await new Promise(r=>setImmediate(r));a.stop();resolves.forEach(resolve=>resolve({duration:30}));await pending;assert.equal(env.plays,0);});
test('Apollo plays the released Marty preview, restarts it on replay, and stops on exit',async()=>{
 const env=setup(),requests=[],decoded=[];
 globalThis.fetch=async src=>{requests.push(src);return {ok:true,arrayBuffer:async()=>src};};
 env.context.decodeAudioData=async src=>({src,duration:25});
 const createSource=env.context.createBufferSource;
 env.context.createBufferSource=()=>{const s=createSource(),start=s.start;s.start=()=>{decoded.push(s.buffer.src);start();};return s;};
 const a=createRoundAudio();await a.play('apollo');env.context.currentTime=8;assert.equal(a.time,8);
 await a.play('apollo');assert.equal(a.time,0);assert.equal(env.stops,1);
 assert.deepEqual(decoded,[merchTrack.src,merchTrack.src]);assert.equal(requests.filter(src=>src===merchTrack.src).length,1);
 assert.equal(merchTrack.title,'WOW');assert.equal(merchTrack.loop,true);
 a.stop();assert.equal(env.stops,2);assert.equal(a.time,0);
});

test('Unlock is lightweight and only the selected song downloads',async()=>{
 setup();const requested=[];const a=createRoundAudio({fetchAudio:async src=>{requested.push(src);return {ok:true,arrayBuffer:async()=>new ArrayBuffer(8)};}});
 await a.unlock();assert.deepEqual(requested,[]);await a.preload('marty');await a.play('marty');assert.equal(requested.length,1);assert.match(requested[0],/marty-cult-classic-preview/);a.stop();
});
test('A stalled mobile resume times out and a later gesture can retry',async()=>{
 const env=setup();env.context.resume=()=>new Promise(()=>{});const a=createRoundAudio({resumeTimeoutMs:10});
 await assert.rejects(a.play('eli'),/Tap Start Game/);assert.equal(env.plays,0);
 env.context.resume=function(){this.state='running';return Promise.resolve();};await a.play('eli');assert.equal(env.plays,1);assert.equal(a.running,true);a.stop();
});
test('A slow or failed download releases loading and can be retried',async()=>{
 const env=setup();let stalled=true;const a=createRoundAudio({loadTimeoutMs:10,fetchAudio:()=>stalled?new Promise(()=>{}):Promise.resolve({ok:true,arrayBuffer:async()=>new ArrayBuffer(8)})});
 await assert.rejects(a.play('brenno'),/too long/);assert.equal(env.plays,0);stalled=false;await a.play('brenno');assert.equal(env.plays,1);a.stop();
});
test('One master mute controls music and effects, and audio interruptions are visible',async()=>{
 const env=setup(),gains=[],original=env.context.createGain;env.context.createGain=()=>{const g=original();gains.push(g);return g;};
 const a=createRoundAudio();a.setMuted(true);await a.play('eli');assert.equal(gains[0].gain.value,0);assert.equal(a.muted,true);
 a.setMuted(false);assert.equal(gains[0].gain.value,1);assert.equal(a.running,true);env.context.state='interrupted';assert.equal(a.running,false);await a.unlock();assert.equal(a.running,true);assert.equal(env.contexts,1);a.stop();
});
test('Supported phones request the media playback audio session',async()=>{
 const env=setup(),session={type:'auto'};Object.defineProperty(globalThis.navigator,'audioSession',{value:session,configurable:true});
 const a=createRoundAudio();await a.unlock();assert.equal(session.type,'playback');assert.equal(env.contexts,1);delete globalThis.navigator.audioSession;
});

test('Sound effects use the same working context and obey master mute',async()=>{
 const env=setup();let effects=0;
 env.context.createOscillator=()=>({frequency:{},connect(){},disconnect(){},start(){effects++;},stop(){}});
 env.context.createGain=()=>({gain:{value:0,setValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){},disconnect(){}});
 const a=createRoundAudio();await a.unlock();a.effect();assert.equal(effects,3);await a.play('marty');a.effect('step');assert.equal(effects,4);assert.equal(env.contexts,1);
 a.setMuted(true);a.effect();assert.equal(effects,4);a.stop();
});

test('Warmup loads only Eli; other previews download on demand and replay reuses them',async()=>{
 const env=setup(),requests=[];const a=createRoundAudio({fetchAudio:async src=>{requests.push(src);return {ok:true,arrayBuffer:async()=>new ArrayBuffer(8)};}});
 await a.warmup();await a.warmup();assert.equal(new Set(requests).size,1);assert.equal(requests.length,1);assert.equal(env.plays,0);
 await a.play('eli');await a.play('marty');await a.play('brenno');await a.play('apollo');assert.equal(requests.length,4);assert.equal(env.plays,4);a.stop();
});
test('Failed lightweight warmup does not block an on-demand song or retry',async()=>{
 setup();let fail=true,requests=0;const a=createRoundAudio({fetchAudio:async src=>{requests++;if(src.includes('eli-bible')&&fail)throw Error('offline');return {ok:true,arrayBuffer:async()=>new ArrayBuffer(8)};}});
 const warm=await a.warmup();assert.equal(warm.filter(r=>r.status==='rejected').length,1);await a.play('marty');assert.equal(requests,2);fail=false;await a.play('eli');assert.equal(requests,3);a.stop();
});

test('Room music waits for a gesture, loops quietly and resumes at its saved position',async()=>{
 const env=setup(),starts=[],gains=[],create=env.context.createBufferSource,makeGain=env.context.createGain;
 env.context.createBufferSource=()=>{const s=create(),start=s.start;s.start=(...args)=>{starts.push({args,loop:s.loop});start();};return s;};
 env.context.createGain=()=>{const g=makeGain();gains.push(g);return g;};
 const a=createRoundAudio();a.setAmbience(true);assert.equal(env.contexts,0);assert.equal(env.plays,0);
 await a.unlock();await new Promise(r=>setImmediate(r));assert.equal(a.ambiencePlaying,true);assert.equal(env.contexts,1);assert.equal(env.plays,1);assert.equal(starts[0].loop,true);assert.equal(gains[1].gain.value,.24);
 env.context.currentTime=9;a.setAmbience(false);assert.equal(a.ambiencePlaying,false);assert.equal(env.stops,1);
 a.setAmbience(true);await new Promise(r=>setImmediate(r));assert.equal(starts[1].args[1],9);assert.equal(a.time,0);
 for(let i=0;i<60;i++)a.setAmbience(true);assert.equal(env.plays,2);a.setAmbience(false);
});
test('The concert loads FACE LIFT on demand once and keeps minigame tracks separate',async()=>{
 const env=setup(),requests=[],sources=[];
 env.context.createBufferSource=()=>{const s={connect(){},disconnect(){},start(){sources.push(this);},stop(){}};return s;};
 const a=createRoundAudio({fetchAudio:async src=>{requests.push(src);return {ok:true,arrayBuffer:async()=>src};}});
 env.context.decodeAudioData=async src=>({src,duration:30});
 await a.unlock();assert.deepEqual(requests,[]);a.setAmbience(true);await new Promise(r=>setImmediate(r));
 assert.equal(venueTrack.title,'FACE LIFT');assert.equal(venueTrack.preview,true);assert.equal(venueTrack.generated,undefined);
 assert.equal(sources[0].buffer.src,'/play/assets/music/marty-face-lift-preview.m4a');assert.equal(sources[0].loop,true);
 a.setAmbience(false);a.setAmbience(true);await new Promise(r=>setImmediate(r));assert.equal(requests.length,1);
 await a.play('gavin-the-hotrod');assert.match(sources.at(-1).buffer.src,/marty-wow-preview/);assert.equal(a.ambiencePlaying,false);a.stop();
});
test('Artist rounds stop room music, then the room can resume without a second context',async()=>{
 const env=setup(),a=createRoundAudio();await a.unlock();a.setAmbience(true);await new Promise(r=>setImmediate(r));assert.equal(a.ambiencePlaying,true);
 await a.play('eli');assert.equal(a.running,true);assert.equal(a.ambiencePlaying,false);assert.equal(env.stops,1);
 a.stop();a.setAmbience(true);await new Promise(r=>setImmediate(r));assert.equal(a.ambiencePlaying,true);assert.equal(a.running,false);assert.equal(env.contexts,1);a.setAmbience(false);
});
test('Muted or exited rooms cannot start a stale pending preview',async()=>{
 const env=setup();let finish;env.context.decodeAudioData=()=>new Promise(resolve=>{finish=resolve;});
 const a=createRoundAudio();await a.unlock();a.setAmbience(true);await new Promise(r=>setImmediate(r));a.setMuted(true);finish({duration:30});await new Promise(r=>setImmediate(r));assert.equal(env.plays,0);
 a.setMuted(false);await new Promise(r=>setImmediate(r));assert.equal(env.plays,1);a.setAmbience(false);assert.equal(a.ambiencePlaying,false);
});
test('Leaving the room while its preview downloads prevents later playback',async()=>{
 const env=setup();let finish;env.context.decodeAudioData=()=>new Promise(resolve=>{finish=resolve;});
 const a=createRoundAudio();await a.unlock();a.setAmbience(true);await new Promise(r=>setImmediate(r));a.setAmbience(false);finish({duration:30});await new Promise(r=>setImmediate(r));assert.equal(env.plays,0);assert.equal(a.ambiencePlaying,false);
});
