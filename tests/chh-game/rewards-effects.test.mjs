import test from 'node:test';
import assert from 'node:assert/strict';
import {initialState,act,score,pointsToGo,objective} from '../../test-overrides/chh-show-night/state.mjs';
import {createBassDetector} from '../../test-overrides/chh-show-night/bass-fx.mjs';
import {pitPhotographers} from '../../test-overrides/chh-show-night/pit.mjs';
import {stageSpots} from '../../test-overrides/chh-show-night/worship.mjs';
import {practiceSpot} from '../../test-overrides/chh-show-night/practice-booth.mjs';

test('An 80 XP night explains both remaining rewards and reaches 125 exactly once',()=>{
 let s=initialState();
 for(const [action,value] of [['invite','jay'],['invite','grace'],['enter'],['worship'],['vip'],['photo'],['show']])s=act(s,action,value);
 assert.equal(score(s),80);assert.match(pointsToGo(s),/45 XP TO FIREWORKS/);
 assert.match(objective(s),/take your bag/);s=act(s,'merch','cream');
 assert.equal(score(s),100);assert.match(pointsToGo(s),/25 XP TO FIREWORKS/);assert.match(objective(s),/Eli/);s=act(s,'beat',5);assert.equal(score(s),125);assert.match(pointsToGo(s),/FIREWORKS UNLOCKED/);
 assert.equal(score(act(s,'merch','mint')),125);assert.equal(score(act(s,'beat',10)),125);
});

test('Bass detection rejects silence, sustained tones, and rapid duplicate hits',()=>{
 const detector=createBassDetector();
 for(let t=0;t<500;t+=16)assert.equal(detector.sample(.002,t),false);
 assert.equal(detector.sample(.2,500),true);
 assert.equal(detector.sample(.3,550),false);
 for(let t=600;t<1400;t+=16)assert.equal(detector.sample(.2,t),false);
 for(let t=1400;t<1800;t+=16)detector.sample(.003,t);
 assert.equal(detector.sample(.2,1800),true);
 detector.reset();assert.equal(detector.sample(.002,0),false);
});

test('Both distinct pit photographers stay above the listening rings',()=>{
 assert.equal(new Set(pitPhotographers.map(p=>p.who)).size,2);
 for(const p of pitPhotographers)for(const spot of [...stageSpots,practiceSpot]){
  assert.ok(p.y+7<spot.y-18,'feet and shadow clear the top of the ring');
 }
});
