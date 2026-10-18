import test from 'node:test';import assert from 'node:assert/strict';import {findPath,walkable} from '../../test-overrides/chh-show-night/navigation.mjs';
test('All room destinations remain reachable, including refreshments to the VIP exit',()=>{
 const rooms={outside:[{x:470,y:575},{x:210,y:590},{x:348,y:578},{x:740,y:385},{x:975,y:625}],show:[{x:500,y:575},{x:105,y:455},{x:335,y:475},{x:512,y:475},{x:720,y:475},{x:940,y:447},{x:75,y:625},{x:900,y:585}],vip:[{x:500,y:570},{x:505,y:442},{x:105,y:310},{x:875,y:410},{x:200,y:635}]};
 for(const [room,points]of Object.entries(rooms))for(const start of points)for(const end of points){const route=findPath(room,start,end);assert.ok(route.length,`${room}: ${JSON.stringify(start)} → ${JSON.stringify(end)}`);let prev=start;for(const next of route){const steps=Math.max(1,Math.ceil(Math.hypot(prev.x-next.x,prev.y-next.y)));for(let i=0;i<=steps;i++){const t=i/steps;assert.ok(walkable(room,prev.x+(next.x-prev.x)*t,prev.y+(next.y-prev.y)*t),`${room} route left the room`);}prev=next;}assert.deepEqual(route.at(-1),end);}
});

test('Grass, plants and lounge furniture never block a direct walk',()=>{
 const formerlyBlocked={outside:[{x:180,y:430},{x:510,y:465},{x:960,y:390}],show:[{x:220,y:410},{x:850,y:410}],vip:[{x:180,y:480},{x:830,y:340}]};
 for(const [room,points] of Object.entries(formerlyBlocked))for(const point of points){assert.equal(walkable(room,point.x,point.y),true);assert.deepEqual(findPath(room,{x:500,y:570},point),[point]);}
});
test('The break spot has a direct route back out, even from old blocked coordinates',()=>{
 for(const start of [{x:875,y:410},{x:180,y:480},{x:850,y:350}])assert.deepEqual(findPath('vip',start,{x:105,y:310}),[{x:105,y:310}]);
});
test('Taps at screen edges are clamped safely instead of rejected',()=>{
 assert.deepEqual(findPath('outside',{x:500,y:570},{x:-100,y:0}),[{x:32,y:170}]);
 assert.deepEqual(findPath('vip',{x:500,y:570},{x:1100,y:700}),[{x:992,y:644}]);
 assert.equal(walkable('show',NaN,500),false);
});
