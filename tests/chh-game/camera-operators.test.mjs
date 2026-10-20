import test from 'node:test';
import assert from 'node:assert/strict';
import {cameraActors,drawCameraFlash} from '../../test-overrides/chh-show-night/pit.mjs';
import {stageSpots} from '../../test-overrides/chh-show-night/worship.mjs';
import {practiceSpot} from '../../test-overrides/chh-show-night/practice-booth.mjs';

test('Camera operators favor the stage and take independent audience shots',()=>{
 const counts=[{stage:0,crowd:0,reposition:0},{stage:0,crowd:0,reposition:0}];
 for(let time=0;time<60000;time+=100){
  const actors=cameraActors(time);
  assert.equal(new Set(actors.map(a=>a.who)).size,2);
  assert.ok(!actors.every(a=>a.shot==='crowd'));
  actors.forEach((a,i)=>{
   counts[i][a.shot]++;
   assert.equal(a.cameraPose,a.walking?2:a.shot==='crowd'?1:0);
   assert.equal(a.video,true);
  });
 }
 for(const count of counts)assert.deepEqual(count,{stage:420,crowd:60,reposition:120});
});

test('Camera paths are continuous, slow and clear of every listening ring',()=>{
 const positions=[new Set(),new Set()];
 for(let time=0;time<=120000;time+=100){
  cameraActors(time).forEach((a,i)=>{
   positions[i].add(`${Math.round(a.x)},${Math.round(a.y)}`);
   assert.ok(a.x>220&&a.x<830&&a.y>=438&&a.y<=444);
   for(const spot of [...stageSpots,practiceSpot])assert.ok(a.y+7<spot.y-18);
   const next=cameraActors(time+100)[i];
   assert.ok(Math.hypot(next.x-a.x,next.y-a.y)<3.3,'no teleport between filming positions');
  });
 }
 assert.ok(positions.every(p=>p.size>60),'both operators actually move');
});

test('Reduced motion holds artists-facing poses and video rigs never flash',()=>{
 const first=cameraActors(0,true);
 assert.deepEqual(cameraActors(59999,true),first);
 assert.deepEqual(cameraActors(120000,true),first);
 const context=new Proxy({},{get(){throw new Error('video operator emitted a flash');}});
 for(const actor of first){
  assert.equal(actor.cameraPose,0);assert.equal(actor.walking,false);assert.equal(actor.shot,'stage');
  drawCameraFlash(context,actor,0,false);
 }
});
