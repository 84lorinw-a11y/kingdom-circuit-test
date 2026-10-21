import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {loadArcadeArt,gameArtwork} from '../../test-overrides/chh-show-night/arcade-art.mjs';
import {artistGames,createArtistRound} from '../../test-overrides/chh-show-night/artist-arcade.mjs';
import {roundSchedule} from '../../test-overrides/chh-show-night/scoring.mjs';
import {drawBeatBoard} from '../../test-overrides/chh-show-night/eli-board.mjs';
import {drawMerchScene} from '../../test-overrides/chh-show-night/arcade-scenes.mjs';
import {merchDrop} from '../../test-overrides/chh-show-night/merch-motion.mjs';

test('opening one game fetches only its setting; shared settings and replays reuse it',async()=>{
 const art={},calls=[],load=async url=>{calls.push(url);return {width:640,height:853};};
 assert.equal(calls.length,0);await loadArcadeArt('eli',art,{load});assert.equal(calls.length,1);
 assert.ok(calls[0].endsWith('arcade-eli-v1.webp'));
 await Promise.all([loadArcadeArt('dearis',art,{load}),loadArcadeArt('andrew-prim',art,{load}),loadArcadeArt('apollo',art,{load})]);
 assert.equal(calls.length,2);await loadArcadeArt('eli',art,{load});assert.equal(calls.length,2);
 await Promise.all([loadArcadeArt('lj-the-messenger',art,{load}),loadArcadeArt('tonyxtrotter',art,{load})]);assert.equal(calls.length,3);
});
test('artwork failures retry, and opening an unrelated game never triggers these downloads',async()=>{
 const art={};let calls=0;const load=async()=>{if(++calls===1)throw Error('offline');return {width:1,height:1};};
 await loadArcadeArt('marty',art,{load});assert.equal(calls,0);
 await assert.rejects(loadArcadeArt('brenno',art,{load}),/offline/);await loadArcadeArt('brenno',art,{load});assert.equal(calls,2);
});
function context(){
 const calls=[],gradient={addColorStop(){}};
 const g=new Proxy({},{get:(o,k)=>o[k]??((...args)=>{for(const a of args)if(typeof a==='number')assert.ok(Number.isFinite(a),`${k} must not receive NaN or Infinity`);calls.push(k);return gradient;}),set:(o,k,v)=>(o[k]=v,true)});
 return {g,calls};
}
const art=Object.fromEntries([...new Set(Object.values(gameArtwork))].map(k=>['arcade_'+k,{width:640,height:853}]));
art.eliBanner={width:600,height:272};
test('all artist scenes draw actual backgrounds and survive an entire round in both motion modes',()=>{
 for(const game of Object.keys(gameArtwork).filter(id=>artistGames[id]))for(const reduced of [false,true]){
  const {g,calls}=context(),r=createArtistRound(game,{notes:roundSchedule(game,89)});
  for(let t=0;t<=artistGames[game].seconds;t+=.25){r.step(t,.05);r.draw(g,{art,reduced});}
  assert.ok(calls.includes('drawImage'),game+' must render its selected setting');
 }
});
test('Eli renders all responsive heights with stable lane geometry and reduced motion',()=>{
 for(const height of [360,430,560,780])for(const reduced of [false,true]){
  const {g}=context();for(const time of [0,1,2.58,12,26])drawBeatBoard(g,{height,art,time,phase:'playing',notes:roundSchedule('eli'),reduced,combo:8,flashes:[time+.1,0,0,0]});
 }
});
test('merch scene keeps all existing clothing assets and the real catch-line drop motion',()=>{
 const {g,calls}=context(),merchArt={...art,merch:{width:900,height:300},merchEli:{width:900,height:300}},notes=roundSchedule('apollo');
 for(const reduced of [false,true])for(const time of [0,1,2.3,12,25])drawMerchScene(g,{art:merchArt,time,px:210,notes,reduced,dropFor:merchDrop});
 assert.ok(calls.includes('drawImage'));assert.equal(merchDrop(notes[0],notes[0].at).y,475);
});
test('all existing audio, video, characters and branding remain byte-identical',()=>{
 const baseline=JSON.parse(readFileSync(new URL('./fixtures/arcade-media-baseline.json',import.meta.url)));
 for(const [file,value] of Object.entries(baseline.files).filter(([f])=>f.startsWith('assets/'))){
  const hash=createHash('sha256').update(readFileSync(new URL('../../test-overrides/chh-show-night/'+file,import.meta.url))).digest('hex');assert.equal(hash,value.sha256,file);
 }
});
