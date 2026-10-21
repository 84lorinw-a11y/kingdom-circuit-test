import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createArtistRound,waveY} from '../../test-overrides/chh-show-night/artist-arcade.mjs';
import {roundSchedule,roundScore} from '../../test-overrides/chh-show-night/scoring.mjs';
import {ryanHazards,ryanHazardX,touchesRyanHazard} from '../../test-overrides/chh-show-night/ryan-hazards.mjs';

function play(seed=1,dodge=false,step=1/60){
 const notes=roundSchedule('ryan-ellis',seed),events=[],mistakes=[];
 const r=createArtistRound('ryan-ellis',{notes,seed,onResolve:(n,hit,perfect)=>events.push({id:n.id,hit,perfect}),onMistake:m=>mistakes.push(m)});
 const hazards=r.snapshot().ryanHazards;
 for(let t=step;t<40+step/2;t+=step){
  const h=dodge?hazards.find(h=>t>=h.at-.6&&t<=h.at+.4):null;
  r.point('move',{x:100,y:h?h.y+(h.y>295?-100:100):waveY(t)});r.step(t,step);
 }
 return {r,events,mistakes};
}
test('Ryan gets nine visible hazards between notes after two warm-up notes',()=>{
 for(let seed=0;seed<100;seed++){
  const notes=roundSchedule('ryan-ellis',seed),hazards=ryanHazards(notes,seed,waveY);
  assert.equal(hazards.length,9);assert.ok(hazards[0].at>notes[1].at);
  for(const h of hazards){assert.ok(Math.min(...notes.map(n=>Math.abs(n.at-h.at)))>.9);assert.ok(h.y>=145&&h.y<=445);assert.equal(ryanHazardX(h,h.at),100);}
  assert.deepEqual(hazards,ryanHazards(notes,seed,waveY));
 }
 assert.notDeepEqual(ryanHazards(roundSchedule('ryan-ellis'),1,waveY),ryanHazards(roundSchedule('ryan-ellis'),2,waveY));
});
test('a clear dodge route can collect all twenty notes at both 30 and 60 fps',()=>{
 for(const step of [1/30,1/60])for(const seed of [1,17,89,999,0xffffffff]){
  const {r,events,mistakes}=play(seed,true,step);
  assert.equal(roundScore(events).total,1000,`seed ${seed}, step ${step}`);
  assert.equal(mistakes.length,0);assert.equal(r.meta().dodged,9);assert.equal(r.meta().bumps,0);
 }
});
test('touching a speaker breaks the streak, costs only the next clean bonus and never ends the round',()=>{
 const {r,events,mistakes}=play(17,false);
 assert.equal(events.length,20);assert.equal(roundScore(events).hits,20);
 assert.equal(mistakes.length,9);assert.equal(r.meta().bumps,9);
 assert.equal(roundScore(events).total,910);assert.equal(events[2].perfect,false);assert.equal(events[3].perfect,true);
 const before=mistakes.length;r.step(40,.05);r.step(40,.05);assert.equal(mistakes.length,before);
});
test('swept collision catches a crossed frame but allows passing safely above or below',()=>{
 const h={at:5,y:300};
 assert.ok(touchesRyanHazard(h,4.7,5.3,300,300));
 assert.ok(touchesRyanHazard(h,4.9,5.1,200,400));
 assert.equal(touchesRyanHazard(h,4.7,5.3,180,220),false);
 assert.equal(touchesRyanHazard(h,4.7,5.3,390,420),false);
 assert.equal(touchesRyanHazard(h,3,4,300,300),false);
 assert.equal(touchesRyanHazard(h,6,7,300,300),false);
});
test('restarting Ryan creates fresh hazards and an empty penalty state',()=>{
 const first=play().r;assert.equal(first.meta().bumps,9);
 const second=createArtistRound('ryan-ellis',{notes:roundSchedule('ryan-ellis'),seed:1});
 assert.equal(second.meta().bumps,0);assert.equal(second.snapshot().ryanStatic,false);
 assert.ok(second.snapshot().ryanHazards.every(h=>!h.done&&!h.hit));
});
test('the challenge adds no media downloads and keeps every asset byte-identical',()=>{
 const baseline=JSON.parse(readFileSync(new URL('./fixtures/ryan-media-baseline.json',import.meta.url)));
 for(const [f,v] of Object.entries(baseline.files).filter(([f])=>f.startsWith('assets/'))){
  assert.equal(createHash('sha256').update(readFileSync(new URL('../../test-overrides/chh-show-night/'+f,import.meta.url))).digest('hex'),v.sha256,f);
 }
});
