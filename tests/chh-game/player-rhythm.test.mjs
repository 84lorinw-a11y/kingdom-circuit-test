import test from 'node:test';import assert from 'node:assert/strict';import {act,initialState,restore,score} from '../../test-overrides/chh-show-night/state.mjs';import {beatNotes,judgeTap} from '../../test-overrides/chh-show-night/rhythm.mjs';import {avatars,playerName} from '../../test-overrides/chh-show-night/avatars.mjs';import {crowdCounts,crowdActors} from '../../test-overrides/chh-show-night/crowds.mjs';
test('Player identity persists, validates choices, and stays separate from friends',()=>{for(const a of avatars){let s=act(initialState(),'profile',{name:'  River  ',avatar:a.id});assert.equal(s.name,'River');assert.equal(s.profileReady,true);assert.equal(restore(JSON.stringify(s)).avatar,a.id);assert.deepEqual(s.friends,[]);}assert.equal(act(initialState(),'profile',{name:' ',avatar:'red'}).profileReady,false);assert.equal(act(initialState(),'profile',{name:'River',avatar:'unknown'}).profileReady,false);assert.equal(playerName('a'.repeat(60)).length,18);});
test('Timing judges real hits, rejects early/late taps, and cannot double-count notes',()=>{const notes=beatNotes();assert.equal(judgeTap(notes,0),null);assert.equal(judgeTap(notes,notes[0].at).perfect,true);assert.equal(judgeTap(notes,notes[0].at),null);assert.equal(judgeTap(notes,notes[1].at+150).perfect,false);assert.equal(judgeTap(notes,notes[2].at+211),null);assert.equal(notes.filter(n=>n.status==='hit').length,2);});
test('Eli completion awards its own 25 XP once, independently of worship and beat best',()=>{
 let s=initialState();for(const [a,v] of [['invite','jay'],['invite','grace'],['enter']])s=act(s,a,v);
 s=act(s,'beat',8);assert.equal(s.eli,true);assert.equal(s.worship,false);assert.equal(score(s),55);
 s=act(s,'beat',3);assert.equal(s.beatBest,8);assert.equal(score(s),55);
 s=restore(JSON.stringify(s));assert.equal(s.eli,true);assert.equal(s.beatBest,8);assert.equal(score(s),55);
 assert.equal(act(s,'beat',11).beatBest,8);s=act(s,'worship');assert.equal(score(s),80);
});
test('A completed round earns XP even with zero hits; invalid or off-stage results do not',()=>{
 const initial=initialState();assert.equal(act(initial,'beat',10).eli,false);
 let s=initial;for(const [a,v] of [['invite','jay'],['invite','grace'],['enter']])s=act(s,a,v);
 for(const invalid of [-1,11,1.5,NaN,'10'])assert.equal(act(s,'beat',invalid).eli,false);
 s=act(s,'beat',0);assert.equal(score(s),55);assert.equal(restore(JSON.stringify(s)).eli,true);
});
test('Older completed rounds migrate, while a fresh night does not reuse an old personal best',()=>{
 let s=initialState();for(const [a,v] of [['invite','jay'],['invite','grace'],['enter'],['beat',7]])s=act(s,a,v);
 delete s.eli;s=restore(JSON.stringify(s));assert.equal(s.eli,true);assert.equal(score(s),55);
 const fresh={...initialState(),beatBest:s.beatBest};
 assert.equal(restore(JSON.stringify(fresh)).eli,false);assert.equal(score(restore(JSON.stringify(fresh))),0);
 const enteredAgain=act(act(act(fresh,'invite','jay'),'invite','grace'),'enter');
 assert.equal(restore(JSON.stringify(enteredAgain)).eli,false);assert.equal(score(enteredAgain),30);
});
test('Every room has a substantial crowd',()=>{assert.deepEqual(crowdCounts,{outside:30,show:34,vip:26});});

test('Imported recording uses its measured beat grid instead of the old click-track lead-in',()=>{
 const notes=beatNotes(104,2580);assert.equal(notes.length,10);assert.equal(notes[0].at,2580);
 assert.ok(notes[9].at>7700&&notes[9].at<7850);
 for(const note of notes)assert.equal(judgeTap(notes,note.at).perfect,true);
 assert.equal(notes.filter(n=>n.status==='hit').length,10);
});


test('Crowd bodies stay close to player size and the white boy and girl are selectable',()=>{
 for(const room of ['outside','show','vip']){
  const actors=crowdActors(room,0,true,{x:500,y:600});assert.ok(actors.every(a=>a.scale>=2.05&&a.scale<=2.4));
  assert.ok(actors.some(a=>a.who===`crowd-${room}:4`));assert.ok(actors.some(a=>a.who===`crowd-${room}:6`));
 }
 assert.ok(avatars.some(a=>a.sprite===4));assert.ok(avatars.some(a=>a.sprite==='blonde-fan'));
});


test('Hands-up zone is on the main-stage floor, separate from the center DJ booth',async()=>{
 const {inFrontRow}=await import('../../test-overrides/chh-show-night/worship.mjs');
 assert.equal(inFrontRow({room:'show',x:335,y:475}),true);
 assert.equal(inFrontRow({room:'show',x:512,y:475}),false);
 assert.equal(inFrontRow({room:'vip',x:510,y:475}),false);
});
