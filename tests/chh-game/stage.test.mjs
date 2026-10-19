import test from 'node:test';
import assert from 'node:assert/strict';
import {stageSpotAt} from '../../test-overrides/chh-show-night/worship.mjs';
import {practiceSpot} from '../../test-overrides/chh-show-night/practice-booth.mjs';
import {crowdActors,crowdCounts,sharedCast,brennoFan,collectedFans} from '../../test-overrides/chh-show-night/crowds.mjs';

test('Each artist triggers only in front of their own stage position; Eli remains separate',()=>{
 assert.equal(stageSpotAt({room:'show',x:420,y:475}),'brenno');
 assert.equal(stageSpotAt({room:'show',x:550,y:475}),'marty');
 assert.equal(stageSpotAt({room:'show',...practiceSpot}),null);
 assert.equal(stageSpotAt({room:'show',x:367,y:540}),null);
 assert.equal(stageSpotAt({room:'vip',x:367,y:475}),null);
});
test('The same balanced cast attends all three rooms, without duplicate people',()=>{
 assert.deepEqual(crowdCounts,{outside:30,show:30,vip:30});
 assert.deepEqual(sharedCast.reduce((n,p)=>(n[p.appearance]=(n[p.appearance]||0)+1,n),{}),{Black:12,brown:10,white:8});
 const expected=sharedCast.map(p=>p.who).sort();
 for(const room of ['outside','show','vip']){
  const cast=crowdActors(room,0,true,{x:500,y:600});
  assert.equal(new Set(cast.map(p=>p.who)).size,30);
  assert.deepEqual(cast.map(p=>p.who).sort(),expected);
  assert.ok(cast.every(p=>p.scale>=2));
 }
});
test('Brenno keeps exactly the fans caught, including the branded fans',()=>{
 const events=[{id:0,hit:true},{id:1,hit:true},{id:2,hit:false},{id:4,hit:true}];
 assert.deepEqual(collectedFans(events),['women:0','brand:0','brand:1']);
 assert.ok(Array.from({length:20},(_,i)=>brennoFan(i)).every(who=>sharedCast.some(p=>p.who===who)));
 assert.equal(new Set(Array.from({length:20},(_,i)=>brennoFan(i))).size,20);
});
