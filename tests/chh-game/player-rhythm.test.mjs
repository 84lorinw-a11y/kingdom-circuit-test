import test from 'node:test';import assert from 'node:assert/strict';import {act,initialState,restore,score} from '../../test-overrides/chh-show-night/state.mjs';import {avatars,playerName} from '../../test-overrides/chh-show-night/avatars.mjs';import {crowdCounts,crowdActors} from '../../test-overrides/chh-show-night/crowds.mjs';
test('Player identity persists, validates choices, and stays separate from friends',()=>{for(const a of avatars){let s=act(initialState(),'profile',{name:'  River  ',avatar:a.id});assert.equal(s.name,'River');assert.equal(s.profileReady,true);assert.equal(restore(JSON.stringify(s)).avatar,a.id);assert.deepEqual(s.friends,[]);}assert.equal(act(initialState(),'profile',{name:' ',avatar:'red'}).profileReady,false);assert.equal(act(initialState(),'profile',{name:'River',avatar:'unknown'}).profileReady,false);assert.equal(playerName('a'.repeat(60)).length,18);});
test('Every room has a substantial crowd',()=>{assert.deepEqual(crowdCounts,{outside:30,show:34,vip:26});});

test('Crowd bodies stay close to player size and the white boy and girl are selectable',()=>{
 for(const room of ['outside','show','vip']){
  const actors=crowdActors(room,0,true,{x:500,y:600});assert.ok(actors.every(a=>a.scale>=2.05&&a.scale<=2.4));
  assert.ok(actors.some(a=>a.who===`crowd-${room}:4`));assert.ok(actors.some(a=>a.who===`crowd-${room}:6`));
 }
 assert.ok(avatars.some(a=>a.sprite===4));assert.ok(avatars.some(a=>a.sprite==='crowd-vip:34'));
});


test('Hands-up zone is on the main-stage floor, separate from the center DJ booth',async()=>{
 const {inFrontRow}=await import('../../test-overrides/chh-show-night/worship.mjs');
 assert.equal(inFrontRow({room:'show',x:335,y:475}),true);
 assert.equal(inFrontRow({room:'show',x:512,y:475}),false);
 assert.equal(inFrontRow({room:'vip',x:510,y:475}),false);
});
