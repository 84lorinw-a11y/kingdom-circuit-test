import test from 'node:test';import assert from 'node:assert/strict';
import {screenFrame,screenSlides} from '../../test-overrides/chh-show-night/stage-screen.mjs';
import {drawApolloMarquee} from '../../test-overrides/chh-show-night/apollo-crew.mjs';
test('Stage screen holds each visual and crossfades slowly through all three',()=>{
 assert.deepEqual(screenSlides,['cover','not-for-sale','apollo-logo']);
 assert.deepEqual(screenFrame(8000),{current:0,next:1,mix:0});
 assert.deepEqual(screenFrame(9200),{current:0,next:1,mix:.5});
 assert.deepEqual(screenFrame(10000),{current:1,next:2,mix:0});
 assert.deepEqual(screenFrame(20000),{current:2,next:0,mix:0});
 assert.deepEqual(screenFrame(30000),{current:0,next:1,mix:0});
 for(const time of [0,9200,19200,29200])assert.deepEqual(screenFrame(time,true),{current:0,next:0,mix:0});
});
test('Every exterior artist uses the same font and common fitting transform',()=>{
 const lines=[],scales=[];
 const ctx={save(){},restore(){},translate(){},scale(x,y){scales.push([x,y]);},measureText(t){return{width:t.length*12};},fillText(text,x,y,maxWidth){lines.push({text,font:this.font,maxWidth});}};
 drawApolloMarquee(ctx);
 const artistLines=lines.slice(1);
 assert.equal(artistLines.length,3);
 assert.equal(new Set(artistLines.map(line=>line.font)).size,1);
 assert.ok(artistLines.every(line=>line.maxWidth===undefined),'No row can independently squeeze the artist names');
 assert.equal(scales.length,1);
 assert.ok(scales[0][0]<=1&&scales[0][1]===1);
});
