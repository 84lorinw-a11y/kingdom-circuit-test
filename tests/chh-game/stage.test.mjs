import test from 'node:test';
import assert from 'node:assert/strict';
import {stageSpotAt} from '../../test-overrides/chh-show-night/worship.mjs';
import {practiceSpot} from '../../test-overrides/chh-show-night/practice-booth.mjs';
import {crowdActors,crowdCounts,sharedCast,stevenFan,collectedFans} from '../../test-overrides/chh-show-night/crowds.mjs';

test('Each artist triggers only in front of their own stage position; Eli remains separate',()=>{
 assert.equal(stageSpotAt({room:'show',x:335,y:475}),'steven');
 assert.equal(stageSpotAt({room:'show',x:720,y:475}),'joz');
 assert.equal(stageSpotAt({room:'show',...practiceSpot}),null);
 assert.equal(stageSpotAt({room:'show',x:335,y:540}),null);
 assert.equal(stageSpotAt({room:'vip',x:335,y:475}),null);
});
test('The same balanced cast attends all three rooms, without duplicate people',()=>{
 assert.deepEqual(crowdCounts,{outside:30,show:30,vip:30});
 assert.deepEqual(sharedCast.reduce((n,p)=>(n[p.appearance]=(n[p.appearance]||0)+1,n),{}),{white:10,Black:10,brown:10});
 const expected=sharedCast.map(p=>p.who).sort();
 for(const room of ['outside','show','vip']){
  const cast=crowdActors(room,0,true,{x:500,y:600});
  assert.equal(new Set(cast.map(p=>p.who)).size,30);
  assert.deepEqual(cast.map(p=>p.who).sort(),expected);
  assert.ok(cast.every(p=>p.scale>=2));
 }
});
test('Steven keeps exactly the fans caught, including the branded fans',()=>{
 const events=[{id:0,hit:true},{id:1,hit:true},{id:2,hit:false},{id:4,hit:true}];
 assert.deepEqual(collectedFans(events),['fan:0','brand:0','brand:1']);
 assert.ok(Array.from({length:20},(_,i)=>stevenFan(i)).every(who=>sharedCast.some(p=>p.who===who)));
 assert.equal(new Set(Array.from({length:20},(_,i)=>stevenFan(i))).size,20);
});
