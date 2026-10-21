import test from 'node:test';
import assert from 'node:assert/strict';
import {createArtistRound,artistGames} from '../../test-overrides/chh-show-night/artist-arcade.mjs';
import {roundSchedule,roundScore} from '../../test-overrides/chh-show-night/scoring.mjs';
import {loadCrowdSurfArt,diveAim,diveTarget,diveWindows,divePose,diveSpeed} from '../../test-overrides/chh-show-night/brenno-surf.mjs';
import {loadArcadeArt} from '../../test-overrides/chh-show-night/arcade-art.mjs';

function setup(seed=1){
 const notes=roundSchedule('brenno',seed),events=[];
 const round=createArtistRound('brenno',{notes,seed,onResolve:(n,hit,perfect)=>events.push({id:n.id,hit,perfect})});
 return {round,notes,events};
}
function tapCenter(round){
 const before=round.snapshot(),n=before.notes[before.index],speed=diveSpeed(n);
 const at=before.aimStart+90/speed;round.step(at,.016);round.point('down',{x:210,y:590});return at;
}
test('standing still never earns dives or points',()=>{
 const {round,events}=setup();for(let t=0;t<=40;t+=.05)round.step(t,.05);round.step(40,.05);
 assert.equal(events.length,0);assert.equal(round.snapshot().hits,0);assert.equal(round.snapshot().index,0);
 assert.equal(round.snapshot().failed,true);assert.equal(round.meta().reason,'time');
});
test('twenty well-timed launches finish before the timer and earn exactly 1000 points',()=>{
 for(const seed of [1,17,89,999]){
  const {round,events}=setup(seed);let at=0;
  for(let i=0;i<20;i++){at=tapCenter(round);assert.equal(round.snapshot().phase,'air');round.step(at+.69,.016);}
  assert.ok(at+.69<artistGames.brenno.seconds);assert.equal(round.snapshot().complete,true);
  assert.equal(roundScore(events).total,1000);assert.equal(round.meta().cleanLandings,20);
  assert.equal(round.snapshot().won,true);assert.equal(round.meta().lives,3);
  round.key(' ');round.point('down',{});round.step(40,.05);assert.equal(events.length,20);
 }
});
test('pointer-up, dragging and key-repeat while airborne do not add attempts or points',()=>{
 const {round,events}=setup();round.step(.5,.016);round.point('move',{});round.point('up',{});assert.equal(round.snapshot().flight,null);
 const at=tapCenter(round);for(let i=0;i<20;i++){round.point('down',{});round.key(' ');round.key('Enter');}
 assert.equal(events.length,0);assert.equal(round.snapshot().index,0);
 round.step(at+.7,.016);assert.equal(events.length,1);assert.equal(round.snapshot().index,1);
 round.key(' ');assert.equal(round.snapshot().flight,null,'landing recovery prevents a held key launching instantly');
});
test('early launches miss, break the streak and recover at the next crowd without restarting',()=>{
 const {round,events}=setup();const at=tapCenter(round);round.step(at+.7,.016);
 round.step(round.snapshot().aimStart+.01,.016);round.key(' ');const flight=round.snapshot().flight;
 assert.equal(flight.hit,false);round.step(flight.start+flight.duration+.01,.016);
 assert.equal(events[1].hit,false);assert.equal(round.snapshot().combo,0);assert.equal(round.snapshot().index,2);assert.equal(round.meta().rescues,1);
 const third=tapCenter(round);round.step(third+.7,.016);assert.equal(events[2].hit,true);
});
test('broad gold landing scores 40; the bright center scores 50, and tutorial windows are wider',()=>{
 const {round,notes,events}=setup();round.step(round.snapshot().aimStart+130/112,.016);round.point('down',{});const f=round.snapshot().flight;
 assert.ok(f.hit&&!f.clean);round.step(f.start+f.duration+.01,.016);assert.equal(roundScore(events).total,40);
 assert.ok(diveWindows(notes[0]).hit>diveWindows(notes[5]).hit);
});
test('aim marker, landing prediction and actual arc share the same position',()=>{
 const {round,notes}=setup();const at=tapCenter(round),s=round.snapshot(),f=s.flight,target=diveTarget(notes[0]);
 assert.ok(Math.abs(diveAim(notes[0],at-s.aimStart))<.0001);
 const start=divePose(s,at),middle=divePose(s,at+f.duration/2),end=divePose(s,at+f.duration);
 assert.equal(start.x,0);assert.ok(Math.abs(end.x-target.x)<.0001);assert.ok(middle.y<Math.min(start.y,end.y)-100);
 assert.ok(Math.abs(end.y-target.y)<.0001);
});
test('Brenno reuses Ryan’s background and fetches his small pose once, with retries',async()=>{
 const art={},calls=[],load=async url=>{calls.push(url);return {width:600,height:400};};
 await loadArcadeArt('ryan-ellis',art,{load});await loadArcadeArt('brenno',art,{load});assert.equal(calls.length,1);
 await Promise.all([loadCrowdSurfArt(art,{load}),loadCrowdSurfArt(art,{load})]);await loadCrowdSurfArt(art,{load});assert.equal(calls.length,2);
 assert.ok(calls[1].endsWith('brenno-crowd-surf-v1.webp'));
 let attempts=0;const retry=async()=>{if(++attempts===1)throw Error('offline');return {width:600,height:400};};
 const second={};await assert.rejects(loadCrowdSurfArt(second,{load:retry}),/offline/);await loadCrowdSurfArt(second,{load:retry});assert.equal(attempts,2);
});
function miss(round){round.step(round.snapshot().aimStart+.01,.016);round.key(' ');const f=round.snapshot().flight;round.step(f.start+f.duration+.01,.016);}
test('three misses end the run and later input cannot add points or attempts',()=>{
 const {round,events}=setup();
 for(let i=0;i<3;i++){miss(round);assert.equal(round.snapshot().lives,2-i);assert.equal(round.snapshot().complete,i===2);}
 assert.equal(round.snapshot().won,false);assert.equal(round.meta().outcome,'lost');assert.equal(round.meta().reason,'misses');
 round.step(20,.05);round.key('Enter');round.point('down',{});round.step(25,.05);
 assert.equal(events.length,3);assert.equal(roundScore(events).total,0);assert.equal(round.snapshot().flight,null);
 assert.equal(setup().round.snapshot().lives,3,'a new run resets all lives');
});
test('a run with two misses can still reach the stage; a third miss on the final dive loses',()=>{
 for(const misses of [2,3]){
  const {round}=setup();for(let i=0;i<20;i++){if(i>=20-misses)miss(round);else{const at=tapCenter(round);round.step(at+.69,.016);}}
  assert.equal(round.snapshot().index,20);assert.equal(round.snapshot().won,misses===2);assert.equal(round.snapshot().failed,misses===3);
 }
});
test('landing targets tighten and the arrow speeds up through three difficulty stages',()=>{
 const first={id:0},middle={id:7},last={id:19};
 assert.ok(diveWindows(first).hit>diveWindows(middle).hit);assert.ok(diveWindows(middle).hit>diveWindows(last).hit);
 assert.ok(diveSpeed(first)<diveSpeed(middle));assert.ok(diveSpeed(middle)<diveSpeed(last));
 assert.ok(2*diveWindows(last).hit/diveSpeed(last)>.24,'final gold window stays touch-friendly');
});
test('a dive that lands after the deadline cannot score or turn a timeout into a win',()=>{
 const {round,events}=setup();round.step(39.8,.05);round.key('Enter');assert.ok(round.snapshot().flight);
 round.step(41,.05);assert.equal(round.meta().reason,'time');assert.equal(events.length,0);
 round.step(42,.05);assert.equal(events.length,0);assert.equal(round.snapshot().won,false);
});
