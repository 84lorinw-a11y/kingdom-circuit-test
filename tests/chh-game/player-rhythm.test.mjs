import test from 'node:test';import assert from 'node:assert/strict';import {act,initialState,restore,score} from '../../test-overrides/chh-show-night/state.mjs';import {avatars,playerName} from '../../test-overrides/chh-show-night/avatars.mjs';import {crowdCounts,crowdActors} from '../../test-overrides/chh-show-night/crowds.mjs';
test('Player identity persists, validates choices, and stays separate from friends',()=>{for(const a of avatars){let s=act(initialState(),'profile',{name:'  River  ',avatar:a.id});assert.equal(s.name,'River');assert.equal(s.profileReady,true);assert.equal(restore(JSON.stringify(s)).avatar,a.id);assert.deepEqual(s.friends,[]);}assert.equal(act(initialState(),'profile',{name:' ',avatar:'red'}).profileReady,false);assert.equal(act(initialState(),'profile',{name:'River',avatar:'unknown'}).profileReady,false);assert.equal(playerName('a'.repeat(60)).length,18);});
test('New and unfinished sessions require a name and an explicit character choice',()=>{
 const fresh=initialState();assert.equal(fresh.name,'');assert.equal(fresh.avatar,'');assert.equal(fresh.profileReady,false);assert.equal(score(fresh),0);
 assert.equal(act(fresh,'profile',{name:'River',avatar:''}).profileReady,false);
 assert.equal(act(fresh,'profile',{name:'',avatar:'blue'}).profileReady,false);
 const restored=restore(JSON.stringify(fresh));assert.equal(restored.name,'');assert.equal(restored.avatar,'');assert.equal(restored.profileReady,false);
 const corrupt=restore(JSON.stringify({...fresh,name:'River',avatar:'removed-character',profileReady:true}));assert.equal(corrupt.profileReady,false);assert.equal(corrupt.avatar,'');
});
test('Every room has a substantial crowd',()=>{assert.deepEqual(crowdCounts,{outside:30,show:30,vip:30});});

test('Crowd bodies stay close to player size and the white boy and girl are selectable',()=>{
 for(const room of ['outside','show','vip']){
  const actors=crowdActors(room,0,true,{x:500,y:600});assert.ok(actors.every(a=>a.scale>=2.05&&a.scale<=2.4));
  assert.ok(actors.some(a=>a.who==='women:0'));assert.ok(actors.some(a=>a.who==='fan:3'));
 }
 assert.ok(avatars.some(a=>a.sprite===4));assert.ok(avatars.some(a=>a.sprite==='crowd-vip:34'));
});


test('Hands-up zone is on the main-stage floor, separate from Eli’s floor entrance',async()=>{
 const {inFrontRow}=await import('../../test-overrides/chh-show-night/worship.mjs');
 assert.equal(inFrontRow({room:'show',x:420,y:475}),true);
 assert.equal(inFrontRow({room:'show',x:700,y:475}),false);
 assert.equal(inFrontRow({room:'vip',x:510,y:475}),false);
});
