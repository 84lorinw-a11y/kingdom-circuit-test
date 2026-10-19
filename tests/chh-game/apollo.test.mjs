import test from 'node:test';
import assert from 'node:assert/strict';
import {apolloCrew,frontCrew,boothLayout,drawApolloStage} from '../../test-overrides/chh-show-night/apollo-crew.mjs';
import {stageSpots} from '../../test-overrides/chh-show-night/worship.mjs';
import {practiceSpot} from '../../test-overrides/chh-show-night/practice-booth.mjs';
import {createScoreStore,createOnlineScores} from '../../test-overrides/chh-show-night/leaderboard.mjs';
import {initialState,act} from '../../test-overrides/chh-show-night/state.mjs';

test('Nine approved artists fit onstage with their own reachable game markers',()=>{
 assert.equal(apolloCrew.length,9);
 assert.equal(new Set(apolloCrew.map(p=>p.id)).size,9);
 assert.equal(new Set(apolloCrew.map(p=>p.stageX)).size,9);
 const drawn=[];drawApolloStage({},0,true,(ctx,x,y,id,options)=>drawn.push({x,y,id,...options}));
 assert.equal(drawn.length,8);
 assert.deepEqual(drawn.map(p=>p.id),frontCrew.map(p=>p.id));
 assert.ok(drawn.every(p=>p.id!=='eli-williams'&&p.y>boothLayout.y+8));
 for(const spot of stageSpots)assert.equal(spot.x,apolloCrew.find(p=>p.id===spot.id).stageX);
 assert.equal(practiceSpot.x,boothLayout.x);
 assert.ok(boothLayout.width<222&&boothLayout.y<363);
});

test('Apollo cannot read or overwrite the original competition or call it during play',async()=>{
 const original=JSON.stringify({best:{nickname:'Original player',total:99999},players:{}});
 const data=new Map([['kc-show-night-scores-v2',original],['kc-show-night-v1','production save']]);
 const storage={getItem:key=>data.get(key),setItem:(key,value)=>data.set(key,value)};
 const store=createScoreStore(storage);
 assert.equal((await store.board()).rows.length,0);
 const state=act(initialState(),'profile',{name:'Apollo test',avatar:'red'});
 store.record(state);
 assert.equal((await store.board()).rows.length,1);
 assert.equal(data.get('kc-show-night-scores-v2'),original);
 assert.equal(data.get('kc-show-night-v1'),'production save');
 let requests=0;
 const online=createOnlineScores(storage,{base:'',fetcher:()=>{requests++;throw Error('Unexpected network call');}});
 await online.connect(state);online.journey('invite','jay');await online.start('marty');await online.finish({});
 assert.equal(requests,0);
 assert.throws(()=>createOnlineScores(storage,{base:'https://script.google.com/macros/s/original/exec'}),/cannot use the original competition/);
});
