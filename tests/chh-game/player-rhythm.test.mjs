import test from 'node:test';import assert from 'node:assert/strict';import {act,initialState,restore,score} from '../../test-overrides/chh-show-night/state.mjs';import {avatars,playerName} from '../../test-overrides/chh-show-night/avatars.mjs';import {crowdCounts,crowdActors} from '../../test-overrides/chh-show-night/crowds.mjs';
import {playerSpritePose,avatarFor} from '../../test-overrides/chh-show-night/avatars.mjs';
test('Player identity persists, validates choices, and stays separate from friends',()=>{for(const a of avatars){let s=act(initialState(),'profile',{name:'  River  ',avatar:a.id});assert.equal(s.name,'River');assert.equal(s.profileReady,true);assert.equal(restore(JSON.stringify(s)).avatar,a.id);assert.deepEqual(s.friends,[]);}assert.equal(act(initialState(),'profile',{name:' ',avatar:'red'}).profileReady,false);assert.equal(act(initialState(),'profile',{name:'River',avatar:'unknown'}).profileReady,false);assert.equal(playerName('a'.repeat(60)).length,18);});
test('New and unfinished sessions require a name and an explicit character choice',()=>{
 const fresh=initialState();assert.equal(fresh.name,'');assert.equal(fresh.avatar,'');assert.equal(fresh.profileReady,false);assert.equal(score(fresh),0);
 assert.equal(act(fresh,'profile',{name:'River',avatar:''}).profileReady,false);
 assert.equal(act(fresh,'profile',{name:'',avatar:'blue'}).profileReady,false);
 const restored=restore(JSON.stringify(fresh));assert.equal(restored.name,'');assert.equal(restored.avatar,'');assert.equal(restored.profileReady,false);
 const corrupt=restore(JSON.stringify({...fresh,name:'River',avatar:'removed-character',profileReady:true}));assert.equal(corrupt.profileReady,false);assert.equal(corrupt.avatar,'');
});
test('Every room has a substantial crowd',()=>{assert.deepEqual(crowdCounts,{outside:30,show:30,vip:30});});
test('Reference player changes preserve old saves and carry the selected identity into every pose',()=>{
 const seen=new Set();
 for(const id of ['red','teal','blonde','blue','pink','sunset']){
  const before={...initialState(),name:'River',avatar:id,profileReady:true,entered:true,vipUnlocked:true,friends:['jay','grace'],totals:{...initialState().totals,marty:600}};
  const saved=restore(JSON.stringify(before)),sprite=avatarFor(saved).sprite;
  assert.equal(saved.totals.marty,600);assert.equal(saved.entered,true);assert.equal(saved.vipUnlocked,true);assert.deepEqual(saved.friends,['jay','grace']);
  const front=playerSpritePose(sprite),cheer=playerSpritePose(sprite,{hands:true}),photo=playerSpritePose(sprite,{peace:true});
  assert.equal(front.atlas,cheer.atlas);assert.equal(front.atlas,photo.atlas);
  assert.equal(cheer.cell,front.cell+3);assert.equal(photo.cell,front.cell+6);seen.add(`${front.atlas}:${front.cell}`);
 }
 assert.equal(seen.size,6);assert.equal(playerSpritePose('fan:3'),null);assert.equal(playerSpritePose('ref-player:6'),null);
});

test('Crowd bodies stay close to player size and all six reference players are selectable',()=>{
 for(const room of ['outside','show','vip']){
  const actors=crowdActors(room,0,true,{x:500,y:600});assert.ok(actors.every(a=>a.scale>=2.05&&a.scale<=2.4));
  assert.ok(actors.some(a=>a.who==='women:0'));assert.ok(actors.some(a=>a.who==='fan:3'));
 }
 assert.equal(avatars.length,6);assert.equal(new Set(avatars.map(a=>a.sprite)).size,6);
 assert.ok(avatars.every(a=>a.sprite.startsWith('ref-player:')));
});


test('Hands-up zone is on the main-stage floor, separate from Eli’s floor entrance',async()=>{
 const {inFrontRow}=await import('../../test-overrides/chh-show-night/worship.mjs');
 assert.equal(inFrontRow({room:'show',x:360,y:475}),true);
 assert.equal(inFrontRow({room:'show',x:535,y:475}),false);
 assert.equal(inFrontRow({room:'vip',x:510,y:475}),false);
});
