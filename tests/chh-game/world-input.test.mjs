import test from 'node:test';
import assert from 'node:assert/strict';
import {createWorldGesture} from '../../test-overrides/chh-show-night/world-input.mjs';
const event=(x=100,y=100,id=1)=>({pointerId:id,clientX:x,clientY:y});
function setup(){const taps=[],walks=[];return {taps,walks,input:createWorldGesture({onTap:p=>taps.push(p),onWalk:p=>walks.push(p)})};}

test('Touching an artist does nothing until a completed tap',()=>{
 const {input,taps,walks}=setup(),point={x:735,y:540};
 input.down(event(),'vip');assert.equal(taps.length,0);assert.equal(input.active,true);
 input.up(event(103,101),point,'vip');assert.deepEqual(taps,[point]);assert.deepEqual(walks,[]);assert.equal(input.active,false);
});
test('Dragging from an artist or door only walks, even after returning to the starting point',()=>{
 for(const room of ['show','vip']){
  const {input,taps,walks}=setup();input.down(event(),room);
  input.move(event(112,100),{x:750,y:580},room);
  input.up(event(),{x:735,y:540},room);
  assert.deepEqual(taps,[]);assert.equal(walks.length,2);assert.equal(input.active,false);
 }
});
test('A swipe with no intermediate move event still never launches an activity',()=>{
 const {input,taps,walks}=setup();input.down(event(),'vip');input.up(event(180,100),{x:880,y:560},'vip');
 assert.equal(taps.length,0);assert.equal(walks.length,1);
});
test('Room changes and cancelled gestures cannot become taps in the new room',()=>{
 for(const mode of ['room','cancel']){
  const {input,taps,walks}=setup();input.down(event(),'show');if(mode==='cancel')input.cancel();
  input.up(event(),{x:600,y:500},'vip');assert.deepEqual(taps,[]);assert.deepEqual(walks,[]);assert.equal(input.active,false);
 }
});
test('A second finger cannot replace or finish the active gesture',()=>{
 const {input,taps}=setup();assert.equal(input.down(event(),'vip'),true);assert.equal(input.down(event(200,200,2),'vip'),false);
 input.up(event(200,200,2),{x:900,y:500},'vip');assert.equal(input.active,true);assert.equal(taps.length,0);
 input.up(event(),{x:400,y:500},'vip');assert.deepEqual(taps,[{x:400,y:500}]);
});
