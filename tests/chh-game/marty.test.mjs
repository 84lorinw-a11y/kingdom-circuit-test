import test from 'node:test';
import assert from 'node:assert/strict';
import {loadMartyArt,martyRowY,MARTY_HEIGHT} from '../../test-overrides/chh-show-night/marty-scene.mjs';
import {createArtistRound,itemX} from '../../test-overrides/chh-show-night/artist-arcade.mjs';

test('Marty artwork loads only on request, shares in-flight work and is reused on replay',async()=>{
 const art={},calls=[];const load=async src=>{calls.push(src);return {width:640,height:960};};
 assert.equal(calls.length,0);
 await Promise.all([loadMartyArt(art,{load}),loadMartyArt(art,{load})]);
 await loadMartyArt(art,{load});
 assert.equal(calls.length,1);assert.ok(calls[0].endsWith('/marty-studio-v1.webp'));
});
test('Marty artwork can retry after a network failure',async()=>{
 const art={};let attempt=0;
 const load=async()=>{if(++attempt===1)throw Error('offline');return {width:640,height:960};};
 await assert.rejects(loadMartyArt(art,{load}),/offline/);
 assert.equal(art.martyStudio,undefined);await loadMartyArt(art,{load});assert.equal(attempt,2);
});
test('all three desk rows have generous tap bounds and stay below Marty and above the footer',()=>{
 for(const id of [0,1,2]){
  const n={id,at:4},events=[],r=createArtistRound('marty',{notes:[n],onResolve:(n,hit,clean)=>events.push({hit,clean})});
  r.step(2,.01);const x=itemX(n,2),y=martyRowY(n);
  assert.ok(y-42>274);assert.ok(y+42<MARTY_HEIGHT-45);
  r.point('down',{x:x+63,y});r.point('down',{x,y:y+43});
  assert.equal(events.length,0,'nearby empty desk must not stamp a contract');
  r.point('down',{x:x+60,y:y+40});r.point('down',{x,y});
  assert.deepEqual(events,[{hit:true,clean:true}]);assert.equal(r.snapshot().pile,1);
 }
});
test('keyboard stamps the matching new desk row; late taps retain the original smaller reward',()=>{
 for(const id of [0,1,2]){
  const n={id,at:4},events=[],r=createArtistRound('marty',{notes:[n],onResolve:(n,hit,clean)=>events.push({hit,clean})});
  r.step(3.6,.01);r.key(String((id+1)%3+1));assert.equal(events.length,0);
  r.key(String(id+1));assert.deepEqual(events,[{hit:true,clean:false}]);
 }
});
test('the real renderer shows contracts and stamps, then clears their animation in normal and reduced motion',()=>{
 for(const reduced of [false,true]){
  const words=[],gradient={addColorStop(){}};
  const g=new Proxy({fillText:value=>words.push(value)},{get:(o,k)=>o[k]??(()=>gradient),set:(o,k,v)=>(o[k]=v,true)});
  const n={id:0,at:4},r=createArtistRound('marty',{notes:[n]});r.step(2,.01);r.draw(g,{reduced});
  assert.ok(words.includes('BUYOUT OFFER'));assert.ok(words.includes('TAP TO REJECT'));
  words.length=0;r.key('1');r.draw(g,{reduced});assert.ok(words.includes('NOT FOR SALE'));
  words.length=0;r.step(3,.01);r.draw(g,{reduced});assert.ok(!words.includes('BUYOUT OFFER'));
 }
});
