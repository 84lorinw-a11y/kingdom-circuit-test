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
 await post('/session',{sessionId:'session-c',nickname:'River'});const {rows:board}=await(await fetch(base+'/scores')).json();assert.equal(board[0].total,1030);assert.equal(board[0].sessionId,'session-a');assert.equal(board[0].marty,0);assert.equal(board[0].token,undefined);
});

test('Every player is listed, including zero-score players and those beyond the first hundred',async t=>{
 const server=createScoreServer({origin:'http://test.local',allowedOrigins:['https://84lorinw-a11y.github.io']});await new Promise(r=>server.listen(0,'127.0.0.1',r));t.after(()=>new Promise(r=>server.close(r)));const base=`http://127.0.0.1:${server.address().port}/play-api`;
 for(let i=0;i<105;i++){const r=await fetch(base+'/session',{method:'POST',headers:{'content-type':'application/json',origin:'https://84lorinw-a11y.github.io'},body:JSON.stringify({sessionId:'fan-'+i,nickname:'Fan '+i})});assert.equal(r.status,200);}
 const rows=[];let offset=0;do{const r=await fetch(base+`/scores?offset=${offset}&limit=50`);const page=await r.json();assert.equal(page.totalPlayers,105);rows.push(...page.rows);offset=page.nextOffset;}while(offset!==null);
 assert.equal(rows.length,105);assert.equal(new Set(rows.map(r=>r.sessionId)).size,105);assert.equal(rows.at(-1).rank,105);assert.ok(rows.every(r=>r.total===0));assert.ok(rows.every(r=>r.token===undefined));
 const preflight=await fetch(base+'/session',{method:'OPTIONS',headers:{origin:'https://84lorinw-a11y.github.io','access-control-request-method':'POST'}});assert.equal(preflight.status,204);assert.equal(preflight.headers.get('access-control-allow-origin'),'https://84lorinw-a11y.github.io');
 assert.equal((await fetch(base+'/scores',{headers:{origin:'https://other.test'}})).status,403);assert.equal((await fetch(base+'/scores?offset=-1')).status,400);
});
test('The all-player board survives restarting the score service',async t=>{
 const {mkdtemp,rm}=await import('node:fs/promises');const {tmpdir}=await import('node:os');const {join}=await import('node:path');
 const dir=await mkdtemp(join(tmpdir(),'chh-board-'));t.after(()=>rm(dir,{recursive:true,force:true}));const database=join(dir,'scores.sqlite');
 let server=createScoreServer({database});await new Promise(r=>server.listen(0,'127.0.0.1',r));let base=`http://127.0.0.1:${server.address().port}/play-api`;
 const created=await(await fetch(base+'/session',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({sessionId:'keep-me',nickname:'Persistent Fan'})})).json();
 await fetch(base+'/journey',{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer '+created.token},body:JSON.stringify({sessionId:'keep-me',action:'invite',value:'jay'})});await new Promise(r=>server.close(r));
 server=createScoreServer({database});await new Promise(r=>server.listen(0,'127.0.0.1',r));t.after(()=>new Promise(r=>server.close(r)));base=`http://127.0.0.1:${server.address().port}/play-api`;
 const board=await(await fetch(base+'/scores')).json();assert.equal(board.totalPlayers,1);assert.equal(board.rows[0].nickname,'Persistent Fan');assert.equal(board.rows[0].total,15);assert.equal(board.rows[0].journey,15);
});
