import test from 'node:test';
import assert from 'node:assert/strict';
import {gameTracks,djTrack} from '../../test-overrides/chh-show-night/music-config.mjs';
import {merchItems,drawMerchItem} from '../../test-overrides/chh-show-night/merch-items.mjs';
import {roundSchedule} from '../../test-overrides/chh-show-night/scoring.mjs';
import {crewGames} from '../../test-overrides/chh-show-night/crew-games.mjs';
import {snacks,drinks} from '../../test-overrides/chh-show-night/venue-social.mjs';
test('Every non-Eli game has a released Marty preview slot; Eli keeps original audio and timing',()=>{assert.equal(Object.keys(gameTracks).length,10);for(const [id,t] of Object.entries(gameTracks)){if(id==='eli')continue;assert.match(t.artist,/MARTY/);assert.match(t.src,/marty-.+-preview.m4a$/);assert.equal(t.preview,true);assert.match(t.listenUrl,/music.apple.com/);assert.equal(t.loop,true);}assert.equal(djTrack.src,'/play/assets/music/eli-bible-original.m4a');assert.equal(djTrack.bpm,104);assert.equal(roundSchedule('eli')[0].at,2.58);});
test('Only merchandise uses the drop game, with all eight items represented',()=>{assert.equal(merchItems.length,8);assert.deepEqual([...new Set(roundSchedule('apollo').map(n=>n.kind))],[0,1,2,3,4,5,6,7]);assert.equal(crewGames.brenno.mode,'find');assert.equal(crewGames['gavin-the-hotrod'].mode,'route');assert.ok(Object.values(crewGames).every(g=>!['drive','drop'].includes(g.mode)));assert.deepEqual(drinks,['Water','Lemonade','Soda']);assert.equal(snacks.length,3);});
test('Every drop and catalog entry uses its own shirt, hoodie or cap cell',()=>{
 const images={merch:{width:900,height:300},merchExtras:{width:600,height:200},merchEli:{width:1086,height:362}},calls=[];
 const g={drawImage(...args){calls.push(args);}};
 for(let i=0;i<8;i++)drawMerchItem(g,images,i,0,0,240,210);
 assert.deepEqual(calls.map(([image,x])=>[Object.keys(images).find(k=>images[k]===image),x]),[['merch',0],['merch',300],['merch',600],['merchExtras',0],['merchExtras',200],['merchEli',0],['merchEli',362],['merchEli',724]]);
 for(const [,, ,sw,sh,,,dw,dh]of calls)assert.equal(dw/dh,sw/sh);
 drawMerchItem(g,images,8,0,0,240,210);assert.equal(calls.length,8);
});
