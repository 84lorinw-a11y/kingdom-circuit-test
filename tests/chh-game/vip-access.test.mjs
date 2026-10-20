import test from 'node:test';
import assert from 'node:assert/strict';
import {matchesVipCode} from '../../test-overrides/chh-show-night/vip-access.mjs';
import {initialState,act,restore,score} from '../../test-overrides/chh-show-night/state.mjs';
const show=()=>act(act(act(initialState(),'invite','jay'),'invite','grace'),'enter');
test('VIP requires the game code and a wrong code preserves progress',()=>{let s=show();const before=score(s);assert.equal(act(s,'vip').room,'show');assert.equal(act(s,'unlockVip','wrong').vipUnlocked,false);s=act(s,'unlockVip',' not-4-sale ');assert.equal(s.vipUnlocked,true);assert.equal(act(s,'vip').room,'vip');assert.equal(score(s),before);assert.equal(matchesVipCode(null),false);assert.equal(matchesVipCode('NOT4SALE123'),false);assert.equal(act(initialState(),'unlockVip','NOT4SALE').vipUnlocked,false);});
test('Saved VIP admission continues; old saves return to the show without losing points',()=>{let s=act(act(show(),'unlockVip','NOT4SALE'),'vip');assert.equal(restore(JSON.stringify(s)).room,'vip');assert.equal(restore(JSON.stringify(s)).vipUnlocked,true);delete s.vipUnlocked;const old=restore(JSON.stringify(s));assert.equal(old.room,'show');assert.equal(old.vipUnlocked,false);assert.equal(score(old),score(s));assert.equal(initialState().vipUnlocked,false);});
