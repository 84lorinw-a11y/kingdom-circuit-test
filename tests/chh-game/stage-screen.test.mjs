import test from 'node:test';import assert from 'node:assert/strict';
import {screenPlacement,stageScreen} from '../../test-overrides/chh-show-night/stage-screen.mjs';
import {drawApolloMarquee} from '../../test-overrides/chh-show-night/apollo-crew.mjs';
test('Stage video follows the world camera and stays above the artists',()=>{
 assert.ok(stageScreen.y+stageScreen.height<=225);
 assert.deepEqual(screenPlacement({width:1024,height:683}),{left:323,top:25,width:454,height:200});
 const phone=screenPlacement({width:375,height:683,camera:300,viewWidth:375});
 assert.deepEqual(phone,{left:23,top:25,width:454,height:200});
 const half=screenPlacement({width:512,height:341.5});
 assert.deepEqual(half,{left:161.5,top:12.5,width:227,height:100});
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
