import test from 'node:test';import assert from 'node:assert/strict';
import {createRoundAudio} from '../../test-overrides/chh-show-night/round-audio.mjs';
import {merchTrack} from '../../test-overrides/chh-show-night/music-config.mjs';
import {roundSeconds} from '../../test-overrides/chh-show-night/scoring.mjs';
const setup=()=>{let contexts=0,plays=0,stops=0;const context={state:'suspended',currentTime:0,destination:{},sampleRate:48000,resume(){this.state='running';return Promise.resolve();},decodeAudioData:async()=>({duration:30}),createBufferSource:()=>({connect(){},disconnect(){},start(){plays++;},stop(){stops++;}}),createGain:()=>({gain:{value:0},connect(){},disconnect(){}}),createDynamicsCompressor:()=>({threshold:{},knee:{},ratio:{},attack:{},release:{},connect(){},disconnect(){}}),createAnalyser:()=>({connect(){},disconnect(){}})};globalThis.window={AudioContext:class{constructor(){contexts++;return context;}}};globalThis.fetch=async()=>({ok:true,arrayBuffer:async()=>new ArrayBuffer(8)});return {context,get contexts(){return contexts;},get plays(){return plays;},get stops(){return stops;}};};
test('Song replay reuses an unlocked context, resets time and stops the previous clip',async()=>{const env=setup(),a=createRoundAudio();await a.unlock();await a.play('eli');env.context.currentTime=7;assert.equal(a.time,7);await a.play('eli');assert.equal(a.time,0);assert.equal(env.contexts,1);assert.equal(env.plays,2);assert.equal(env.stops,1);a.stop();assert.equal(a.time,0);assert.equal(env.stops,2);});
test('Leaving while a recording decodes prevents stale audio starting',async()=>{const env=setup();let resolves=[];env.context.decodeAudioData=()=>new Promise(r=>{resolves.push(r);});const a=createRoundAudio();const pending=a.play('eli');await new Promise(r=>setImmediate(r));a.stop();resolves.forEach(resolve=>resolve({duration:30}));await pending;assert.equal(env.plays,0);});
test('Chamblissnation plays Bounce Back, restarts it on replay, and stops on exit',async()=>{
 const env=setup(),requests=[],decoded=[];
 globalThis.fetch=async src=>{requests.push(src);return {ok:true,arrayBuffer:async()=>src};};
 env.context.decodeAudioData=async src=>({src,duration:25});
 const createSource=env.context.createBufferSource;
 env.context.createBufferSource=()=>{const s=createSource(),start=s.start;s.start=()=>{decoded.push(s.buffer.src);start();};return s;};
 const a=createRoundAudio();await a.play('chamblissnation');env.context.currentTime=8;assert.equal(a.time,8);
 await a.play('chamblissnation');assert.equal(a.time,0);assert.equal(env.stops,1);
 assert.deepEqual(decoded,[merchTrack.src,merchTrack.src]);assert.equal(requests.filter(src=>src===merchTrack.src).length,1);
 assert.equal(merchTrack.title,'BOUNCE BACK');assert.equal(merchTrack.durationSeconds,roundSeconds.chamblissnation);
 a.stop();assert.equal(env.stops,2);assert.equal(a.time,0);
});
