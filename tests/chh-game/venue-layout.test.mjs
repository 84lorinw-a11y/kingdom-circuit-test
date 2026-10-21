import test from 'node:test';import assert from 'node:assert/strict';
import {andrewSpot,vipSpot,vipReturn,merchSpot,roomMusicEnabled} from '../../test-overrides/chh-show-night/venue-layout.mjs';
import {roomStops,stopNames} from '../../test-overrides/chh-show-night/journey-guide.mjs';
import {crowdActors} from '../../test-overrides/chh-show-night/crowds.mjs';
import {findPath} from '../../test-overrides/chh-show-night/navigation.mjs';
import {initialState,act} from '../../test-overrides/chh-show-night/state.mjs';
test('Andrew on the booth rug and VIP below its right edge are distinct reachable destinations',()=>{
 assert.ok(andrewSpot.x>850&&andrewSpot.y>=444);assert.ok(vipSpot.x>970&&vipSpot.y>560);assert.ok(Math.hypot(andrewSpot.x-vipSpot.x,andrewSpot.y-vipSpot.y)>100);
 for(const h of [andrewSpot,vipSpot])assert.deepEqual(findPath('show',{x:500,y:570},h).at(-1),{x:h.x,y:h.y});
 const state={...initialState(),entered:true,room:'vip',vipUnlocked:true};const back=act(state,'show');assert.deepEqual({x:back.x,y:back.y},vipReturn);
});
test('Retired merch and mic stops stay out of the floor guide; VIP marker remains compact',()=>{
 const destination=findPath('show',{x:500,y:570},merchSpot).at(-1);
 assert.equal(destination.y,625);assert.ok(!roomStops.show.includes('merch'));assert.equal(vipSpot.radius,18);assert.ok(Math.hypot(destination.x-merchSpot.x,destination.y-merchSpot.y)<83);
 assert.ok(!roomStops.show.includes('cypher'));assert.equal(stopNames.cypher,undefined);
});
test('Outside has eight standing queue members, two seated campers and talking groups',()=>{
 const cast=crowdActors('outside',0,true,{x:400,y:600});const queue=cast.filter(a=>a.role==='queue'),campers=cast.filter(a=>a.role==='camper');
 assert.equal(queue.length,8);assert.deepEqual(queue.map(a=>a.queueOrder),[1,2,3,4,5,6,7,8]);assert.equal(campers.length,2);assert.ok(campers.every(a=>Number.isInteger(a.campPose)&&a.y<queue[0].y));
 assert.equal(cast.filter(a=>a.role==='conversation').length,20);assert.equal(new Set(cast.map(a=>a.who)).size,30);
 assert.ok(cast.every(a=>Math.hypot(a.x-695,a.y-445)>65),'Entrance circle stays open');
 const later=crowdActors('outside',900,false,{x:400,y:600}).filter(a=>a.role==='camper');assert.deepEqual(later.map(a=>a.y),campers.map(a=>a.y),'Chairs stay planted');
});
test('Ambient playback is allowed only during active main-room exploration',()=>{
 const ready={room:'show',profileReady:true,entryPending:false,dialogOpen:false,hidden:false,soundOn:true};assert.equal(roomMusicEnabled(ready),true);
 for(const override of [{room:'outside'},{room:'vip'},{profileReady:false},{entryPending:true},{dialogOpen:true},{hidden:true},{soundOn:false}])assert.equal(roomMusicEnabled({...ready,...override}),false);
});
