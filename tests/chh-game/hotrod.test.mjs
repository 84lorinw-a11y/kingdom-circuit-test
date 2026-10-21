import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {merchItems} from '../../test-overrides/chh-show-night/merch-items.mjs';
import {loadHotrodArt,hotrodArrivalPose,HOTROD_ARRIVAL_SECONDS} from '../../test-overrides/chh-show-night/hotrod-scene.mjs';
import {mountArtistArcade} from '../../test-overrides/chh-show-night/arcade-round.mjs';
import {createArtistRound} from '../../test-overrides/chh-show-night/artist-arcade.mjs';
import {roundSchedule,gameIds} from '../../test-overrides/chh-show-night/scoring.mjs';

test('Gavin passes never repeat the previous lane and balance all three lanes across 1,000 rounds',()=>{
 const patterns=new Set();
 for(let seed=0;seed<1000;seed++){
  const notes=roundSchedule('gavin-the-hotrod',seed),lanes=notes.map(n=>n.lane),counts=[0,0,0];
  assert.equal(lanes.length,20);
  for(let i=0;i<lanes.length;i++){assert.ok(lanes[i]>=0&&lanes[i]<3);if(i)assert.notEqual(lanes[i],lanes[i-1]);counts[lanes[i]]++;}
  assert.ok(Math.max(...counts)-Math.min(...counts)<=1);
  assert.deepEqual(roundSchedule('gavin-the-hotrod',seed),notes);
  patterns.add(lanes.join(''));
 }
 assert.ok(patterns.size>900,'rounds should vary instead of repeating one fixed rotation');
});
test('games other than Gavin and the replaced Brenno round preserve their schedules',()=>{
 const source=readFileSync(new URL('./fixtures/previous-scoring.mjs',import.meta.url),'utf8').replace(/^import[^\n]+\n/,'').replaceAll('export ','');
 const original=Function('merchItems',source+'; return roundSchedule;')(merchItems);
 for(const id of gameIds.filter(id=>!['gavin-the-hotrod','brenno'].includes(id)))for(const seed of [1,42,0xffffffff])assert.deepEqual(roundSchedule(id,seed),original(id,seed));
});

test('Gavin art loads on request once, shares concurrent loads and is reused on replay',async()=>{
 const art={},calls=[];const load=async src=>{calls.push(src);return {width:630,height:840};};
 assert.equal(calls.length,0);
 await Promise.all([loadHotrodArt(art,{load}),loadHotrodArt(art,{load})]);
 await loadHotrodArt(art,{load});
 assert.equal(calls.length,2);assert.ok(calls.every(src=>src.endsWith('.webp')));
 assert.ok(art.hotrodCar&&art.hotrodRoad);
});
test('one failed hotrod image retries without downloading the successful image again',async()=>{
 const art={},calls=[];let fail=true;
 const load=async src=>{calls.push(src);if(src.includes('road')&&fail)throw Error('offline');return {width:1,height:1};};
 await assert.rejects(loadHotrodArt(art,{load}),/offline/);fail=false;
 await loadHotrodArt(art,{load});assert.equal(calls.filter(s=>s.includes('gavin')).length,1);assert.equal(calls.length,3);
});
test('arrival begins at the current lane, ends parked and stays bounded',()=>{
 for(const x of [70,210,350]){const start=hotrodArrivalPose(x,0),end=hotrodArrivalPose(x,1);assert.equal(start.x,x);assert.equal(start.scale,1);assert.equal(end.x,230);assert.ok(end.y<start.y&&end.scale<1);
  for(let p=0;p<=1;p+=.01){const pose=hotrodArrivalPose(x,p);assert.ok(pose.x>=Math.min(x,230)&&pose.x<=Math.max(x,230));assert.ok(pose.scale>=.54);}
  assert.deepEqual(hotrodArrivalPose(x,5),end);
 }
});
test('swipes change one lane, taps choose a lane, canceled gestures do nothing',()=>{
 const r=createArtistRound('gavin-the-hotrod',{notes:roundSchedule('gavin-the-hotrod')});
 r.point('down',{x:210,y:400});r.point('up',{x:350,y:400});assert.equal(r.snapshot().lane,2);
 r.point('down',{x:210,y:400});r.point('up',{x:350,y:400});assert.equal(r.snapshot().lane,2);
 r.point('down',{x:40,y:400});r.point('cancel',{x:40,y:400});assert.equal(r.snapshot().lane,2);
 r.point('down',{x:40,y:400});r.point('up',{x:40,y:400});assert.equal(r.snapshot().lane,0);
 r.key('ArrowLeft');assert.equal(r.snapshot().lane,0);
});

// Mount the actual round controller with a small DOM/audio/RAF adapter so the
// finish, replay and interruption checks exercise the real lifecycle.
function harness({game='gavin-the-hotrod',reduced=false}={}){
 const saved=Object.fromEntries(['document','matchMedia','requestAnimationFrame','cancelAnimationFrame'].map(k=>[k,globalThis[k]]));
 const callbacks=new Map(),listeners=new Map(),recorded=[],finished=[];let serial=0,now=performance.now();
 const gradient={addColorStop(){}};
 const ctx=new Proxy({},{get:(o,k)=>o[k]??(()=>gradient),set:(o,k,v)=>(o[k]=v,true)});
 class Element{
  constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.hidden=false;this.textContent='';this.className='';}
  append(...xs){this.children.push(...xs);}replaceChildren(...xs){this.children=xs;}
  setAttribute(){}getContext(){return ctx;}focus(){}setPointerCapture(){}addEventListener(type,fn){this[type]=fn;}removeEventListener(type){delete this[type];}
  getBoundingClientRect(){return {width:390,height:594,left:0,top:0};}
 }
 globalThis.document={hidden:false,createElement:tag=>new Element(tag),addEventListener:(type,fn)=>listeners.set(type,fn),removeEventListener:type=>listeners.delete(type)};
 globalThis.matchMedia=()=>({matches:reduced});
 globalThis.requestAnimationFrame=fn=>{callbacks.set(++serial,fn);return serial;};
 globalThis.cancelAnimationFrame=id=>callbacks.delete(id);
 const audio={time:0,running:true,muted:true,unlock:async()=>{},preload:async()=>{},play:async()=>{audio.time=0;audio.running=true;return true;},stop:()=>{audio.running=false;}};
 const host=new Element('div'),art={hotrodCar:{width:380,height:570},hotrodRoad:{width:630,height:840},martyStudio:{width:640,height:960},brennoSurfer:{width:600,height:400},...Object.fromEntries(['eli','alley','studio','courtyard','soundstage'].map(k=>['arcade_'+k,{width:640,height:853}]))};
 const dispose=mountArtistArcade(host,{game,audio,art,records:{record:(...args)=>recorded.push(args),board:()=>[]},name:'Test',onFinish:data=>finished.push(data),onExit:()=>{}});
 const all=e=>[e,...e.children.flatMap(all)];const find=cls=>all(host).find(e=>e.className===cls);
 return {host,find,audio,recorded,finished,callbacks,
  tap(){all(host).find(e=>e.tag==='canvas').onpointerdown({clientX:200,clientY:400,pointerId:1,preventDefault(){}});},
  key(key,repeat=false){const canvas=all(host).find(e=>e.tag==='canvas');canvas.keydown({target:canvas,key,repeat,preventDefault(){}});},
  frame(time=audio.time){audio.time=time;const entry=callbacks.entries().next().value;assert.ok(entry);callbacks.delete(entry[0]);entry[1](now+=50);},
  hide(){document.hidden=true;listeners.get('visibilitychange')();},
  close(){dispose();Object.assign(globalThis,saved);}
 };
}
test('round banks once before arrival, reveals results, and replay banks one fresh round',async()=>{
 const h=harness();try{
  await h.find('round-start').onclick();h.frame(40);
  assert.equal(h.host.dataset.phase,'arriving');assert.equal(h.find('round-overlay').hidden,true);assert.equal(h.finished.length,1);assert.equal(h.finished[0].events.length,20);
  for(let i=0;i<Math.ceil(HOTROD_ARRIVAL_SECONDS/.05)+2;i++)h.frame();
  assert.equal(h.host.dataset.phase,'result');assert.equal(h.find('round-overlay').hidden,false);assert.equal(h.recorded.length,1);
  for(let i=0;i<20;i++)h.frame();assert.equal(h.finished.length,1);
  await h.find('round-start').onclick();assert.equal(h.host.dataset.phase,'playing');h.frame(40);
  assert.equal(h.finished.length,2);assert.notEqual(h.finished[0].id,h.finished[1].id);
 }finally{h.close();}assert.equal(h.callbacks.size,0);
});
test('hiding during arrival shows the already banked result without a duplicate award',async()=>{
 const h=harness();try{await h.find('round-start').onclick();h.frame(40);h.hide();assert.equal(h.host.dataset.phase,'result');h.frame();assert.equal(h.recorded.length,1);}finally{h.close();}
});
test('reduced motion goes directly to the parked result',async()=>{
 const h=harness({reduced:true});try{await h.find('round-start').onclick();h.frame(40);assert.equal(h.host.dataset.phase,'result');assert.equal(h.recorded.length,1);}finally{h.close();}
});
test('leaving mid-round gives no partial award and releases its animation',async()=>{
 const h=harness();await h.find('round-start').onclick();h.frame(12);h.close();assert.equal(h.recorded.length,0);assert.equal(h.callbacks.size,0);
});
test('other artist rounds keep their immediate result flow',async()=>{
 for(const game of ['ryan-ellis','lj-the-messenger','dearis','tonyxtrotter','andrew-prim']){
  const h=harness({game});try{await h.find('round-start').onclick();h.frame(45);assert.equal(h.host.dataset.phase,'result');assert.equal(h.recorded.length,1);assert.equal(h.finished[0].events.length,20);h.frame(45);assert.equal(h.recorded.length,1);}finally{h.close();}
 }
});
test('Brenno banks once, finishes on stage, and replays with a new round',async()=>{
 const h=harness({game:'brenno'});try{
  assert.equal(h.find('round-arena').children.find(e=>e.tag==='canvas').height,640);
  await h.find('round-start').onclick();let aim=.2;
  for(let id=0;id<20;id++){const speed=id<3?112:138+id*3+(id%3)*7,at=aim+90/speed;h.frame(at);h.tap();h.frame(at+.69);aim=at+.95;}
  assert.equal(h.host.dataset.phase,'arriving');assert.equal(h.finished.length,1);assert.equal(h.finished[0].meta.outcome,'won');
  assert.equal(h.finished[0].events.length,20);const first=h.finished[0].id;
  for(let i=0;i<30;i++)h.frame();assert.equal(h.host.dataset.phase,'result');assert.equal(h.finished.length,1);
  await h.find('round-start').onclick();assert.equal(h.host.dataset.phase,'playing');h.frame(40);
  assert.equal(h.finished.length,2);assert.notEqual(h.finished[1].id,first);
 }finally{h.close();}assert.equal(h.callbacks.size,0);
});
test('Brenno reduced motion shows the stage result immediately',async()=>{
 const h=harness({game:'brenno',reduced:true});try{
  await h.find('round-start').onclick();let aim=.2;
  for(let id=0;id<20;id++){const speed=id<3?112:138+id*3+(id%3)*7,at=aim+90/speed;h.frame(at);h.tap();h.frame(at+.69);aim=at+.95;}
  assert.equal(h.host.dataset.phase,'result');assert.equal(h.finished.length,1);assert.equal(h.finished[0].meta.outcome,'won');
 }finally{h.close();}
});
test('Brenno loses after three misses, banks once without a victory, and replay restores lives',async()=>{
 const h=harness({game:'brenno'});try{
  await h.find('round-start').onclick();let at=.21;
  for(let i=0;i<3;i++){h.frame(at);h.tap();h.frame(at+.95);at+=1.22;assert.equal(h.host.dataset.phase,i===2?'result':'playing');}
  assert.equal(h.find('round-overlay').children[0].textContent,'GAME OVER');assert.equal(h.finished[0].meta.reason,'misses');assert.equal(h.finished[0].meta.lives,0);assert.equal(h.finished[0].events.length,20);
  h.frame();assert.equal(h.recorded.length,1);await h.find('round-start').onclick();h.frame(.21);h.tap();h.frame(1.17);
  assert.equal(h.host.dataset.phase,'playing');assert.equal(h.recorded.length,1);
 }finally{h.close();}
});
test('Brenno timeout is a loss, and holding a key cannot launch repeatedly',async()=>{
 const h=harness({game:'brenno'});try{
  await h.find('round-start').onclick();h.frame(.9);h.key('Enter',true);h.frame(2);h.key(' ',true);h.frame(39.9);assert.equal(h.host.dataset.phase,'playing');h.frame(40);
  assert.equal(h.host.dataset.phase,'result');assert.equal(h.find('round-overlay').children[0].textContent,'GAME OVER');assert.equal(h.finished[0].meta.reason,'time');assert.equal(h.finished[0].meta.dives,0);assert.equal(h.finished[0].meta.rescues,0);
 }finally{h.close();}
});
test('Marty completes on his studio result, replays cleanly, and awards each round once',async()=>{
 const h=harness({game:'marty'});try{
  const canvas=h.find('round-arena').children.find(e=>e.tag==='canvas');assert.equal(canvas.height,640);
  await h.find('round-start').onclick();h.frame(40);
  assert.equal(h.host.dataset.phase,'result');assert.equal(h.find('round-overlay').hidden,false);
  assert.equal(h.finished.length,1);assert.equal(h.finished[0].events.length,20);
  h.frame();assert.equal(h.recorded.length,1);
  await h.find('round-start').onclick();assert.equal(h.host.dataset.phase,'playing');h.frame(40);
  assert.equal(h.finished.length,2);assert.notEqual(h.finished[0].id,h.finished[1].id);
 }finally{h.close();}assert.equal(h.callbacks.size,0);
});
test('hiding Marty mid-round offers a restart without banking a partial score',async()=>{
 const h=harness({game:'marty'});try{
  await h.find('round-start').onclick();h.frame(10);h.hide();
  assert.equal(h.host.dataset.phase,'ready');assert.equal(h.find('round-overlay').hidden,false);assert.equal(h.recorded.length,0);
 }finally{h.close();}
});
