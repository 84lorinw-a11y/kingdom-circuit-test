import {drawPerson} from './sprites.mjs?v=apollo-23';
import {apolloCrew} from './apollo-crew.mjs?v=apollo-23';
import {brennoFan} from './crowds.mjs?v=apollo-23';
export const artistGames={
 marty:{title:'APOLLO IS NOT FOR SALE',instruction:'Tap buyout offers to stamp them away; let your crew and new music through.',gesture:'TAP OFFERS',seconds:40,result:'STILL INDEPENDENT',unit:'good calls'},
 brenno:{title:'BRING YOUR PEOPLE',instruction:'Swipe to steer your growing crew around barriers and bring them through the doors.',gesture:'SWIPE TO TURN',seconds:45,result:'YOUR PEOPLE MADE IT',unit:'friends collected'},
 'ryan-ellis':{title:'SOUNDWAVE SURFER',instruction:'Drag up and down to ride the wave and collect the notes.',gesture:'DRAG UP / DOWN',seconds:40,result:'RIDE THE SOUND',unit:'notes collected'},
 'gavin-the-hotrod':{title:'HOTROD TO THE SHOW',instruction:'Swipe between lanes to dodge road cases and collect backstage passes.',gesture:'SWIPE LEFT / RIGHT',seconds:40,result:'MADE IT TO THE SHOW',unit:'passes collected'},
 'lj-the-messenger':{title:'SPECIAL DELIVERY',instruction:'Swipe upward from the paper plane to send invitations to the moving fans.',gesture:'SWIPE TO THROW',seconds:45,result:'THE INVITES ARE OUT',unit:'invitations delivered'},
 dearis:{title:'FIND THE LOST FILES',instruction:'Remember the studio files, then tap matching pairs to recover the session.',gesture:'TAP MATCHING PAIRS',seconds:45,result:'SESSION RECOVERED',unit:'pairs recovered'},
 tonyxtrotter:{title:'THE ART OF GETTING UP',instruction:'Drag sideways to land on the cases, collect passes and keep climbing.',gesture:'DRAG LEFT / RIGHT',seconds:45,result:'KEEP GETTING UP',unit:'passes collected'},
 'andrew-prim':{title:'RELEASE DAY RUSH',instruction:'Drag each song, cover or pass from the conveyor into its matching station.',gesture:'DRAG TO SORT',seconds:40,result:'READY FOR RELEASE',unit:'assets sorted'}
};
export const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
export const waveY=t=>295+Math.sin(t*1.5)*100+Math.sin(t*.61)*30;
export const offerKind=n=>n.id%5===3?'crew':n.id%5===4?'music':'offer';
export const itemX=(n,t,lead=3)=>-65+(t-(n.at-lead))/lead*425;
export const targetPoint=(n,t)=>({x:clamp(n.x+Math.sin(t*1.7+n.id)*25,55,365),y:165+n.id%3*65});
export function launchPlane(a,b){let vx=(b.x-a.x)*3.2,vy=(b.y-a.y)*3.2;const speed=Math.hypot(vx,vy);if(speed<90||vy>-45)return null;const scale=Math.min(1,850/speed);return {x:210,y:502,vx:vx*scale,vy:vy*scale,age:0};}
export function memoryDeck(board=0,seed=1){const deck=Array.from({length:10},(_,i)=>i%5);let s=(seed+board*997)>>>0;for(let i=deck.length-1;i>0;i--){s=(Math.imul(s,1664525)+1013904223)>>>0;const j=s%(i+1);[deck[i],deck[j]]=[deck[j],deck[i]];}return deck;}
const text=(g,s,x,y,size=15,color='#eee5d6')=>{g.fillStyle=color;g.font=`700 ${size}px system-ui,sans-serif`;g.textAlign='center';g.fillText(s,x,y);};
const box=(g,x,y,w,h,color='#26272c')=>{g.fillStyle=color;g.fillRect(x,y,w,h);g.strokeStyle='#ffffff22';g.lineWidth=1;g.strokeRect(x,y,w,h);};
function noteIcon(g,x,y,color='#e1ba79'){text(g,'♪',x,y+10,32,color);}
function pass(g,x,y,size=1){g.save();g.translate(x,y);g.scale(size,size);g.fillStyle='#d5c39e';g.fillRect(-19,-26,38,49);g.fillStyle='#a8443c';g.fillRect(-19,-26,38,10);g.fillStyle='#24252a';g.fillRect(-7,-20,14,3);text(g,'PASS',0,5,10,'#27252b');g.restore();}
function caseBox(g,x,y,w=100,h=20){box(g,x-w/2,y,w,h,'#292b2d');g.strokeStyle='#96938c';g.lineWidth=2;g.strokeRect(x-w/2,y,w,h);g.fillStyle='#090b10';g.fillRect(x-9,y+h*.4,18,4);}
function car(g,x,y,boost=false){g.fillStyle='#0a0b0d';g.fillRect(x-39,y-43,78,91);g.fillStyle=boost?'#c37243':'#9b403c';g.fillRect(x-32,y-60,64,128);g.fillStyle='#bac8c7';g.fillRect(x-26,y-36,52,33);g.fillStyle='#272f35';g.fillRect(x-24,y+29,48,23);g.fillStyle='#f0d9a3';g.fillRect(x-30,y-58,12,7);g.fillRect(x+18,y-58,12,7);}
function cassette(g,x,y,kind=0){box(g,x-30,y-20,60,40,['#8b6b59','#667e77','#7b687c','#a18959','#6a788b'][kind]);g.fillStyle='#d8cdb4';g.fillRect(x-24,y-13,48,15);g.fillStyle='#24242a';for(const dx of [-13,13]){g.beginPath();g.arc(x+dx,y-5,5,0,7);g.fill();}text(g,['MIX','DRUMS','VOCALS','COVER','MASTER'][kind],x,y+15,8);}
export function createArtistRound(game,{notes,seed=1,onResolve=()=>{},onMistake=()=>{}}){
 const cfg=artistGames[game];if(!cfg)throw Error('Unknown artist arcade');
 let t=0,last=0,combo=0,hitCount=0,message='',messageUntil=0,drag=null,focus=0;
 const s={x:210,y:295,targetX:210,targetY:295,lane:1,boost:0,delivered:0,pile:0,crew:0,plane:null,planeTrail:[],cursor:null,
  snake:[{x:4,y:7}],direction:{x:0,y:-1},nextDirection:{x:0,y:-1},snakeClock:0,carried:0,clean:true,food:null,
  board:0,deck:memoryDeck(0,seed),open:[],matched:[],revealUntil:1.5,flipUntil:0,boardUntil:0,
  jumpY:438,jumpV:-340,camera:0,lastPlatform:0,platforms:Array.from({length:25},(_,i)=>({x:i?85+((Math.sin(seed+i*7.5)+1)/2)*250:210,y:500-i*63,moving:i%4===2})),sorted:new Set(),packages:0};
 const barriers=[{x:2,y:2},{x:2,y:3},{x:6,y:4},{x:6,y:5},{x:4,y:1}];
 const tell=(msg)=>{message=msg;messageUntil=t+1.2;};
 function resolve(n,hit,clean=true){if(!n||n.done)return; n.done=true;n.rejected=!hit;n.resolvedAt=t;n.hit=hit;combo=hit?combo+1:0;if(hit){hitCount++;if(game==='marty'&&combo%2===0)s.crew=Math.min(8,s.crew+1);}onResolve(n,hit,hit&&clean);tell(hit?game==='marty'?(offerKind(n)==='offer'?'NOT FOR SALE!':'WELCOME TO APOLLO'):'NICE!':game==='marty'?(offerKind(n)==='music'?'THAT’S OUR MUSIC!':'THAT WAS THE CREW!'):'KEEP GOING');}
 function mistake(msg){combo=0;s.clean=false;onMistake(msg);tell(msg);}
 const pending=()=>notes.find(n=>!n.done);
 const ready=n=>n&&t>=(n.id?notes[n.id-1].at:0)&&t<=n.at;
 function spawnFood(){const n=pending();if(!n){s.food=null;return;}for(let k=0;k<81;k++){const cell=(Math.floor(n.x)+n.id*13+k*17)%81,x=cell%9,y=Math.floor(cell/9);if(!s.snake.some(p=>p.x===x&&p.y===y)&&!barriers.some(p=>p.x===x&&p.y===y)&&!(x===8&&y===0)){s.food={x,y};return;}}s.food={x:0,y:0};}
 spawnFood();
 const platformX=(p,time)=>p.x+(p.moving?Math.sin(time*1.5+p.y)*23:0);
 function turn(dx,dy){if(dx===-s.direction.x&&dy===-s.direction.y&&s.snake.length>1)return;s.nextDirection={x:dx,y:dy};}
 function matchCard(index){if(s.board>=4||t<s.revealUntil||t<s.flipUntil||s.open.includes(index)||s.matched.includes(index)||index<0||index>=10)return;s.open.push(index);if(s.open.length===2){const [a,b]=s.open;if(s.deck[a]===s.deck[b]){s.matched.push(a,b);resolve(notes[s.board*5+s.deck[a]],true,s.clean);s.clean=true;s.open=[];if(s.matched.length===10)s.boardUntil=t+.65;}else{mistake('TRY ANOTHER PAIR');s.flipUntil=t+.65;}}}
 function sortItem(n,index){if(!n)return;const hit=n.id%3===index;resolve(n,hit,hit&&t-(n.at-3)<1.5);if(hit){s.sorted.add(index);if(s.sorted.size===3){s.packages++;s.sorted.clear();tell('RELEASE PACKAGE READY');}}}
 function point(type,p){
  if(type==='down'){drag={start:p,last:p,note:null};s.cursor=p;
   if(game==='marty'){const n=notes.find(n=>!n.done&&t>=n.at-3&&t<=n.at&&Math.abs(p.x-itemX(n,t))<62&&Math.abs(p.y-(175+n.id%3*105))<42);if(n){const kind=offerKind(n);resolve(n,kind==='offer',kind==='offer'&&itemX(n,t)<235);if(kind==='offer')s.pile++;}}
   if(game==='dearis'){const col=Math.floor((p.x-20)/128),row=Math.floor((p.y-140)/96);if(col>=0&&col<3&&row>=0&&row<4)matchCard(row*3+col);}
   if(game==='andrew-prim')drag.note=notes.find(n=>!n.done&&t>=n.at-3&&t<=n.at&&Math.abs(p.x-itemX(n,t))<48&&Math.abs(p.y-250)<55);
  }
  if(type==='move'||type==='down'){
   if(game==='ryan-ellis')s.targetY=clamp(p.y,145,445);
   if(game==='tonyxtrotter')s.targetX=clamp(p.x,30,390);
   if(drag){drag.last=p;s.cursor=p;}
  }
  if(type==='up'||type==='cancel'){
   if(drag&&type==='up'){
    const dx=p.x-drag.start.x,dy=p.y-drag.start.y;
    if(game==='brenno'&&Math.hypot(dx,dy)>15){if(Math.abs(dx)>Math.abs(dy))turn(Math.sign(dx),0);else turn(0,Math.sign(dy));}
    if(game==='gavin-the-hotrod'){if(Math.abs(dx)>18)s.lane=clamp(s.lane+Math.sign(dx),0,2);else s.lane=clamp(Math.floor(p.x/140),0,2);}
    if(game==='lj-the-messenger'&&!s.plane&&ready(pending())){s.plane=launchPlane(drag.start,p);s.planeTrail=[];}
    if(game==='andrew-prim'&&drag.note&&p.y>=407&&p.y<=540)sortItem(drag.note,clamp(Math.floor(p.x/140),0,2));
   }drag=null;s.cursor=null;
  }
 }
 function key(key){
  if(game==='brenno'){const d={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[key];if(d)turn(...d);}
  if(game==='gavin-the-hotrod'){if(key==='ArrowLeft')s.lane=clamp(s.lane-1,0,2);if(key==='ArrowRight')s.lane=clamp(s.lane+1,0,2);}
  if(game==='ryan-ellis'){if(key==='ArrowUp')s.targetY=clamp(s.targetY-25,145,445);if(key==='ArrowDown')s.targetY=clamp(s.targetY+25,145,445);}
  if(game==='tonyxtrotter'){if(key==='ArrowLeft')s.targetX=clamp(s.targetX-35,30,390);if(key==='ArrowRight')s.targetX=clamp(s.targetX+35,30,390);}
  if(game==='dearis'){if(key==='ArrowLeft')focus=(focus+9)%10;if(key==='ArrowRight')focus=(focus+1)%10;if(key==='ArrowUp')focus=(focus+7)%10;if(key==='ArrowDown')focus=(focus+3)%10;if(key===' '||key==='Enter')matchCard(focus);}
  if(game==='andrew-prim'&&/^[123]$/.test(key))sortItem(notes.find(n=>!n.done&&t>=n.at-3),Number(key)-1);
  if(game==='marty'&&/^[123]$/.test(key)){const n=notes.find(n=>!n.done&&n.id%3===Number(key)-1&&t>=n.at-3&&t<=n.at);if(n)point('down',{x:itemX(n,t),y:175+n.id%3*105});}
  if(game==='lj-the-messenger'&&(key===' '||key==='Enter')&&ready(pending())&&!s.plane){const q=targetPoint(pending(),t+.6);s.plane={x:210,y:502,vx:(q.x-210)/.6,vy:(q.y-502-85*.36)/.6,age:0};}
 }
 function step(time,dt){
  t=time;dt=Math.min(.05,Math.max(0,dt));s.x+=(s.targetX-s.x)*Math.min(1,dt*12);s.y+=(s.targetY-s.y)*Math.min(1,dt*14);
  if(game==='marty')for(const n of notes)if(!n.done&&t>=n.at){const friendly=offerKind(n)!=='offer';resolve(n,friendly,friendly);if(!friendly)tell('A BUYER REACHED THE DESK');}
  if(game==='ryan-ellis')for(const n of notes)if(!n.done&&t>=n.at){const d=Math.abs(s.y-waveY(n.at));resolve(n,d<52,d<22);}
  if(game==='gavin-the-hotrod'){s.targetX=70+s.lane*140;for(const n of notes)if(!n.done&&t>=n.at){const distance=Math.abs(s.x-(70+n.lane%3*140));resolve(n,distance<58,distance<22);if(combo&&combo%5===0)s.boost=t+2;}}
  if(game==='brenno'){
   s.snakeClock+=dt;if(s.snakeClock>.155){s.snakeClock=0;s.direction=s.nextDirection;const h={x:s.snake[0].x+s.direction.x,y:s.snake[0].y+s.direction.y};
    if(h.x<0||h.x>8||h.y<0||h.y>8||barriers.some(p=>p.x===h.x&&p.y===h.y)||s.snake.slice(0,-1).some(p=>p.x===h.x&&p.y===h.y)){
     mistake('CREW DETOUR · KEEP GOING');s.snake=[{x:4,y:7}];s.direction=s.nextDirection={x:0,y:-1};s.carried=0;spawnFood();
    }else{s.snake.unshift(h);const food=s.food&&h.x===s.food.x&&h.y===s.food.y;if(food){resolve(pending(),true,s.clean);s.clean=true;s.carried++;spawnFood();}else s.snake.pop();
     if(h.x===8&&h.y===0&&s.carried){s.delivered+=s.carried;s.carried=0;s.snake=[h];tell('YOUR PEOPLE ARE INSIDE!');}}
   }
  }
  if(game==='lj-the-messenger'){
   const n=pending();if(s.plane&&n){const p=s.plane;p.age+=dt;p.vy+=170*dt;p.x+=p.vx*dt;p.y+=p.vy*dt;s.planeTrail.push({x:p.x,y:p.y});if(s.planeTrail.length>12)s.planeTrail.shift();const q=targetPoint(n,t),d=Math.hypot(p.x-q.x,p.y-q.y);
    if(d<43){resolve(n,true,d<24);s.delivered++;s.plane=null;}
    else if(p.x<-30||p.x>450||p.y<-40||p.y>560||p.age>1.5){mistake('MISSED · THROW AGAIN');s.plane=null;}
   }
   for(const n of notes)if(!n.done&&t>=n.at){resolve(n,false);s.plane=null;}
  }
  if(game==='dearis'){
   if(s.flipUntil&&t>=s.flipUntil){s.open=[];s.flipUntil=0;}
   if(s.boardUntil&&t>=s.boardUntil){s.board++;s.boardUntil=0;s.deck=memoryDeck(s.board,seed);s.matched=[];s.open=[];s.revealUntil=t+1.2;s.clean=true;}
  }
  if(game==='tonyxtrotter'){
   const prev=s.jumpY;s.jumpV+=650*dt;s.jumpY+=s.jumpV*dt;
   if(s.jumpV>0)for(let i=0;i<s.platforms.length;i++){const p=s.platforms[i],x=platformX(p,t);if(prev<=p.y&&s.jumpY>=p.y&&Math.abs(s.x-x)<61){s.jumpY=p.y;s.jumpV=combo>0&&combo%3===0?-390:-340;s.lastPlatform=Math.max(s.lastPlatform,i);if(i>0&&i<=20)resolve(notes[i-1],true,Math.abs(s.x-x)<25);break;}}
   s.camera=Math.min(s.camera,s.jumpY-235);
   if(s.jumpY>s.camera+570){mistake('BACK ON YOUR FEET');const p=s.platforms[s.lastPlatform];s.jumpY=p.y-2;s.x=s.targetX=platformX(p,t);s.jumpV=-340;s.camera=Math.min(0,s.jumpY-235);}
  }
  if(game==='andrew-prim')for(const n of notes)if(!n.done&&t>=n.at){resolve(n,false);if(drag?.note===n)drag.note=null;}
  last=t;
 }
 function draw(g,{art={},reduced=false}={}){
  g.fillStyle='#15161b';g.fillRect(0,0,420,560);
  if(art.apolloPoster){g.globalAlpha=.06;g.drawImage(art.apolloPoster,0,0,420,560);g.globalAlpha=1;}
  text(g,cfg.title,210,32,cfg.title.length>22?21:25);text(g,`${hitCount} / 20  ·  ${cfg.gesture}`,210,57,11,'#c2b4a4');
  if(game==='marty'){
   box(g,8,75,404,70,'#21292d');for(let x=16;x<410;x+=32){g.strokeStyle='#4b5559';g.beginPath();g.moveTo(x,80);g.lineTo(x,140);g.stroke();}box(g,12,128,396,10,'#786650');const studioCrew=apolloCrew.filter(p=>p.id!=='marty');for(let i=0;i<s.crew;i++)drawPerson(g,34+i*49,130,studioCrew[i].id,{scale:.9,lean:reduced?0:Math.sin(t*3+i)*.025});
   for(let i=0;i<4;i++){const x=44+i*96;box(g,x-19,122,38,13,'#393538');g.fillStyle='#b6baa8';for(let key=0;key<6;key++)g.fillRect(x-16+key*5,125,3,7);if(i<s.crew/2){g.fillStyle='#79aa8a';g.fillRect(x-12,117,24,3);}}
   for(let row=0;row<3;row++){box(g,8,148+row*105,294,93,'#202125');g.setLineDash([7,10]);g.strokeStyle='#9a866344';g.beginPath();g.moveTo(20,195+row*105);g.lineTo(300,195+row*105);g.stroke();g.setLineDash([]);}
   box(g,312,151,100,40,'#3a3028');text(g,'APOLLO HQ',362,176,13,'#d4b583');drawPerson(g,362,468,'marty',{scale:3.65});box(g,300,380,120,122,'#594b3d');box(g,294,373,126,13,'#9e8a69');box(g,321,349,48,24,'#14191b');g.fillStyle='#7eaaa1';g.fillRect(326,354,38,14);text(g,'NOT FOR',360,430,14);text(g,'SALE',360,454,22,'#e6ba82');text(g,'STILL INDEPENDENT',210,477,11,'#adbaa5');
   for(const n of notes){const kind=offerKind(n),age=t-n.resolvedAt;let x=itemX(n,t),y=175+n.id%3*105;if(n.done){if(!n.hit||kind!=='offer'||age>.55)continue;x-=age*600;y-=age*200;}if(x<-80||x>338||t<n.at-3)continue;
    if(kind==='offer'){if(!n.done){g.fillStyle='#bda388';g.beginPath();g.arc(x-55,y-45,12,0,7);g.fill();g.fillStyle='#383e48';g.fillRect(x-66,y-35,23,17);g.fillStyle='#141820';g.fillRect(x-66,y-51,22,4);}if(n.id%2){g.strokeStyle='#a48a68';g.lineWidth=4;g.strokeRect(x-14,y-44,28,10);}box(g,x-59,y-35,118,70,n.id%2?'#80664c':'#e5dcc7');const color=n.id%2?'#fff0d7':'#28252c';text(g,'BUY APOLLO',x,y-15,11,color);const offer=['$10 MILLION','PRIVATE ISLAND','UNLIMITED SNACKS','YOUR OWN JET','A GOLDEN DESK','100% CONTROL'][Math.floor(n.id/3)%6];text(g,offer,x,y+5,10,color);text(g,n.done?'NOT FOR SALE':'OWNERSHIP: US',x,y+24,10,n.done?'#ce5549':color);}
    else if(kind==='crew'){box(g,x-36,y-43,72,85,'#263d32');drawPerson(g,x,y+36,apolloCrew[Math.floor(n.id/5)+1].id,{scale:1.1});text(g,'CREW',x,y-27,10,'#b6d6b8');}
    else{box(g,x-39,y-34,78,68,'#293742');noteIcon(g,x,y-6);text(g,'NEW MUSIC',x,y+24,9,'#b6d6d2');}
   }
   for(let i=0;i<Math.min(10,s.pile);i++){g.fillStyle='#b4a78c';g.fillRect(16+i*8,515-(i%3)*5,30,18);}text(g,'REJECTED · OUTSIDE',101,553,10,'#b9a48a');
  }else if(game==='brenno'){
   box(g,23,115,374,374,'#24272a');for(let x=0;x<9;x++)for(let y=0;y<9;y++){g.strokeStyle='#ffffff0a';g.strokeRect(30+x*40,121+y*40,40,40);}
   box(g,350,104,42,51,'#355447');text(g,'IN →',371,121,10,'#dcddbb');
   barriers.forEach(p=>caseBox(g,50+p.x*40,135+p.y*40,32,22));
   s.snake.slice(1).reverse().forEach((p,i)=>drawPerson(g,50+p.x*40,159+p.y*40,brennoFan(i),{scale:.65}));
   const h=s.snake[0];drawPerson(g,50+h.x*40,160+h.y*40,'brenno',{scale:1.05});
   if(s.food){const x=50+s.food.x*40,y=155+s.food.y*40;g.strokeStyle='#e4bb7c';g.lineWidth=2;g.strokeRect(x-17,y-33,34,38);drawPerson(g,x,y,brennoFan(pending()?.id??0),{scale:.65});}
   text(g,`${s.carried} WITH YOU  ·  ${s.delivered} INSIDE`,210,523,16,'#e2c198');
  }else if(game==='ryan-ellis'){
   const progress=hitCount/20;g.fillStyle=`rgba(166,58,68,${progress*.25})`;g.fillRect(0,85,420,450);
   for(let i=0;i<Math.floor(hitCount/2);i++)drawPerson(g,25+i*41,550,brennoFan(i),{scale:1.2});
   g.strokeStyle='#74b9c7';g.lineWidth=6;g.beginPath();for(let x=0;x<=420;x+=5){const y=waveY(t+(x-100)/130);if(!x)g.moveTo(x,y);else g.lineTo(x,y);}g.stroke();
   g.strokeStyle='#d7e5d4';g.lineWidth=1;g.stroke();for(const n of notes){if(n.done)continue;const x=100+(n.at-t)*130;if(x<0||x>440)continue;noteIcon(g,x,waveY(n.at),'#f0c477');}
   drawPerson(g,100,s.y+22,'ryan-ellis',{scale:1.55});g.fillStyle='#d9ba84';g.beginPath();g.ellipse(100,s.y+26,37,6,-.12,0,7);g.fill();text(g,'STAY WITH THE WAVE',210,96,12,'#b2cfd2');
  }else if(game==='gavin-the-hotrod'){
   if(t>cfg.seconds-2&&art.outside){g.drawImage(art.outside,0,75,420,260);}else{g.fillStyle='#25282c';g.beginPath();g.moveTo(164,90);g.lineTo(256,90);g.lineTo(420,560);g.lineTo(0,560);g.closePath();g.fill();}
   for(let i=0;i<12;i++){const z=((i/12+t*(s.boost>t?.7:.35))%1),y=90+z*z*470;g.fillStyle='#d6c4a1';g.fillRect(210-(10+z*60)-2,y,3,6+z*20);g.fillRect(210+(10+z*60),y,3,6+z*20);}
   for(const n of notes){if(n.done||t<n.at-3)continue;const z=clamp(1-(n.at-t)/3,0,1),y=95+z*z*350,scale=.2+z*.8;for(let lane=0;lane<3;lane++){const x=210+(lane-1)*140*z;if(lane===n.lane%3)pass(g,x,y,scale);else{g.save();g.translate(x,y);g.scale(scale,scale);caseBox(g,0,-21,86,42);g.restore();}}}
   car(g,s.x,454,s.boost>t);if(s.boost>t){text(g,'BOOST! · THE CREW IS HYPED',210,100,16,'#edc88a');drawPerson(g,s.x+15,447,'marty',{scale:.7});}
  }else if(game==='lj-the-messenger'){
   const n=pending();for(let row=0;row<3;row++)for(let col=0;col<3;col++){const x=26+col*132,y=101+row*90;box(g,x,y,105,78,'#363134');box(g,x+20,y+10,64,48,'#121820');g.fillStyle='#7b6b5b';g.fillRect(x+12,y+62,80,6);}
   if(n){const q=targetPoint(n,t);g.strokeStyle='#e9bc79';g.lineWidth=3;g.strokeRect(q.x-33,q.y-59,66,72);drawPerson(g,q.x,q.y+10,brennoFan(n.id),{scale:1.1});}
   for(let i=0;i<Math.min(s.delivered,10);i++)drawPerson(g,22+i*41,425,brennoFan(i),{scale:.75});
   const p=s.plane||{x:210,y:502,vx:0,vy:-1};g.strokeStyle='#d6d4bb88';g.lineWidth=2;g.beginPath();s.planeTrail.forEach((q,i)=>i?g.lineTo(q.x,q.y):g.moveTo(q.x,q.y));g.stroke();
   if(drag&&!s.plane){g.setLineDash([5,6]);g.beginPath();g.moveTo(210,502);g.lineTo(210+(drag.last.x-drag.start.x),502+(drag.last.y-drag.start.y));g.stroke();g.setLineDash([]);}
   g.save();g.translate(p.x,p.y);g.rotate(Math.atan2(p.vy,p.vx)+Math.PI/2);g.fillStyle='#f0e8d1';g.beginPath();g.moveTo(0,-20);g.lineTo(-20,16);g.lineTo(0,8);g.lineTo(20,16);g.closePath();g.fill();g.restore();
   drawPerson(g,65,551,'lj-the-messenger',{scale:1.5});text(g,'SWIPE UP TO INVITE',245,548,13);
  }else if(game==='dearis'){
   drawPerson(g,49,134,'dearis',{scale:1.1});text(g,`SESSION ${Math.min(4,s.board+1)} / 4`,222,95,16,'#c9d9bb');text(g,t<s.revealUntil?'REMEMBER THESE FILES':s.board>=4?'ALL FILES RECOVERED':'FIND THE MATCHES',222,118,12);
   if(s.board<4)for(let i=0;i<10;i++){const x=20+i%3*128,y=140+Math.floor(i/3)*96,visible=t<s.revealUntil||s.open.includes(i)||s.matched.includes(i);box(g,x,y,114,84,s.matched.includes(i)?'#29463b':'#2d2c32');if(i===focus){g.strokeStyle='#c8af83';g.lineWidth=2;g.strokeRect(x+2,y+2,110,80);}if(visible)cassette(g,x+57,y+42,s.deck[i]);else{text(g,'APOLLO',x+57,y+35,12,'#d1c4b1');text(g,'SESSION FILE',x+57,y+55,9,'#998d7a');}}
   for(let i=0;i<s.board;i++){caseBox(g,206+(i%2)*100,445+Math.floor(i/2)*42,85,27);text(g,['DRUMS','VOCALS','MIX','MASTER'][i],206+(i%2)*100,462+Math.floor(i/2)*42,9);}
  }else if(game==='tonyxtrotter'){
   g.strokeStyle='#ffffff0a';for(let y=0;y<560;y+=40){g.beginPath();g.moveTo(0,y-((s.camera%40)+40)%40);g.lineTo(420,y-((s.camera%40)+40)%40);g.stroke();}
   s.platforms.forEach((p,i)=>{const y=p.y-s.camera;if(y<85||y>560)return;const x=platformX(p,t);caseBox(g,x,y,110,22);if(i>0&&i<=20&&!notes[i-1].done)pass(g,x,y-24,.55);});
   drawPerson(g,s.x,s.jumpY-s.camera,'tonyxtrotter',{scale:1.45});text(g,`${Math.max(0,Math.floor((500-s.jumpY)/10))} m  ·  KEEP CLIMBING`,210,97,14,'#dfc18f');
  }else if(game==='andrew-prim'){
   drawPerson(g,357,181,'andrew-prim',{scale:1.8});box(g,18,88,264,76,'#292b30');text(g,['FINAL final mix?','Guest passes, please!','Cover looks hard.','More studio snacks?'][Math.floor(t/5)%4],150,117,16);text(g,'THE CREW NEEDS YOU',150,144,10,'#bea98e');
   box(g,0,206,420,103,'#303235');for(let x=-20;x<450;x+=25){g.strokeStyle='#131519';g.lineWidth=3;g.beginPath();g.moveTo(x+(reduced?0:t*50%25),207);g.lineTo(x+(reduced?0:t*50%25),308);g.stroke();}
   for(const n of notes){if(n.done||t<n.at-3||drag?.note===n)continue;const x=itemX(n,t);box(g,x-39,219,78,67,['#6b8177','#997e6b','#777c97'][n.id%3]);text(g,['♪ SONG','▧ COVER','PASS'][n.id%3],x,259,14);}
   for(let i=0;i<3;i++){box(g,i*140+8,411,124,110,['#334f42','#584337','#3e455f'][i]);text(g,['SONG FILES','COVER ART','GUEST PASSES'][i],70+i*140,446,12);text(g,['♪','▧','✓'][i],70+i*140,488,28);}
   if(drag?.note&&s.cursor){const p=s.cursor,n=drag.note;box(g,p.x-39,p.y-32,78,64,'#c4b995');text(g,['♪ SONG','▧ COVER','PASS'][n.id%3],p.x,p.y+5,14,'#242326');}
   for(let i=0;i<Math.min(s.packages,6);i++){box(g,12+i*67,336,59,48,'#251d21');if(art.apolloPoster)g.drawImage(art.apolloPoster,15+i*67,339,53,42);}text(g,`${s.packages} RELEASE PACKAGES READY`,210,400,13,'#d6be95');
  }
  if(t<messageUntil){box(g,45,65,330,29,'#101315ef');text(g,message,210,85,13,'#e8c083');}
 }
 return {step,draw,point,key,snapshot:()=>({time:t,combo,hits:hitCount,...s,notes}),meta:()=>({delivered:s.delivered})};
}
