import test from 'node:test';import assert from 'node:assert/strict';
import {prepareRoundStart} from '../../test-overrides/chh-show-night/rounds.mjs';
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};};
test('Round audio and score reservation start together and both complete before gameplay',async()=>{
 const music=deferred(),ticket=deferred(),calls=[];let done=false;
 const pending=prepareRoundStart({unlock:async()=>calls.push('unlock'),preload:()=>{calls.push('music');return music.promise;}},{start:()=>{calls.push('score');return ticket.promise;}},'marty').then(value=>{done=true;return value;});
 await Promise.resolve();assert.deepEqual(calls,['unlock','music','score']);music.resolve();await Promise.resolve();assert.equal(done,false);ticket.resolve({id:'ticket'});assert.deepEqual(await pending,{id:'ticket'});
});
test('Score outage permits device play while music failure remains retryable',async()=>{
 assert.equal(await prepareRoundStart({unlock:async()=>{},preload:async()=>{}},{start:async()=>{throw Error('offline');}},'eli'),null);
 await assert.rejects(prepareRoundStart({unlock:async()=>{},preload:async()=>{throw Error('music failed');}},{start:async()=>({id:'ticket'})},'eli'),/music failed/);
});
