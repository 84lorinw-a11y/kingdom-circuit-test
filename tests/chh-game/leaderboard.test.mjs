import test from 'node:test';import assert from 'node:assert/strict';
import {createScoreStore,createOnlineScores,confirmSessionSave} from '../../test-overrides/chh-show-night/leaderboard.mjs';
import {scoreColumns} from '../../test-overrides/chh-show-night/scoreboard-view.mjs';
import {initialState,act} from '../../test-overrides/chh-show-night/state.mjs';
const memory=()=>{const data=new Map();return {getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)};};
const profile=(name,id)=>({...act(initialState(),'profile',{name,avatar:'red'}),sessionId:id});
test('Exit confirmation waits for the shared save and never labels offline points as online',async()=>{
 const state={...profile('River','exit-save'),totals:{eli:1000,joz:800,steven:0,chamblissnation:0}};
 let release;const online={enabled:true,connect:()=>new Promise(resolve=>{release=resolve;})};let finished=false;
 const saving=confirmSessionSave(state,online).then(value=>{finished=true;return value;});await Promise.resolve();assert.equal(finished,false);
 release({state});assert.equal((await saving).status,'online');
 assert.equal((await confirmSessionSave(state,{enabled:true,connect:async()=>({state:{...state,totals:{...state.totals,eli:0}}})})).status,'partial');
 assert.equal((await confirmSessionSave(state,{enabled:true,connect:async()=>{throw Error('offline');}})).status,'waiting');
 assert.equal((await confirmSessionSave(state,{enabled:false},{localSaved:false})).status,'unsaved');
});
test('The scoreboard puts all four games and journey before the final Total column',()=>{assert.deepEqual(scoreColumns.map(c=>c[0]),['rank','nickname','eli','joz','steven','chamblissnation','journey','total']);});
test('Device storage preserves every named player, best whole sessions, and a legacy best score',async()=>{
 const storage=memory(),legacy={nickname:'Earlier Fan',sessionId:'old',total:90,eli:0,joz:90,steven:0,chamblissnation:0,journey:0};storage.setItem('kc-show-night-scores-v2',JSON.stringify({playerId:'device-a',best:legacy}));
 const store=createScoreStore(storage);store.record(profile('River','river-1'));store.record(profile('Sky','sky-1'));store.record({...profile('River','river-2'),totals:{eli:100,joz:200,steven:0,chamblissnation:0}});store.record({...profile('River','river-3'),totals:{eli:200,joz:0,steven:0,chamblissnation:0}});
 const board=await createScoreStore(storage).board();assert.equal(board.mode,'device');assert.equal(board.rows.length,3);assert.deepEqual(board.rows.map(r=>r.nickname),['River','Earlier Fan','Sky']);assert.equal(board.rows[0].total,300);assert.equal(board.rows[0].eli,100);assert.equal(board.rows[0].joz,200);assert.equal(board.rows[2].total,0);assert.equal(board.nextOffset,null);
});
test('Shared player tokens stay separate when different people use the same phone',async()=>{
 const storage=memory(),calls=[];const fetcher=async(url,options)=>{const body=JSON.parse(options.body);calls.push({body,token:options.headers.Authorization});return {ok:true,json:async()=>({token:body.nickname==='River'?'river-token':'sky-token',state:profile(body.nickname,body.sessionId)})};};
 const online=createOnlineScores(storage,{base:'https://scores.test/play-api',fetcher});await online.connect(profile('River','a'));await online.connect(profile('Sky','b'));await online.connect(profile('River','c'));assert.equal(calls[0].token,undefined);assert.equal(calls[1].token,undefined);assert.equal(calls[2].token,'Bearer river-token');
});
test('Connecting a saved visitor restores journey access without importing old round points',async()=>{
 const calls=[];let state=profile('River','a');const fetcher=async(url,options)=>{const body=JSON.parse(options.body);calls.push({url,body});if(url.endsWith('/session'))return {ok:true,json:async()=>({token:'token',state})};state=act(state,body.action,body.value);return {ok:true,json:async()=>({})};};
 let saved=profile('River','a');for(const [action,value] of [['invite','jay'],['invite','grace'],['enter']])saved=act(saved,action,value);saved.totals.eli=5000;
 await createOnlineScores(memory(),{base:'https://scores.test/play-api',fetcher}).connect(saved);assert.equal(state.room,'show');assert.equal(state.totals.eli,0);assert.equal(calls.some(c=>c.url.endsWith('/finish')),false);
});
test('Scoreboard requests pages and retries after a connection failure',async()=>{
 let fail=true;const urls=[];const fetcher=async(url)=>{urls.push(url);if(fail){fail=false;throw Error('offline');}return {ok:true,json:async()=>({rows:[],totalPlayers:0,nextOffset:null})};};
 const online=createOnlineScores(memory(),{base:'https://scores.test/play-api',fetcher});await assert.rejects(online.connect(profile('River','a')));const board=await online.board(100);assert.equal(board.totalPlayers,0);assert.equal(urls.at(-1),'https://scores.test/play-api/scores?offset=100&limit=50');
});
