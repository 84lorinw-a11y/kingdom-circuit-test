import test from 'node:test';
import assert from 'node:assert/strict';
import {stageSpotAt} from '../../test-overrides/chh-show-night/worship.mjs';
import {practiceSpot} from '../../test-overrides/chh-show-night/practice-booth.mjs';
import {crowdActors,crowdCounts} from '../../test-overrides/chh-show-night/crowds.mjs';

test('Each artist triggers only in front of their own stage position; Eli remains separate',()=>{
 assert.equal(stageSpotAt({room:'show',x:335,y:475}),'steven');
 assert.equal(stageSpotAt({room:'show',x:720,y:475}),'joz');
 assert.equal(stageSpotAt({room:'show',...practiceSpot}),null);
 assert.equal(stageSpotAt({room:'show',x:335,y:540}),null);
 assert.equal(stageSpotAt({room:'vip',x:335,y:475}),null);
});
test('Every scene has two extra fans and no reused crowd sprite',()=>{
 assert.deepEqual(crowdCounts,{outside:30,show:34,vip:26});
 const ids=[];
 for(const room of ['outside','show','vip']){
  const cast=crowdActors(room,0,true,{x:500,y:600});
  assert.equal(new Set(cast.map(p=>p.who)).size,cast.length);
  assert.ok(cast.every(p=>p.scale>=2));
  ids.push(...cast.map(p=>p.who));
 }
 assert.equal(new Set(ids).size,ids.length);
});
