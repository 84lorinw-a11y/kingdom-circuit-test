import test from 'node:test';import assert from 'node:assert/strict';
import {createScoreServer} from '../../game-backend/server.mjs';
test('Shared scores enforce ownership, elapsed time, single use, and best complete session',async t=>{
 let clock=100000;const server=createScoreServer({now:()=>clock,origin:'http://test.local'});await new Promise(r=>server.listen(0,'127.0.0.1',r));t.after(()=>new Promise(r=>server.close(r)));const base=`http://127.0.0.1:${server.address().port}/play-api`;let token;
 async function post(path,data,auth=token){const r=await fetch(base+path,{method:'POST',headers:{'content-type':'application/json',...(auth?{authorization:'Bearer '+auth}:{})},body:JSON.stringify(data)});return {status:r.status,data:await r.json()};}
 const connected=await post('/session',{sessionId:'session-a',nickname:'River'});token=connected.data.token;assert.equal(connected.status,200);
 assert.equal((await post('/start',{sessionId:'session-a',game:'eli'})).status,400);
 for(const [action,value] of [['invite','jay'],['invite','grace'],['enter']])assert.equal((await post('/journey',{sessionId:'session-a',action,value})).status,200);
 const ticket=(await post('/start',{sessionId:'session-a',game:'eli'})).data;const result={game:'eli',id:ticket.id,events:Array.from({length:20},(_,id)=>({id,hit:true,perfect:true}))};
 assert.equal((await post('/finish',{sessionId:'session-a',result})).status,400);clock+=26000;const finish=await post('/finish',{sessionId:'session-a',result});assert.equal(finish.data.total,1030);assert.equal(finish.data.eli,1000);assert.equal((await post('/finish',{sessionId:'session-a',result})).status,409);
 const intruder=(await post('/session',{sessionId:'session-b',nickname:'Other'},'bad')).data.token;assert.equal((await post('/journey',{sessionId:'session-a',action:'photo'},intruder)).status,404);
 await post('/session',{sessionId:'session-c',nickname:'River'});const board=await(await fetch(base+'/scores')).json();assert.equal(board[0].total,1030);assert.equal(board[0].sessionId,'session-a');assert.equal(board[0].joz,0);assert.equal(board[0].token,undefined);
});
