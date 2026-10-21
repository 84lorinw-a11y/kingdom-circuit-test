import test from 'node:test';
import assert from 'node:assert/strict';
import {loadImage} from '../../test-overrides/chh-show-night/asset-loader.mjs';
import {musicRetryMessage} from '../../test-overrides/chh-show-night/audio-errors.mjs';
import {createScoreStore} from '../../test-overrides/chh-show-night/leaderboard.mjs';

test('Damaged score saves cannot stop entry, while valid saved players survive',async()=>{
 for(const value of ['true','null','17','[]','"bad"','{']){
  const store=createScoreStore({getItem:()=>value,setItem(){}});
  assert.equal((await store.board()).rows.length,0);assert.ok(store.playerId);
 }
 const good={nickname:'Earlier Fan',total:350,journey:30,rounds:2,marty:320};
 const saved={playerId:'original-device',best:good,players:{one:good,two:null,three:{nickname:'Invalid',total:-1},four:{nickname:'Second Fan',total:0}}};
 const store=createScoreStore({getItem:()=>JSON.stringify(saved),setItem(){}});
 assert.equal(store.playerId,'original-device');
 assert.deepEqual((await store.board()).rows.map(r=>[r.nickname,r.total]),[['Earlier Fan',350],['Second Fan',0]]);
 assert.equal(store.best.marty,320);assert.equal(store.best.eli,0);
});

test('Image loading rejects failed or stalled decoding and allows a clean retry',async()=>{
 const good={width:80,height:120,decode:async()=>{}};
 assert.equal(await loadImage('/good.webp',{imageFactory:()=>good,timeoutMs:30}),good);
 await assert.rejects(loadImage('/bad.webp',{imageFactory:()=>({decode:async()=>{throw Error('invalid');}}),timeoutMs:30}),/invalid/);
 const stalled={width:80,height:120,decode:()=>new Promise(()=>{})};
 await assert.rejects(loadImage('/slow.webp',{imageFactory:()=>stalled,timeoutMs:5}),/too long/);
 assert.equal(stalled.src,'');
 assert.equal(await loadImage('/slow.webp',{imageFactory:()=>good,timeoutMs:30}),good);
 await assert.rejects(loadImage('/empty.webp',{imageFactory:()=>({width:0,height:0,decode:async()=>{}}),timeoutMs:30}),/empty/);
});

test('Music retries distinguish connection failures from a blocked playback gesture',()=>{
 for(const error of [new TypeError('Failed to fetch'),Error('Music unavailable'),Error('Music took too long to load'),{name:'EncodingError'}])assert.match(musicRetryMessage(error),/connection/);
 for(const error of [{name:'NotAllowedError'},Error('Tap Start Game to enable music')])assert.match(musicRetryMessage(error),/allow/);
 assert.match(musicRetryMessage(Error('Unknown song')),/reload/);
});
