import test from 'node:test';import assert from 'node:assert/strict';
import {beatLayout,beatY,beatLane,judgeBeat,streakLabel} from '../../test-overrides/chh-show-night/eli-board.mjs';
import {roundSchedule,roundScore} from '../../test-overrides/chh-show-night/scoring.mjs';

test('Responsive beat boards put every note on the hit line at its actual audio time',()=>{
 for(const height of [360,430,560,780]){const l=beatLayout(height);assert.ok(l.hitY>l.laneTop+140);assert.ok(l.hitY+28<l.height);assert.equal(beatY(l,4,4),l.hitY);assert.ok(Math.abs(beatY(l,4,4-l.lead)-l.laneTop)<.001);assert.ok(l.noteWidth>70);}
});
test('Direct taps and physical pads use the same four lanes at phone and desktop widths',()=>{
 for(const width of [320,390,430,520])for(let lane=0;lane<4;lane++)assert.equal(beatLane(12+(lane+.5)*width/4,12,width),lane);
 assert.equal(beatLane(-20,0,390),0);assert.equal(beatLane(420,0,390),3);
});
test('Live-audio judgment preserves timing windows, lane accuracy and one hit per note',()=>{
 const note={id:0,at:4,lane:2},notes=[note];
 assert.equal(judgeBeat(notes,2,4).perfect,true);assert.equal(judgeBeat(notes,2,4.2).perfect,false);
 assert.equal(judgeBeat(notes,2,4.4),null);assert.equal(judgeBeat(notes,1,4),null);assert.equal(judgeBeat(notes,8,4),null);
 note.done=true;assert.equal(judgeBeat(notes,2,4),null);
});
test('The upgraded Eli board still awards exactly the same twenty 40 + 10 opportunities',()=>{
 const notes=roundSchedule('eli',23),events=notes.map(n=>{const hit=judgeBeat(notes,n.lane,n.at);return {id:hit.note.id,hit:true,perfect:hit.perfect};});
 assert.equal(events.length,20);assert.equal(roundScore(events).total,1000);assert.equal(roundScore(events).bestCombo,20);
 assert.equal(streakLabel(5),'LOCKED IN');assert.equal(streakLabel(10),'ON FIRE');assert.equal(streakLabel(15),'ALL FOR THE KING');
});
