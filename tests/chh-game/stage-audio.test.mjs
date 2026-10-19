import test from 'node:test';
import assert from 'node:assert/strict';
import {createStagePlayback} from '../../test-overrides/chh-show-night/stage-audio.mjs';

function fixture({slow=false}={}){
 let gesture=false,release;
 const ready=slow?new Promise(resolve=>{release=resolve;}):Promise.resolve();
 const sources=[],gains=[],requests=[],states=[];
 const context={state:'suspended',currentTime:0,destination:{},
  resume(){if(this.state==='suspended'&&!gesture)return Promise.reject(new Error('User activation required'));this.state='running';return Promise.resolve();},
  async decodeAudioData(){await ready;return {duration:21};},
  createBufferSource(){const source={connect(){},disconnect(){},stop(){this.stopped=true;},start(when,offset){assert.equal(context.state,'running');this.offset=offset;}};sources.push(source);return source;},
  createGain(){const gain={gain:{value:0},connect(){},disconnect(){}};gains.push(gain);return gain;}
 };
 const player=createStagePlayback({
  tracks:{brenno:{src:'brenno.m4a',volume:.8},marty:{src:'marty.m4a',volume:1}},
  contextFactory:()=>context,
  fetchAudio:async src=>{requests.push(src);return {ok:true,arrayBuffer:async()=>new ArrayBuffer(1)};},
  onState:(state,id)=>states.push([state,id])
 });
 return {player,context,sources,gains,requests,states,release,
  tap(){gesture=true;const promise=player.unlock();gesture=false;return promise;}
 };
}

test('A normal movement tap unlocks audio before delayed arrival, without a second Play tap',async()=>{
 const f=fixture();await f.tap();assert.equal(f.sources.length,0);
 await f.player.enter('brenno');
 assert.equal(f.player.playing,'brenno');assert.equal(f.sources.length,1);assert.equal(f.gains[0].gain.value,.8);
 await f.player.enter('marty');
 assert.equal(f.player.playing,'marty');assert.equal(f.sources[0].stopped,true);assert.equal(f.gains[1].gain.value,1);
 assert.deepEqual(f.requests,['brenno.m4a','marty.m4a']);
});

test('Saved arrival before the first gesture starts on the next ordinary movement tap',async()=>{
 const f=fixture();await f.player.enter('brenno');assert.equal(f.player.status,'waiting');
 await f.player.unlock();assert.equal(f.player.status,'waiting');assert.equal(f.sources.length,0);
 await f.tap();assert.equal(f.player.playing,'brenno');
});

test('Slow decoding cannot start a song after the player leaves its circle',async()=>{
 const f=fixture({slow:true});await f.tap();
 const arriving=f.player.enter('brenno');f.player.leave();f.release();await arriving;
 assert.equal(f.sources.length,0);assert.equal(f.player.status,'idle');assert.equal(f.player.wantsPlay,false);
});

test('Switching circles during loading plays only the latest artist',async()=>{
 const f=fixture({slow:true});await f.tap();
 const brenno=f.player.enter('brenno'),marty=f.player.enter('marty');f.release();await Promise.all([brenno,marty]);
 assert.equal(f.sources.length,1);assert.equal(f.player.playing,'marty');
});

test('Repeated touch/pointer events never layer duplicate sources',async()=>{
 const f=fixture({slow:true});await f.tap();const arriving=f.player.enter('brenno');
 const taps=[f.tap(),f.tap(),f.tap()];f.release();await Promise.all([arriving,...taps]);
 assert.equal(f.sources.length,1);assert.equal(f.player.playing,'brenno');
});

test('Manual pause survives unrelated taps; resume keeps the current position',async()=>{
 const f=fixture();await f.tap();await f.player.enter('brenno');f.context.currentTime=6;
 f.player.pause();await f.tap();assert.equal(f.player.status,'paused');assert.equal(f.sources.length,1);
 await f.player.play();assert.equal(f.sources[1].offset,6);assert.equal(f.player.playing,'brenno');
});

test('Completed excerpts do not auto-repeat but can be replayed',async()=>{
 const f=fixture();await f.tap();await f.player.enter('marty');f.sources[0].onended();
 await f.tap();assert.equal(f.player.status,'ended');assert.equal(f.sources.length,1);
 await f.player.play();assert.equal(f.sources[1].offset,0);assert.equal(f.player.playing,'marty');
});

test('A background pause resumes at the same position after interruption',async()=>{
 const f=fixture();await f.tap();await f.player.enter('brenno');f.context.currentTime=3;
 f.player.pause();f.context.state='suspended';await f.player.play();assert.equal(f.player.status,'waiting');
 await f.tap();assert.equal(f.player.playing,'brenno');assert.equal(f.sources[1].offset,3);
});
