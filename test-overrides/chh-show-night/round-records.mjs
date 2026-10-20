import {gameIds,roundScore,validateRound} from './scoring.mjs?v=apollo-06';
// Only add an artist benchmark after the artist has actually played this version.
export const artistBenchmarks=Object.freeze({});
export function createRoundRecords(storage){
 const key='kc-apollo-arcade-bests-v1';let rows=[];
 try{const value=JSON.parse(storage.getItem(key));if(Array.isArray(value))rows=value.filter(r=>gameIds.includes(r.game)&&typeof r.name==='string'&&r.name.length<=24&&Number.isInteger(r.total)&&r.total>=0&&r.total<=1000);}catch{}
 return {
  record(name,result){if(!name||!validateRound(result))return null;const value={game:result.game,name:name.slice(0,24),...roundScore(result.events)};
   const old=rows.find(r=>r.game===value.game&&r.name.toLocaleLowerCase()===value.name.toLocaleLowerCase());
   if(!old||old.total<value.total){rows=rows.filter(r=>r!==old);rows.push(value);try{storage.setItem(key,JSON.stringify(rows));}catch{}}
   return value;
  },
  board(game){return rows.filter(r=>r.game===game).sort((a,b)=>b.total-a.total||a.name.localeCompare(b.name)).map((r,i)=>({...r,rank:i+1}));},
  best(game,name){return this.board(game).find(r=>r.name.toLocaleLowerCase()===name.toLocaleLowerCase())?.total??null;}
 };
}
export function drawScoreCard(canvas,{name,game,title,result,drawPortrait}){
 canvas.width=1080;canvas.height=1350;const g=canvas.getContext('2d');
 g.fillStyle='#181719';g.fillRect(0,0,1080,1350);g.fillStyle='#a23e37';g.fillRect(55,55,970,12);
 const line=(s,y,size,color='#ede4d6')=>{g.fillStyle=color;g.font=`800 ${size}px system-ui,sans-serif`;g.textAlign='center';g.fillText(s,540,y,950);};
 line('APOLLO RECORDS',150,43);line('NOT 4 SALE',205,22,'#c9a882');
 drawPortrait?.(g,540,690,game==='eli'?'eli-williams':game,6.8);
 line(title,770,39);line(`${result.total.toLocaleString()} POINTS`,885,76,'#e7bd82');line(name,970,42);
 line(`${result.hits}/20 · BEST STREAK ${result.bestCombo}`,1035,26,'#c2b4a4');
 line(game==='marty'?'STILL INDEPENDENT':'SEE YOU AT THE SHOW',1170,36);
 line('KINGDOM CIRCUIT · APOLLO NIGHT',1260,22,'#a79b8c');
}
// Shared results controls for the preserved Eli and merch rounds.
export function mountRoundResultTools(host,{game,title,name,records,drawPortrait}){
 const wrap=document.createElement('div');wrap.className='round-result-actions';wrap.hidden=true;
 const board=document.createElement('button'),save=document.createElement('button'),detail=document.createElement('div');board.textContent='GAME LEADERBOARD';save.textContent='SHARE SCORE';detail.className='round-local-board';detail.hidden=true;wrap.append(board,save);host.append(wrap,detail);let result=null,url=null,disposed=false;
 const clear=()=>{if(url){URL.revokeObjectURL(url);url=null;}detail.replaceChildren();detail.hidden=true;};
 board.onclick=()=>{clear();detail.hidden=false;const heading=document.createElement('strong');heading.textContent='BEST ROUNDS · ON THIS DEVICE';const list=document.createElement('ol');for(const row of records.board(game)){const item=document.createElement('li');item.textContent=`${row.name} · ${row.total} pts`;list.append(item);}detail.append(heading,list);};
 save.onclick=()=>{if(!result)return;const card=document.createElement('canvas');drawScoreCard(card,{name,game,title,result,drawPortrait});card.toBlob(blob=>{if(disposed||!blob)return;clear();url=URL.createObjectURL(blob);const img=document.createElement('img'),link=document.createElement('a');img.className='score-card-preview';img.src=url;img.alt=`${name}: ${result.total} points`;link.className='score-card-save';link.href=url;link.download=`apollo-${game}-score.png`;link.textContent='SAVE SCORE CARD';detail.hidden=false;detail.append(img,link);},'image/png');};
 return {show(data){result=roundScore(data.events);records.record(name,data);clear();wrap.hidden=false;},hide(){wrap.hidden=true;clear();},dispose(){disposed=true;clear();}};
}
