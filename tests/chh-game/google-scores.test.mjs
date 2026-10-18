import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
import {createGoogleScores} from '../../test-overrides/chh-show-night/google-scores.mjs';
import {initialState,act} from '../../test-overrides/chh-show-night/state.mjs';

const source=readFileSync(new URL('../../game-backend/apps-script/Code.gs',import.meta.url),'utf8');
const uuid=n=>`session-${String(n).padStart(8,'0')}`;
const token=n=>String(n).padStart(64,'0');
const events=perfect=>Array.from({length:20},(_,id)=>({id,hit:true,perfect}));
const journey={friends:['jay','grace'],entered:true,worship:true,photo:true,room:'show'};
const current=(name='River',id=uuid(1))=>({...act(initialState(),'profile',{name,avatar:'red'}),...journey,sessionId:id});
function backend() {
 const records=new Map(),context=vm.createContext({Utilities:{DigestAlgorithm:{SHA_256:'sha256'},computeDigest:(_,s)=>[...createHash('sha256').update(s).digest()]}});
 vm.runInContext(source,context);
 const store={get:key=>records.has(key)?structuredClone(records.get(key)):null,players:()=>[...records].filter(([key])=>key.startsWith('p_')).map(([,value])=>structuredClone(value)),commit(changes){for(const [key,value] of changes)records.set(key,structuredClone(value));}};
 return {records,call:(path,body,t=token(1),now=1_000_000)=>structuredClone(context.chhHandle_({path,body,token:t,...(path==='/scores'?body:{})},store,now))};
}
test('Google scores register zero-point entrants and never import local game totals',()=>{
 const b=backend();b.call('/session',{sessionId:uuid(1),nickname:'River',journey:{...journey,totals:{eli:999999}}});
 const board=b.call('/scores',{});assert.equal(board.rows.length,1);assert.equal(board.rows[0].eli,0);assert.equal(board.rows[0].total,80);
});
test('All four Google-backed games score equally and retries do not double points',()=>{
 const b=backend();let time=1_000_000;
 for(const [i,game] of ['eli','joz','steven','chamblissnation'].entries()) {
  const id=`round-id-${i}`;b.call('/start',{sessionId:uuid(1),nickname:'River',journey,game,roundId:id},token(1),time);
  const body={sessionId:uuid(1),result:{id,game,events:events(true)}};
  const result=b.call('/finish',body,token(1),time+30_000);assert.equal(result.roundPoints,1000);
  assert.equal(b.call('/finish',body,token(1),time+60_000).duplicate,true);time+=90_000;
 }
 const row=b.call('/scores',{}).rows[0];assert.equal(row.total,4080);assert.equal(row.rounds,4);
 for(const game of ['eli','joz','steven','chamblissnation'])assert.equal(row[game],1000);
});
test('Delayed finish saves, instant finish and foreign session writes are rejected',()=>{
 const b=backend(),id='round-test-1';const body={sessionId:uuid(1),nickname:'River',journey,game:'eli',roundId:id};b.call('/start',body);
 const finish={sessionId:uuid(1),result:{id,game:'eli',events:events(false)}};
 assert.throws(()=>b.call('/finish',finish,token(1),1_000_001),/too quickly/);
 assert.throws(()=>b.call('/session',body,token(2)),/another player/);
 assert.equal(b.call('/finish',finish,token(1),1_000_000+86400_000).roundPoints,800);
});
test('The board retains the best whole session and paginates every one of 1,009 players',()=>{
 const b=backend();for(let n=1;n<=1009;n++)b.call('/session',{sessionId:uuid(n),nickname:`Fan ${n}`,journey:n===1?journey:{}},token(n));
 b.call('/session',{sessionId:uuid(1010),nickname:'Fan 1',journey:{}},token(1));
 const first=b.call('/scores',{offset:0,limit:100});assert.equal(first.totalPlayers,1009);assert.equal(first.rows[0].total,80);
 const last=b.call('/scores',{offset:1000,limit:100});assert.equal(last.rows.length,9);assert.equal(last.nextOffset,null);assert.equal(last.rows.at(-1).rank,1009);
});
test('Invalid hit sets and abandoned rounds cannot add points',()=>{
 const b=backend();b.call('/start',{sessionId:uuid(1),nickname:'River',journey,game:'joz',roundId:'round-old'});
 b.call('/start',{sessionId:uuid(1),nickname:'River',journey,game:'joz',roundId:'round-new'});
 assert.throws(()=>b.call('/finish',{sessionId:uuid(1),result:{id:'round-old',game:'joz',events:events(true)}},token(1),1_100_000),/abandoned/);
 assert.throws(()=>b.call('/finish',{sessionId:uuid(1),result:{id:'round-new',game:'joz',events:events(true).slice(1)}},token(1),1_100_000),/Invalid round/);
});
test('Retrying a start ticket reuses its original server start time',()=>{
 const b=backend(),body={sessionId:uuid(1),nickname:'River',journey,game:'eli',roundId:'retry-round-1'};
 const first=b.call('/start',body,token(1),1_000_000),second=b.call('/start',body,token(1),1_020_000);
 assert.equal(first.id,second.id);
 assert.equal(b.call('/finish',{sessionId:uuid(1),result:{id:first.id,game:'eli',events:events(true)}},token(1),1_026_000).roundPoints,1000);
});
const memory=()=>{const data=new Map();return {getItem:key=>data.get(key),setItem:(key,value)=>data.set(key,value)};};
test('A briefly busy Google service retries without requiring another player tap',async()=>{
 const b=backend();let attempts=0;
 const client=createGoogleScores(memory(),{base:'https://script.google.com/macros/s/test/exec',schedule:(fn,ms)=>{if(ms<2000)queueMicrotask(fn);return 0;},cancel:()=>{},fetcher:async(_,request)=>{
  if(++attempts<3)return {ok:true,json:async()=>({status:503,error:'Scoreboard is busy. Please retry.'})};
  const sent=JSON.parse(request.body);return {ok:true,json:async()=>b.call(sent.path,sent.body,sent.token)};
 }});
 await client.connect(current());assert.equal(attempts,3);assert.equal((await client.board()).totalPlayers,1);client.dispose();
});
test('Google transport uses a simple POST and persists a failed finish across refresh',async()=>{
 const storage=memory(),b=backend();let offline=false,time=1_000_000;const options={base:'https://script.google.com/macros/s/test/exec',schedule:()=>0,cancel:()=>{},fetcher:async(_,request)=>{
  assert.equal(request.headers['Content-Type'],'text/plain;charset=UTF-8');assert.equal(request.headers.Authorization,undefined);
  const sent=JSON.parse(request.body);if(offline&&sent.path==='/finish')throw Error('offline');
  const value=b.call(sent.path,sent.body,sent.token,time);return {ok:true,json:async()=>value};
 }};
 let client=createGoogleScores(storage,options);await client.connect(current());const ticket=await client.start('eli');time+=30_000;offline=true;
 await assert.rejects(client.finish({id:ticket.id,game:'eli',events:events(true)}));assert.equal(client.pendingCount,1);client.dispose();
 offline=false;client=createGoogleScores(storage,options);await client.connect(current());assert.equal(client.pendingCount,0);assert.equal((await client.board()).rows[0].eli,1000);client.dispose();
});
test('Lost successful response retries once without double-counting',async()=>{
 const storage=memory(),b=backend();let time=1_000_000,lose=true;
 const client=createGoogleScores(storage,{base:'https://script.google.com/macros/s/test/exec',schedule:()=>0,cancel:()=>{},fetcher:async(_,request)=>{
  const sent=JSON.parse(request.body),value=b.call(sent.path,sent.body,sent.token,time);
  if(sent.path==='/finish'&&lose){lose=false;throw Error('response lost');}return {ok:true,json:async()=>value};
 }});
 await client.connect(current());const ticket=await client.start('eli');time+=30_000;
 await assert.rejects(client.finish({id:ticket.id,game:'eli',events:events(true)}));await client.retry();
 assert.equal((await client.board()).rows[0].total,1080);assert.equal(client.pendingCount,0);client.dispose();
});
test('A permanently rejected round stays local without trapping later replays',async()=>{
 const storage=memory(),b=backend();let time=1_000_000,reject=true;
 const client=createGoogleScores(storage,{base:'https://script.google.com/macros/s/test/exec',schedule:()=>0,cancel:()=>{},fetcher:async(_,request)=>{
  const sent=JSON.parse(request.body);if(sent.path==='/finish'&&reject){reject=false;return {ok:true,json:async()=>({status:409,error:'Round was abandoned'})};}
  return {ok:true,json:async()=>b.call(sent.path,sent.body,sent.token,time)};
 }});
 await client.connect(current());const ticket=await client.start('eli');time+=30_000;
 await assert.rejects(client.finish({id:ticket.id,game:'eli',events:events(true)}));assert.equal(client.pendingCount,0);assert.equal(client.rejectedCount,1);
 const next=await client.start('joz');time+=30_000;await client.finish({id:next.id,game:'joz',events:events(true)});
 assert.equal((await client.board()).rows[0].joz,1000);client.dispose();
});
