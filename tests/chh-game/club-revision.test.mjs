import test from 'node:test';
import assert from 'node:assert/strict';
import {gameTracks,djTrack} from '../../test-overrides/chh-show-night/music-config.mjs';
import {merchItems} from '../../test-overrides/chh-show-night/merch-items.mjs';
import {roundSchedule} from '../../test-overrides/chh-show-night/scoring.mjs';
import {crewGames} from '../../test-overrides/chh-show-night/crew-games.mjs';
import {snacks,drinks} from '../../test-overrides/chh-show-night/venue-social.mjs';
test('Every non-Eli game has a released Marty preview slot; Eli keeps original audio and timing',()=>{assert.equal(Object.keys(gameTracks).length,10);for(const [id,t] of Object.entries(gameTracks)){if(id==='eli')continue;assert.match(t.artist,/MARTY/);assert.match(t.src,/marty-.+-preview.m4a$/);assert.equal(t.preview,true);assert.match(t.listenUrl,/music.apple.com/);assert.equal(t.loop,true);}assert.equal(djTrack.src,'/play/assets/music/eli-bible-original.m4a');assert.equal(djTrack.bpm,104);assert.equal(roundSchedule('eli')[0].at,2.58);});
test('Only merchandise uses the drop game, with all six items represented',()=>{assert.equal(merchItems.length,6);assert.deepEqual([...new Set(roundSchedule('apollo').map(n=>n.kind))],[0,1,2,3,4,5]);assert.equal(crewGames.brenno.mode,'find');assert.equal(crewGames['gavin-the-hotrod'].mode,'route');assert.ok(Object.values(crewGames).every(g=>!['drive','drop'].includes(g.mode)));assert.deepEqual(drinks,['Water','Lemonade','Soda']);assert.equal(snacks.length,3);});
