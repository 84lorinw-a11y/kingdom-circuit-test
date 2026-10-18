// Optional same-origin score service. Node 24+, no npm dependencies.
// Keep this server and its SQLite database out of the static Pages artifact.
import http from 'node:http';
import {DatabaseSync} from 'node:sqlite';
import {randomUUID,randomBytes,createHash} from 'node:crypto';
import {readFile,mkdir} from 'node:fs/promises';
import {realpathSync} from 'node:fs';
import {resolve,extname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {initialState,act,score,journeyScore} from '../test-overrides/chh-show-night/state.mjs';
import {gameIds,roundSeconds,validateRound,roundScore} from '../test-overrides/chh-show-night/scoring.mjs';
const hash=s=>createHash('sha256').update(s).digest('hex');
export function createScoreServer({database=':memory:',source=resolve('test-overrides/chh-show-night'),origin='http://127.0.0.1:4329',allowedOrigins=[origin],now=()=>Date.now()}={}){
 const db=new DatabaseSync(database);db.exec(`PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS players(id TEXT PRIMARY KEY, token TEXT UNIQUE NOT NULL); CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, player TEXT NOT NULL, state TEXT NOT NULL); CREATE TABLE IF NOT EXISTS rounds(id TEXT PRIMARY KEY, session TEXT NOT NULL, game TEXT NOT NULL, started INTEGER NOT NULL, done INTEGER DEFAULT 0); CREATE TABLE IF NOT EXISTS best(player TEXT PRIMARY KEY, total INTEGER NOT NULL, row TEXT NOT NULL);`);
 const json=(res,status,data)=>{res.writeHead(status,{'content-type':'application/json','cache-control':'no-store','x-content-type-options':'nosniff'});res.end(JSON.stringify(data));};
 function row(state){return {nickname:state.name,sessionId:state.sessionId,...state.totals,journey:journeyScore(state),total:score(state),rounds:state.rounds};}
 function save(id,player,state){db.prepare('UPDATE sessions SET state=? WHERE id=?').run(JSON.stringify(state),id);const r=row(state);db.prepare('INSERT INTO best VALUES(?,?,?) ON CONFLICT(player) DO UPDATE SET total=excluded.total,row=excluded.row WHERE excluded.total > best.total').run(player,r.total,JSON.stringify(r));return r;}
 const server=http.createServer(async(req,res)=>{try{
  const url=new URL(req.url,origin);
  if(url.pathname.startsWith('/play-api/')){
   const requestOrigin=req.headers.origin;
   if(requestOrigin&&!allowedOrigins.includes(requestOrigin))return json(res,403,{error:'Origin not allowed'});
   if(requestOrigin){res.setHeader('Access-Control-Allow-Origin',requestOrigin);res.setHeader('Vary','Origin');}
   if(req.method==='OPTIONS'){res.setHeader('Access-Control-Allow-Methods','GET, POST, OPTIONS');res.setHeader('Access-Control-Allow-Headers','Content-Type, Authorization');res.setHeader('Access-Control-Max-Age','600');res.writeHead(204);return res.end();}
   if(req.method==='GET'&&url.pathname==='/play-api/scores'){
    const offset=Number(url.searchParams.get('offset')||0),limit=Number(url.searchParams.get('limit')||50);
    if(!Number.isSafeInteger(offset)||offset<0||!Number.isSafeInteger(limit)||limit<1||limit>100)return json(res,400,{error:'Invalid page'});
    const totalPlayers=db.prepare('SELECT COUNT(*) AS count FROM best').get().count;
    const rows=db.prepare('SELECT row FROM best ORDER BY total DESC, player ASC LIMIT ? OFFSET ?').all(limit,offset).map((r,i)=>({...JSON.parse(r.row),rank:offset+i+1}));
    return json(res,200,{mode:'online',rows,totalPlayers,nextOffset:offset+rows.length<totalPlayers?offset+rows.length:null});
   }
   if(req.method!=='POST')return json(res,405,{error:'Use POST'});
   if(!req.headers['content-type']?.startsWith('application/json'))return json(res,415,{error:'JSON required'});
   let text='';for await(const chunk of req){text+=chunk;if(text.length>16000)return json(res,413,{error:'Request too large'});}let data;try{data=JSON.parse(text);}catch{return json(res,400,{error:'Invalid JSON'});}
   let token=req.headers.authorization?.replace(/^Bearer /,''),player=token?db.prepare('SELECT id FROM players WHERE token=?').get(hash(token))?.id:null;
   if(url.pathname==='/play-api/session'){
    if(!player){token=randomBytes(32).toString('hex');player=randomUUID();db.prepare('INSERT INTO players VALUES(?,?)').run(player,hash(token));}
    if(typeof data.sessionId!=='string'||data.sessionId.length>100)return json(res,400,{error:'Session required'});
    const existing=db.prepare('SELECT player,state FROM sessions WHERE id=?').get(data.sessionId);
    if(existing&&existing.player!==player)return json(res,403,{error:'Session belongs to another player'});
    let state=existing?JSON.parse(existing.state):{...initialState(),sessionId:data.sessionId};state=act(state,'profile',{name:data.nickname,avatar:'red'});
    if(!state.profileReady)return json(res,400,{error:'Nickname required'});
    if(!existing)db.prepare('INSERT INTO sessions VALUES(?,?,?)').run(state.sessionId,player,JSON.stringify(state));save(state.sessionId,player,state);
    return json(res,200,{token,state});
   }
   if(!player)return json(res,401,{error:'Start a session first'});
   const session=db.prepare('SELECT * FROM sessions WHERE id=? AND player=?').get(data.sessionId,player);
   if(!session)return json(res,404,{error:'Session missing'});let state=JSON.parse(session.state);
   if(url.pathname==='/play-api/journey'){
    // Journey awards are one-time and ordered by the server state machine.
    if(!['invite','enter','worship','vip','photo','show','outside'].includes(data.action))return json(res,400,{error:'Unknown journey action'});
    state=act(state,data.action,data.value);return json(res,200,save(session.id,player,state));
   }
   if(url.pathname==='/play-api/start'){
    if(!gameIds.includes(data.game)||state.room!=='show')return json(res,400,{error:'Enter the show before playing'});
    // Abandoned attempts are invalidated; one live round per session.
    db.prepare('UPDATE rounds SET done=1 WHERE session=? AND done=0').run(session.id);
    const id=randomUUID();db.prepare('INSERT INTO rounds(id,session,game,started) VALUES(?,?,?,?)').run(id,session.id,data.game,now());return json(res,200,{id});
   }
   if(url.pathname==='/play-api/finish'){
    const result=data.result;if(!validateRound(result))return json(res,400,{error:'Invalid round'});
    const round=db.prepare('SELECT * FROM rounds WHERE id=? AND session=?').get(result.id,session.id);
    if(!round||round.done||round.game!==result.game)return json(res,409,{error:'Round already saved or not started'});
    if(now()-round.started<roundSeconds[round.game]*1000-350||now()-round.started>120000)return json(res,400,{error:'Round duration invalid'});
    db.exec('BEGIN IMMEDIATE');try{db.prepare('UPDATE rounds SET done=1 WHERE id=?').run(result.id);state=act(state,'round',result);const saved=save(session.id,player,state);db.exec('COMMIT');return json(res,200,{...saved,roundPoints:roundScore(result.events).total});}catch(e){db.exec('ROLLBACK');throw e;}
   }
   return json(res,404,{error:'Unknown endpoint'});
  }
  if(req.method!=='GET')return json(res,405,{error:'Use GET'});
  let pathname=decodeURIComponent(url.pathname);if(pathname==='/')pathname='/play/';if(!pathname.startsWith('/play/'))return json(res,404,{error:'Not found'});
  const rel=pathname.slice(6)||'index.html',file=resolve(source,rel);if(!file.startsWith(resolve(source)+'/'))return json(res,403,{error:'Not allowed'});
  let body=await readFile(file);const ext=extname(file);if(ext==='.html')body=Buffer.from(body.toString().replace('<head>','<head><meta name="score-service" content="/play-api">'));
  res.writeHead(200,{'content-type':({'.html':'text/html','.mjs':'text/javascript','.css':'text/css','.png':'image/png','.webp':'image/webp','.m4a':'audio/mp4'})[ext]||'application/octet-stream','cache-control':'no-cache','x-robots-tag':'noindex,nofollow'});res.end(body);
 }catch(error){json(res,error.code==='ENOENT'?404:500,{error:error.code==='ENOENT'?'Not found':'Request could not be completed'});}});
 server.on('close',()=>db.close());return server;
}
if(process.argv[1]&&import.meta.url===pathToFileURL(realpathSync(process.argv[1])).href){
 const port=Number(process.env.PORT||4329),host=process.env.HOST||'127.0.0.1',origin=process.env.PUBLIC_ORIGIN||`http://${host}:${port}`;
 const allowedOrigins=(process.env.ALLOWED_ORIGINS||origin).split(',').map(s=>s.trim()).filter(Boolean);
 const directory=process.env.SCORE_DATA_DIR||resolve('game-backend/data');await mkdir(directory,{recursive:true});const server=createScoreServer({database:resolve(directory,'scores.sqlite'),origin,allowedOrigins});server.listen(port,host,()=>console.log(`CHH test + score service: ${origin}/play/`));
}
