/** CHH Show Night — shared TEST scores. No emails or raw player tokens are stored. */
const CHH = Object.freeze({
  spreadsheet: '1YhSyRhnLUFliM8x-ngY1WH8OCvIfxJBGZmt701mWLb4',
  board: 'CHH Show Up', data: '_CHH Score Data',
  games: ['eli', 'joz', 'steven', 'chamblissnation'],
  seconds: {eli:26, joz:21, steven:21, chamblissnation:25},
  headers: ['Rank','Player','Eli','Joz','Steven','Chamblissnation','Journey','Rounds','Last played','Total','Player ID'],
  dataHeaders: ['Record ID','Type','Player ID','Data','Updated'],
  journal: 'CHH_PENDING_COMMIT_V1'
});

// Run once in the editor before deploying as a web app, executing as the owner.
function setupCHHScores() {
  const book = SpreadsheetApp.openById(CHH.spreadsheet);
  const board = book.getSheetByName(CHH.board) || book.insertSheet(CHH.board);
  const data = book.getSheetByName(CHH.data) || book.insertSheet(CHH.data);
  for (const pair of [[board,CHH.headers],[data,CHH.dataHeaders]]) {
    const sheet=pair[0], headers=pair[1];
    if (sheet.getLastRow() && JSON.stringify(sheet.getRange(1,1,1,headers.length).getValues()[0]) !== JSON.stringify(headers)) {
      throw Error('Existing content in '+sheet.getName()+' was preserved. Choose a separate score tab.');
    }
    sheet.getRange(1,1,1,headers.length).setValues([headers]).setBackground('#122435').setFontColor('#ffca72').setFontWeight('bold');
    sheet.setFrozenRows(1); sheet.setRowHeight(1,36);
  }
  board.setColumnWidth(1,65); board.setColumnWidth(2,180);
  board.setColumnWidths(3,3,90); board.setColumnWidth(6,150);
  board.setColumnWidths(7,2,90); board.setColumnWidth(9,175); board.setColumnWidth(10,110);
  board.getRange(2,3,Math.max(1,board.getMaxRows()-1),6).setNumberFormat('#,##0');
  board.getRange(2,10,Math.max(1,board.getMaxRows()-1),1).setNumberFormat('#,##0');
  board.getRange(2,9,Math.max(1,board.getMaxRows()-1),1).setNumberFormat('mm/dd/yy h:mm am/pm');
  board.hideColumns(11); data.hideSheet();
  PropertiesService.getScriptProperties().setProperty('CHH_READY','1');
  SpreadsheetApp.flush();
  return 'CHH Show Up is ready. Other tabs were not changed.';
}

function doGet(e) {
  return chhRespond_({path:'/scores',offset:e && e.parameter && e.parameter.offset,limit:e && e.parameter && e.parameter.limit});
}
function doPost(e) {
  try {
    const text=e && e.postData && e.postData.contents;
    if (!text || text.length>16000) throw Error('Invalid request');
    return chhRespond_(JSON.parse(text));
  } catch (_) { return chhJson_({error:'Invalid request',status:400}); }
}
function chhJson_(value) { return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON); }
function chhRespond_(request) {
  const lock=LockService.getScriptLock();
  try {
    if (!PropertiesService.getScriptProperties().getProperty('CHH_READY')) return chhJson_({error:'Scoreboard setup is not finished',status:503});
    if (!lock.tryLock(2500)) return chhJson_({error:'Scoreboard is busy. Please retry.',status:503});
    const store=chhStore_(); store.recover();
    return chhJson_(chhHandle_(request,store,Date.now()));
  } catch (error) {
    return chhJson_({error:error.chhStatus?error.message:'Scoreboard is temporarily unavailable. Please retry.',status:error.chhStatus||503});
  } finally { if(lock.hasLock()) lock.releaseLock(); }
}
function chhFail_(status,message) { const error=Error(message);error.chhStatus=status;throw error; }
function chhHash_(value) { return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,value).map(n=>((n+256)%256).toString(16).padStart(2,'0')).join(''); }
function chhId_(value) { return typeof value==='string' && /^[a-zA-Z0-9_-]{8,100}$/.test(value); }
function chhName_(value) { return String(value||'').normalize('NFKC').replace(/[\u0000-\u001f\u007f<>]/g,'').trim().slice(0,24); }
function chhState_(id,name) { return {sessionId:id,name,profileReady:true,avatar:'red',room:'outside',friends:[],visited:[],entered:false,worship:false,photo:false,totals:{eli:0,joz:0,steven:0,chamblissnation:0},roundIds:[],rounds:0}; }
function chhJourney_(state,source) {
  if (!source || typeof source!=='object') return;
  const friends=Array.isArray(source.friends)?source.friends:[];
  for(const friend of ['jay','grace']) if(friends.includes(friend)&&!state.friends.includes(friend)) state.friends.push(friend);
  if(source.entered && state.friends.length===2) state.entered=true;
  if(state.entered) { state.worship=state.worship||source.worship===true;state.photo=state.photo||source.photo===true; }
  state.room=state.entered&&['show','vip'].includes(source.room)?source.room:'outside';
}
function chhRow_(state,now) {
  const journey=state.friends.length*15+(state.worship?25:0)+(state.photo?25:0);
  const total=CHH.games.reduce((sum,id)=>sum+state.totals[id],journey);
  if(!Number.isSafeInteger(total)) chhFail_(400,'Score exceeds supported numeric precision');
  return Object.assign({nickname:state.name,sessionId:state.sessionId,journey,total,rounds:state.rounds,updated:now},state.totals);
}
function chhValidateRound_(result) {
  return result && CHH.games.includes(result.game) && chhId_(result.id) && Array.isArray(result.events) && result.events.length===20 &&
    new Set(result.events.map(event=>event.id)).size===20 && result.events.every(event=>Number.isInteger(event.id)&&event.id>=0&&event.id<20&&typeof event.hit==='boolean'&&typeof event.perfect==='boolean'&&(!event.perfect||event.hit));
}
function chhHandle_(request,store,now) {
  const path=String(request.path||'').split('?')[0];
  if(path==='/scores') {
    const offset=Number(request.offset||0),limit=Number(request.limit||50);
    if(!Number.isSafeInteger(offset)||offset<0||!Number.isSafeInteger(limit)||limit<1||limit>100) chhFail_(400,'Invalid page');
    const all=store.players().map(player=>({playerId:player.id,...player.best})).sort((a,b)=>b.total-a.total||a.playerId.localeCompare(b.playerId));
    return {mode:'online',rows:all.slice(offset,offset+limit).map((row,i)=>({...row,rank:offset+i+1})),totalPlayers:all.length,nextOffset:offset+limit<all.length?offset+limit:null};
  }
  if(!['/session','/start','/finish'].includes(path)) chhFail_(404,'Unknown operation');
  const body=request.body||{}, token=request.token;
  if(typeof token!=='string'||!/^[a-f0-9]{64}$/.test(token)) chhFail_(401,'Start a session first');
  const playerId=chhHash_(token), playerKey='p_'+playerId;
  let player=store.get(playerKey);
  if(!chhId_(body.sessionId)) chhFail_(400,'Session required');
  let session=store.get('s_'+body.sessionId);
  if(session && session.player!==playerId) chhFail_(403,'Session belongs to another player');
  if(path==='/finish' && (!player||!session)) chhFail_(404,'Session missing');
  const nickname=chhName_(body.nickname);
  if(path!=='/finish') {
    if(!nickname) chhFail_(400,'Nickname required');
    if(!player) player={id:playerId,created:now,best:null};
    if(!session) session={player:playerId,state:chhState_(body.sessionId,nickname),active:null};
    session.state.name=nickname; chhJourney_(session.state,body.journey);
  }
  const changes=[]; let response;
  if(path==='/start') {
    if(!CHH.games.includes(body.game)||session.state.room!=='show') chhFail_(400,'Enter the show before playing');
    if(!chhId_(body.roundId)) chhFail_(400,'Round ID required');
    const key='r_'+body.roundId, existing=store.get(key);
    if(existing) {
      if(existing.session!==body.sessionId||existing.player!==playerId||existing.game!==body.game||existing.done) chhFail_(409,'Round is not available');
      return {id:body.roundId,token,state:session.state};
    }
    if(session.active) {const prior=store.get('r_'+session.active);if(prior&&!prior.done) changes.push(['r_'+session.active,{...prior,abandoned:true}]);}
    changes.push([key,{player:playerId,session:body.sessionId,game:body.game,started:now,done:false}]);
    session.active=body.roundId; response={id:body.roundId,token,state:session.state};
  } else if(path==='/finish') {
    const result=body.result;if(!chhValidateRound_(result)) chhFail_(400,'Invalid round');
    const key='r_'+result.id, round=store.get(key);
    if(!round||round.player!==playerId||round.session!==body.sessionId||round.game!==result.game) chhFail_(409,'Round was not started');
    if(round.done) return {...round.receipt,duplicate:true};
    if(round.abandoned||session.active!==result.id) chhFail_(409,'Round was abandoned');
    if(now-round.started<CHH.seconds[result.game]*1000-350) chhFail_(400,'Round finished too quickly');
    const points=result.events.reduce((sum,event)=>sum+(event.hit?40+(event.perfect?10:0):0),0);
    session.state.totals[result.game]+=points;session.state.rounds++;session.active=null;
    response={...chhRow_(session.state,now),roundPoints:points};
    changes.push([key,{...round,done:true,finished:now,receipt:response}]);
  } else response={token,state:session.state};
  const candidate=chhRow_(session.state,now);
  if(!player.best||candidate.total>player.best.total||(candidate.sessionId===player.best.sessionId&&candidate.total===player.best.total)) player.best=candidate;
  changes.push(['s_'+body.sessionId,session],[playerKey,player]);
  store.commit(changes,player);
  return response;
}

function chhStore_() {
  const book=SpreadsheetApp.openById(CHH.spreadsheet),data=book.getSheetByName(CHH.data),board=book.getSheetByName(CHH.board),properties=PropertiesService.getScriptProperties();
  if(!data||!board) throw Error('Missing score tabs');
  function find(id) { if(data.getLastRow()<2)return null;return data.getRange(2,1,data.getLastRow()-1,1).createTextFinder(id).matchEntireCell(true).useRegularExpression(false).findNext(); }
  function get(id) { const cell=find(id);return cell?JSON.parse(data.getRange(cell.getRow(),4).getValue()):null; }
  function put(id,value) {
    const cell=find(id),row=cell?cell.getRow():data.getLastRow()+1;
    if(row>data.getMaxRows())data.insertRowsAfter(data.getMaxRows(),500);
    data.getRange(row,1,1,5).setValues([[id,id[0],value.player||value.id,JSON.stringify(value),new Date()]]);
  }
  function show(player) {
    const existing=board.getLastRow()>1?board.getRange(2,11,board.getLastRow()-1,1).createTextFinder(player.id).matchEntireCell(true).useRegularExpression(false).findNext():null;
    const row=existing?existing.getRow():Math.max(2,board.getLastRow()+1),best=player.best;
    if(row>board.getMaxRows())board.insertRowsAfter(board.getMaxRows(),500);
    const name=/^[=+\-@]/.test(best.nickname)?"'"+best.nickname:best.nickname;
    board.getRange(row,1,1,11).setValues([['',name,best.eli,best.joz,best.steven,best.chamblissnation,best.journey,best.rounds,new Date(best.updated),best.total,player.id]]);
    board.getRange(row,1).setFormula('=RANK(J'+row+',$J$2:$J,0)');
    board.getRange(row,3,1,6).setNumberFormat('#,##0');board.getRange(row,9).setNumberFormat('mm/dd/yy h:mm am/pm');board.getRange(row,10).setNumberFormat('#,##0');
  }
  function apply(transaction) { for(const change of transaction.changes)put(change[0],change[1]);show(transaction.player);SpreadsheetApp.flush();properties.deleteProperty(CHH.journal); }
  return {
    get,
    // Read one row per player, rather than scanning every historical round.
    players(){return board.getLastRow()<2?[]:board.getRange(2,1,board.getLastRow()-1,11).getValues().filter(row=>row[10]).map(row=>({id:row[10],best:{nickname:String(row[1]),eli:Number(row[2]),joz:Number(row[3]),steven:Number(row[4]),chamblissnation:Number(row[5]),journey:Number(row[6]),rounds:Number(row[7]),updated:row[8] instanceof Date?row[8].getTime():row[8],total:Number(row[9])}}));},
    recover(){const pending=properties.getProperty(CHH.journal);if(pending)apply(JSON.parse(pending));},
    commit(changes,player){const transaction={changes,player};properties.setProperty(CHH.journal,JSON.stringify(transaction));apply(transaction);}
  };
}
