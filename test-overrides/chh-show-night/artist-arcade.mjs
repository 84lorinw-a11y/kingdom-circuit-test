import {ryanHazards,touchesRyanHazard,RYAN_HAZARD_WINDOW} from './ryan-hazards.mjs?v=apollo-25';
import {createBrennoRound} from './brenno-surf.mjs?v=apollo-25';
import {drawArcadeScene} from './arcade-scenes.mjs?v=apollo-25';
import {drawHotrod} from './hotrod-scene.mjs?v=apollo-25';
import {drawMarty,martyRowY} from './marty-scene.mjs?v=apollo-25';
export const artistGames={
 marty:{title:'APOLLO IS NOT FOR SALE',instruction:'Tap buyout offers to stamp them away; let your crew and new music through.',gesture:'TAP OFFERS',seconds:40,result:'STILL INDEPENDENT',unit:'good calls'},
 brenno:{title:'SEND IT',instruction:'Tap in gold. Clear 20 dives in 40 seconds. Three misses = game over.',gesture:'TAP TO DIVE',seconds:40,result:'BACK ON STAGE',unit:'dives landed'},
 'ryan-ellis':{title:'SOUNDWAVE SURFER',instruction:'Drag up and down. Collect gold notes; dodge red X speakers.',gesture:'DRAG UP / DOWN',seconds:40,result:'RIDE THE SOUND',unit:'notes collected'},
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
export function createArtistRound(game,{notes,seed=1,onResolve=()=>{},onMistake=()=>{}}){
 if(game==='brenno')return createBrennoRound({notes,seconds:artistGames.brenno.seconds,onResolve});
 const cfg=artistGames[game];if(!cfg)throw Error('Unknown artist arcade');
 let t=0,last=0,combo=0,hitCount=0,message='',messageUntil=0,drag=null,focus=0;
 const s={x:210,y:295,targetX:210,targetY:295,lane:1,boost:0,delivered:0,pile:0,crew:0,plane:null,planeTrail:[],cursor:null,
  clean:true,ryanHazards:game==='ryan-ellis'?ryanHazards(notes,seed,waveY):[],ryanBumps:0,ryanDodged:0,ryanStatic:false,ryanBumpUntil:0,
  board:0,deck:memoryDeck(0,seed),open:[],matched:[],revealUntil:1.5,flipUntil:0,boardUntil:0,
  jumpY:438,jumpV:-340,camera:0,lastPlatform:0,platforms:Array.from({length:25},(_,i)=>({x:i?85+((Math.sin(seed+i*7.5)+1)/2)*250:210,y:500-i*63,moving:i%4===2})),sorted:new Set(),packages:0};
 const tell=(msg)=>{message=msg;messageUntil=t+1.2;};
 function resolve(n,hit,clean=true){if(!n||n.done)return; n.done=true;n.rejected=!hit;n.resolvedAt=t;n.hit=hit;combo=hit?combo+1:0;if(hit){hitCount++;if(game==='marty'&&combo%2===0)s.crew=Math.min(8,s.crew+1);}onResolve(n,hit,hit&&clean);tell(hit?game==='marty'?(offerKind(n)==='offer'?'NOT FOR SALE!':'WELCOME TO APOLLO'):'NICE!':game==='marty'?(offerKind(n)==='music'?'THAT’S OUR MUSIC!':'THAT WAS THE CREW!'):'KEEP GOING');}
 function mistake(msg){combo=0;s.clean=false;onMistake(msg);tell(msg);}
 const pending=()=>notes.find(n=>!n.done);
 const ready=n=>n&&t>=(n.id?notes[n.id-1].at:0)&&t<=n.at;
 const platformX=(p,time)=>p.x+(p.moving?Math.sin(time*1.5+p.y)*23:0);
 function matchCard(index){if(s.board>=4||t<s.revealUntil||t<s.flipUntil||s.open.includes(index)||s.matched.includes(index)||index<0||index>=10)return;s.open.push(index);if(s.open.length===2){const [a,b]=s.open;if(s.deck[a]===s.deck[b]){s.matched.push(a,b);resolve(notes[s.board*5+s.deck[a]],true,s.clean);s.clean=true;s.open=[];if(s.matched.length===10)s.boardUntil=t+.65;}else{mistake('TRY ANOTHER PAIR');s.flipUntil=t+.65;}}}
 function sortItem(n,index){if(!n)return;const hit=n.id%3===index;resolve(n,hit,hit&&t-(n.at-3)<1.5);if(hit){s.sorted.add(index);if(s.sorted.size===3){s.packages++;s.sorted.clear();tell('RELEASE PACKAGE READY');}}}
 function point(type,p){
  if(type==='down'){drag={start:p,last:p,note:null};s.cursor=p;
   if(game==='marty'){const n=notes.find(n=>!n.done&&t>=n.at-3&&t<=n.at&&Math.abs(p.x-itemX(n,t))<62&&Math.abs(p.y-martyRowY(n))<42);if(n){const kind=offerKind(n);resolve(n,kind==='offer',kind==='offer'&&itemX(n,t)<235);if(kind==='offer')s.pile++;}}
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
     if(game==='gavin-the-hotrod'){if(Math.abs(dx)>18)s.lane=clamp(s.lane+Math.sign(dx),0,2);else s.lane=clamp(Math.floor(p.x/140),0,2);}
    if(game==='lj-the-messenger'&&!s.plane&&ready(pending())){s.plane=launchPlane(drag.start,p);s.planeTrail=[];}
    if(game==='andrew-prim'&&drag.note&&p.y>=407&&p.y<=540)sortItem(drag.note,clamp(Math.floor(p.x/140),0,2));
   }drag=null;s.cursor=null;
  }
 }
 function key(key){
  if(game==='gavin-the-hotrod'){if(key==='ArrowLeft')s.lane=clamp(s.lane-1,0,2);if(key==='ArrowRight')s.lane=clamp(s.lane+1,0,2);}
  if(game==='ryan-ellis'){if(key==='ArrowUp')s.targetY=clamp(s.targetY-25,145,445);if(key==='ArrowDown')s.targetY=clamp(s.targetY+25,145,445);}
  if(game==='tonyxtrotter'){if(key==='ArrowLeft')s.targetX=clamp(s.targetX-35,30,390);if(key==='ArrowRight')s.targetX=clamp(s.targetX+35,30,390);}
  if(game==='dearis'){if(key==='ArrowLeft')focus=(focus+9)%10;if(key==='ArrowRight')focus=(focus+1)%10;if(key==='ArrowUp')focus=(focus+7)%10;if(key==='ArrowDown')focus=(focus+3)%10;if(key===' '||key==='Enter')matchCard(focus);}
  if(game==='andrew-prim'&&/^[123]$/.test(key))sortItem(notes.find(n=>!n.done&&t>=n.at-3),Number(key)-1);
  if(game==='marty'&&/^[123]$/.test(key)){const n=notes.find(n=>!n.done&&n.id%3===Number(key)-1&&t>=n.at-3&&t<=n.at);if(n)point('down',{x:itemX(n,t),y:martyRowY(n)});}
  if(game==='lj-the-messenger'&&(key===' '||key==='Enter')&&ready(pending())&&!s.plane){const q=targetPoint(pending(),t+.6);s.plane={x:210,y:502,vx:(q.x-210)/.6,vy:(q.y-502-85*.36)/.6,age:0};}
 }
 function step(time,dt){
  const previousY=s.y;
  t=time;dt=Math.min(.05,Math.max(0,dt));s.x+=(s.targetX-s.x)*Math.min(1,dt*12);s.y+=(s.targetY-s.y)*Math.min(1,dt*14);
  if(game==='marty')for(const n of notes)if(!n.done&&t>=n.at){const friendly=offerKind(n)!=='offer';resolve(n,friendly,friendly);if(!friendly)tell('A BUYER REACHED THE DESK');}
  if(game==='ryan-ellis'){
   for(const h of s.ryanHazards){
    if(h.done)continue;
    if(touchesRyanHazard(h,last,t,previousY,s.y)){
     h.done=h.hit=true;h.resolvedAt=t;s.ryanBumps++;s.ryanStatic=true;s.ryanBumpUntil=t+.65;
     mistake('FEEDBACK! · COMBO RESET');
    }else if(t>h.at+RYAN_HAZARD_WINDOW){h.done=true;h.resolvedAt=t;s.ryanDodged++;tell('NICE DODGE!');}
   }
   for(const n of notes)if(!n.done&&t>=n.at){
    const d=Math.abs(s.y-waveY(n.at)),staticHit=s.ryanStatic;
    resolve(n,d<52,d<22&&!staticHit);s.ryanStatic=false;
    if(d<52&&staticHit)tell('+40 · BACK IN THE GROOVE');
   }
  }
  if(game==='gavin-the-hotrod'){s.targetX=70+s.lane*140;for(const n of notes)if(!n.done&&t>=n.at){const distance=Math.abs(s.x-(70+n.lane%3*140));resolve(n,distance<58,distance<22);if(combo&&combo%5===0)s.boost=t+2;}}
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
 function draw(g,{art={},reduced=false,arrival=null}={}){
  if(game==='gavin-the-hotrod'){drawHotrod(g,{art,time:t,state:s,notes,hits:hitCount,reduced,arrival,message:t<messageUntil?message:''});return;}
  if(game==='marty'){drawMarty(g,{art,time:t,state:s,notes,hits:hitCount,reduced,message:t<messageUntil?message:'',itemX,offerKind});return;}
  drawArcadeScene(g,{game,art,time:t,state:s,notes,hits:hitCount,reduced,message:t<messageUntil?message:'',drag,focus,itemX,waveY,targetPoint,platformX,launchPlane});
 }
 return {step,draw,point,key,snapshot:()=>({time:t,combo,hits:hitCount,...s,notes}),meta:()=>game==='ryan-ellis'?{dodged:s.ryanDodged,bumps:s.ryanBumps,hazards:s.ryanHazards.length}:{delivered:s.delivered}};
}
