import test from 'node:test';import assert from 'node:assert/strict';
import {screenPlacement,stageScreen,drawStageScreen} from '../../test-overrides/chh-show-night/stage-screen.mjs';
import {drawApolloMarquee} from '../../test-overrides/chh-show-night/apollo-crew.mjs';
test('Stage video follows the world camera just above the rear stage floor',()=>{
 assert.ok(stageScreen.y+stageScreen.height>=300&&stageScreen.y+stageScreen.height<=313);
 assert.deepEqual(screenPlacement({width:1024,height:683}),{left:283,top:110,width:454,height:200});
 const phone=screenPlacement({width:375,height:683,camera:300,viewWidth:375});
 assert.deepEqual(phone,{left:-17,top:110,width:454,height:200});
 const half=screenPlacement({width:512,height:341.5});
 assert.deepEqual(half,{left:141.5,top:55,width:227,height:100});
});
test('Film and still poster fill the same screen without letterboxing or distorting the picture',()=>{
 const pictures=[],text=[];
 const ctx={save(){},restore(){},fillRect(){},strokeRect(){},fillText(...args){text.push(args);},drawImage(...args){pictures.push(args);}};
 for(const frame of [{videoWidth:960,videoHeight:540},{naturalWidth:960,naturalHeight:540}]){
  drawStageScreen(ctx,frame);
  const [,sx,sy,sw,sh,x,y,w,h]=pictures.at(-1);
  assert.equal(sw/sh,w/h);assert.ok(sx>=0&&sy>=0&&sx+sw<=960&&sy+sh<=540);
  assert.deepEqual([x,y,w,h],[283,110,454,200]);
 }
 assert.equal(text.length,0,'The film has no text overlay; the supplied logo banner is drawn separately.');
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
