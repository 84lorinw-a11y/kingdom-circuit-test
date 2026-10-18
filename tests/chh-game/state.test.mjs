import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,act,score,coins,restore} from '../../test-overrides/chh-show-night/state.mjs';
test('Complete journey earns exactly 125; coins are spent once',()=>{
 let s=initialState();s=act(s,'enter');assert.equal(s.room,'outside');s=act(s,'invite','jay');s=act(s,'invite','jay');assert.equal(score(s),15);s=act(s,'invite','grace');assert.equal(score(s),30);s=act(s,'enter');assert.equal(s.room,'show');s=act(s,'vip');assert.equal(s.room,'vip');s=act(s,'show');s=act(s,'merch','mint');assert.equal(coins(s),10);assert.equal(score(s),50);s=act(s,'merch','black');assert.equal(s.merch,'mint');s=act(s,'worship');assert.equal(score(s),75);s=act(s,'beat',6);assert.equal(score(s),100);s=act(s,'beat',9);assert.equal(score(s),100);s=act(s,'vip');assert.equal(s.room,'vip');s=act(s,'photo');assert.equal(score(s),125);s=act(s,'photo');assert.equal(score(s),125);s=act(s,'show');s=act(s,'outside');assert.equal(s.room,'outside');assert.equal(score(s),125);
});
test('Saved progress survives reload and rejects corrupt data',()=>{
 assert.deepEqual(restore('broken'),initialState());assert.deepEqual(restore('{}'),initialState());let s=initialState();for(const [a,v] of [['invite','jay'],['invite','grace'],['enter'],['merch','cream'],['worship'],['vip'],['photo']])s=act(s,a,v);const restored=restore(JSON.stringify(s));assert.equal(score(restored),100);assert.equal(restored.room,'vip');assert.equal(restored.merch,'cream');
 const invalid=restore(JSON.stringify({version:1,friends:['jay','jay','fake'],room:'vip',worship:true,photo:true,merch:'mint',entered:true}));assert.equal(score(invalid),15);assert.equal(invalid.room,'outside');
});

test('Worship is freely available before merch and survives a save without awarding twice',()=>{
 let s=initialState();for(const [a,v] of [['invite','jay'],['invite','grace'],['enter'],['worship']])s=act(s,a,v);
 assert.equal(s.worship,true);assert.equal(s.merch,null);assert.equal(score(s),55);s=restore(JSON.stringify(s));assert.equal(s.worship,true);assert.equal(score(act(s,'worship')),55);
 assert.equal(act(s,'vip').room,'vip');s=act(s,'merch','black');s=act(s,'vip');s=act(s,'photo');assert.equal(score(s),100);
});

test('VIP styling is validated, saved, and compatible with older saves',()=>{
 let s=initialState();assert.deepEqual(s.photoStyle,{pose:'classic',frame:'gold'});
 assert.deepEqual(act(s,'photoStyle',{pose:'lean',frame:'mint'}).photoStyle,s.photoStyle);
 for(const [a,v] of [['invite','jay'],['invite','grace'],['enter'],['merch','cream'],['worship'],['vip']])s=act(s,a,v);
 s=act(s,'photoStyle',{pose:'lean',frame:'mint'});s=act(s,'photo');
 const saved=restore(JSON.stringify(s));assert.deepEqual(saved.photoStyle,{pose:'lean',frame:'mint'});assert.equal(score(saved),100);assert.equal(coins(saved),10);
 assert.deepEqual(act(s,'photoStyle',{pose:'bad',frame:'javascript:bad'}).photoStyle,{pose:'classic',frame:'gold'});
 delete s.photoStyle;assert.deepEqual(restore(JSON.stringify(s)).photoStyle,{pose:'classic',frame:'gold'});
});


test('VIP and its photo work before merch or worship, including after reload',()=>{
 let s=initialState();for(const [a,v] of [['invite','jay'],['invite','grace'],['enter'],['vip'],['photo']])s=act(s,a,v);
 assert.equal(s.room,'vip');assert.equal(s.merch,null);assert.equal(s.worship,false);assert.equal(score(s),55);assert.equal(coins(s),20);
 s=restore(JSON.stringify(s));assert.equal(s.room,'vip');assert.equal(s.photo,true);assert.equal(score(s),55);
 s=act(s,'photo');assert.equal(score(s),55);s=act(s,'show');s=act(s,'worship');s=act(s,'merch','cream');assert.equal(score(s),100);
});
