import {brennoFan} from './crowds.mjs?v=apollo-24';
import {drawPerson} from './sprites.mjs?v=apollo-24';

export const crewGames={
 brenno:{title:'FIND YOUR PEOPLE',instruction:'Find the fan in Brenno’s invite. Tap their numbered portrait below. Twenty fans to bring into the crew.',mode:'find',labels:['1','2','3','4','5','6'],result:'fans found'},
 'gavin-the-hotrod':{title:'HOTROD ROUTE',instruction:'Read each route clue and choose the right turn to reach the show. Keys 1–3 work too.',mode:'route',labels:['← LEFT','STRAIGHT ↑','RIGHT →'],result:'turns navigated'},
 'ryan-ellis':{title:'FIND THE HARMONY',instruction:'Slide your note into the gold target before the countdown ends. Drag or use ← →.',mode:'slider',result:'notes matched'},
 'lj-the-messenger':{title:'DELIVER THE MESSAGE',instruction:'Read the envelope. Tap its destination before time runs out. Keys 1–3 work too.',mode:'choice',labels:['CREW','STUDIO','STAGE'],result:'messages delivered'},
 dearis:{title:'FIND YOUR LIGHT',instruction:'Follow De’aris with the spotlight. Keep him centered when the countdown ends. Drag or use ← →.',mode:'spotlight',result:'shots lit'},
 tonyxtrotter:{title:'VERSE BUILDER',instruction:'Build each four-word line in the shown order. Tap the next word. Keys 1–4 work too.',mode:'words',labels:['','','',''],result:'words placed'},
 'andrew-prim':{title:'BUILD THE BEAT',instruction:'Watch four pads light up, then repeat that order. Five patterns, four sounds each. Keys 1–4 work too.',mode:'memory',labels:['KICK','SNARE','HATS','BASS'],result:'sounds arranged'}
};
export const phrases=[['KEEP','THE','CREW','TOGETHER'],['MAKE','ROOM','FOR','EVERYONE'],['LET','YOUR','LIGHT','SHINE'],['BUILD','SOMETHING','THAT','LASTS'],['ALL','HEART','NO','PRICE']];
export const controlColors=['#e6bb7e','#80bfbc','#b1a9d0','#e79d90'];
export const laneCenter=lane=>70+140*lane;
export const roadLane=note=>note.lane%3;
export function currentPrompt(notes,time,game){
 const note=notes.find(n=>!n.done);if(!note)return null;
 const start=game==='andrew-prim'?Math.floor(note.id/4)*5.3+1.7:note.id===0?0:notes[note.id-1].at;
 return {note,start,ready:time>=start&&time<=note.at,remaining:Math.max(0,note.at-time)};
}
export function wordOptions(note){const phrase=phrases[Math.floor(note.id/4)],shift=(Math.floor(note.id/4)+1)%4;return phrase.map((_,i)=>phrase[(i+shift)%4]);}
export function correctChoice(game,note){
 if(game==='brenno')return note.id%6;
 if(game==='gavin-the-hotrod')return roadLane(note);
 if(game==='lj-the-messenger')return note.kind;
 if(game==='andrew-prim')return note.lane;
 if(game==='tonyxtrotter')return wordOptions(note).indexOf(phrases[Math.floor(note.id/4)][note.id%4]);
 return null;
}
export function judgeChoice(game,notes,index,time){
 const prompt=currentPrompt(notes,time,game),count=crewGames[game]?.labels?.length;
 if(!prompt?.ready||!Number.isInteger(index)||index<0||index>=count)return null;
 const hit=index===correctChoice(game,prompt.note);
 return {note:prompt.note,hit,perfect:hit&&time-prompt.start<=.75};
}
export function spotlightX(note,time){return Math.max(48,Math.min(372,note.x+Math.sin((time-note.at)*2.2)*42));}
export function judgePosition(game,note,x){
 if(game==='gavin-the-hotrod'){const distance=Math.abs(x-laneCenter(roadLane(note)));return {hit:distance<58,perfect:distance<23};}
 const distance=Math.abs(x-note.x);return {hit:distance<(game==='dearis'?48:32),perfect:distance<(game==='dearis'?19:12)};
}
function text(g,value,x,y,size=15,color='#f4eee4'){g.fillStyle=color;g.font=`bold ${size}px sans-serif`;g.textAlign='center';g.fillText(value,x,y);}
function panel(g,x,y,w,h,color='#202127'){g.fillStyle=color;g.fillRect(x,y,w,h);g.strokeStyle='#ffffff28';g.lineWidth=1;g.strokeRect(x,y,w,h);}
function car(g,x,y){
 g.fillStyle='#090a0d';g.fillRect(x-29,y-40,58,104);g.fillStyle='#8d3936';g.fillRect(x-23,y-48,46,112);g.fillStyle='#d7d4c4';g.fillRect(x-16,y-20,32,24);g.fillStyle='#282b33';g.fillRect(x-16,y+21,32,18);g.fillStyle='#e2b77e';g.fillRect(x-21,y-46,9,5);g.fillRect(x+12,y-46,9,5);g.fillStyle='#d36559';g.fillRect(x-21,y+58,9,5);g.fillRect(x+12,y+58,9,5);
}
export function drawCrewGame(g,{game,notes,time,px,phase,reduced=false,events=[]}){
 const cfg=crewGames[game],prompt=currentPrompt(notes,time,game),note=prompt?.note;
 g.fillStyle='#111216';g.fillRect(0,0,420,560);
 text(g,cfg.title,210,33,26);text(g,`${events.length} / 20`,210,58,12,'#bdb7ad');
 if(cfg.mode==='find'){
  drawPerson(g,84,214,'brenno',{scale:2.2});panel(g,149,83,232,139,'#2d3433');text(g,'FIND THIS FAN',265,107,13,'#cce0c7');
  if(note)drawPerson(g,265,217,brennoFan(note.id),{scale:1.7});
  for(let i=0;i<6;i++){const x=78+(i%3)*132,y=350+Math.floor(i/3)*130;panel(g,x-54,y-112,108,118,'#25292b');
   const fanId=note?(note.id+(i-note.id%6+6)%6)%30:i;
   drawPerson(g,x,y-6,brennoFan(fanId),{scale:1.65});text(g,String(i+1),x-39,y-89,17,'#eac492');}
 }else if(cfg.mode==='route'){
  const turns=['LEFT','STRAIGHT','RIGHT'],turn=note?roadLane(note):1;
  drawPerson(g,62,217,game,{scale:2.1});panel(g,129,86,268,113,'#203b32');text(g,'NEXT TURN',263,111,12,'#aec6af');text(g,turns[turn],263,151,29);text(g,`STOP ${(note?.id??19)+1} / 20 · APOLLO SHOW`,263,180,11);
  g.fillStyle='#262b2c';g.fillRect(24,242,372,239);g.strokeStyle='#4a5051';g.lineWidth=48;g.beginPath();g.moveTo(210,470);g.lineTo(210,317);g.moveTo(55,317);g.lineTo(365,317);g.moveTo(210,317);g.lineTo(210,255);g.stroke();
  g.strokeStyle='#b5b19c';g.lineWidth=2;g.setLineDash([8,8]);g.beginPath();g.moveTo(210,470);g.lineTo(210,255);g.moveTo(55,317);g.lineTo(365,317);g.stroke();g.setLineDash([]);
  car(g,210,409);text(g,'←',57,323,25);text(g,'↑',210,276,25);text(g,'→',362,323,25);
 }else if(cfg.mode==='spotlight'){
  g.fillStyle='#211d26';g.fillRect(0,105,420,390);g.fillStyle='#382d30';g.fillRect(0,470,420,25);
  const x=note?spotlightX(note,time):210;
  g.fillStyle='#f9e7bb1c';g.beginPath();g.moveTo(px,100);g.lineTo(px-80,481);g.lineTo(px+80,481);g.closePath();g.fill();
  drawPerson(g,x,475,game,{scale:4.1,walking:!reduced,frame:time*3});
  g.fillStyle='#f8e6b930';g.beginPath();g.ellipse(px,478,65,14,0,0,7);g.fill();
  g.strokeStyle='#f0d39b';g.lineWidth=2;g.strokeRect(px-46,215,92,224);text(g,'KEEP HIM IN THE LIGHT',210,525,15,'#e2ccac');
 }else if(cfg.mode==='slider'){
  drawPerson(g,210,300,game,{scale:3.55});
  panel(g,24,330,372,155);text(g,'MATCH THE GOLD NOTE',210,357,16);
  g.strokeStyle='#5b6066';g.lineWidth=4;g.beginPath();g.moveTo(42,412);g.lineTo(378,412);g.stroke();
  if(note){g.fillStyle='#e2b77e33';g.fillRect(note.x-32,380,64,65);g.strokeStyle='#e2b77e';g.lineWidth=2;g.strokeRect(note.x-12,380,24,65);text(g,'♪',note.x,407,27,'#edc88e');}
  g.fillStyle='#90cfc2';g.beginPath();g.arc(px,439,13,0,7);g.fill();text(g,'LOW',47,472,10,'#bfbab1');text(g,'HIGH',372,472,10,'#bfbab1');
 }else if(cfg.mode==='memory'){
  drawPerson(g,210,238,game,{scale:2.5});
  const group=Math.floor((note?.id??19)/4),start=group*5.3+.5,preview=time>=start&&time<start+1.2,flash=preview?Math.floor((time-start)/.3):-1;
  text(g,time<start?'NEXT PATTERN…':preview?'WATCH THE PATTERN':'YOUR TURN · REPEAT IT',210,272,20,preview?'#e9c18b':'#9dd6c6');
  for(let i=0;i<4;i++){const n=notes[group*4+i],x=37+i*94;panel(g,x,300,64,55,preview&&flash===i?controlColors[n.lane]:'#27282e');text(g,n?.done?(n.rejected?'×':'✓'):preview&&flash===i?String(n.lane+1):'•',x+32,337,25,preview&&flash===i?'#17171b':'#e7ddd0');}
  text(g,`PATTERN ${group+1} OF 5`,210,390,15);text(g,'KICK  /  SNARE  /  HATS  /  BASS',210,422,13,'#bfbab1');
 }else if(cfg.mode==='words'){
  drawPerson(g,210,225,game,{scale:2.4});
  const phrase=phrases[Math.floor((note?.id??19)/4)],step=(note?.id??20)%4;
  text(g,'BUILD THIS LINE',210,260,12,'#beb8b1');text(g,phrase.join(' '),210,288,17,'#e7c99e');
  for(let i=0;i<4;i++){const x=15+i*100;panel(g,x,323,90,55);const missed=notes[Math.floor((note?.id??19)/4)*4+i]?.rejected;text(g,i<step?(missed?'×':phrase[i]):'____',x+45,357,12,i<step?(missed?'#e79d90':'#a2d6c3'):'#838186');}
  text(g,'Original word puzzles · not song lyrics',210,435,11,'#9c9891');
 }else{
  drawPerson(g,210,260,game,{scale:2.9});panel(g,72,290,276,137,'#e8dfcc');
  g.strokeStyle='#9c927e';g.beginPath();g.moveTo(72,290);g.lineTo(210,347);g.lineTo(348,290);g.stroke();
  text(g,'DELIVER TO',210,367,12,'#5c5045');text(g,note?cfg.labels[note.kind]:'DELIVERED',210,398,25,'#24212a');
 }
 if(prompt&&phase==='playing'){
  const duration=Math.max(.3,note.at-prompt.start),ratio=Math.min(1,prompt.remaining/duration);g.fillStyle='#39383c';g.fillRect(42,504,336,7);g.fillStyle='#e6bc83';g.fillRect(42,504,336*ratio,7);
  if(cfg.mode!=='spotlight')text(g,prompt.ready?`${prompt.remaining.toFixed(1)}s`:cfg.mode==='memory'?'WATCH FIRST':'NEXT UP…',210,540,13,'#d8c8b3');
 }
}
