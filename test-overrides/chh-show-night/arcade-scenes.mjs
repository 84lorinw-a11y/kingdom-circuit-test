import {drawRyanHazard} from './ryan-hazards.mjs?v=apollo-25';
import {drawPerson} from './sprites.mjs?v=apollo-25';
import {brennoFan} from './crowds.mjs?v=apollo-25';
import {drawMerchItem} from './merch-items.mjs?v=apollo-25';
import {background,label,panel,poly,glow,logo,caseBox,pass,musicNote,cassette,recentFeedback} from './arcade-drawing.mjs?v=apollo-25';

function caption(g,value,y=530){panel(g,55,y-19,310,29,5,'#10212de8','#d4ba7955');label(g,value,210,y,11);}
function portrait(g,who,x,y,scale=1.5){glow(g,x,y-35,50,'#efba5333');drawPerson(g,x,y,who,{scale});}
function deskPortrait(g,who,x,bottom,height){
 g.save();g.beginPath();g.rect(x-65,0,130,bottom);g.clip();
 glow(g,x,70,70,'#edbe4c26');drawPerson(g,x,20+height,who,{scale:height/57});g.restore();
}
function ryan(g,{art,time:t,state:s,notes,hits,reduced,waveY}){
 background(g,art,'soundstage');
 // Layered wave trails share the exact center curve used for scoring.
 for(let band=3;band>=0;band--){g.strokeStyle=['#b6faf0','#36c4cc88','#579ed755','#9a7fd033'][band];g.lineWidth=band?2:5;g.shadowColor='#49dbe4';g.shadowBlur=reduced?0:band?5:13;g.beginPath();
  for(let x=0;x<=420;x+=4){const y=waveY(t+(x-100)/130)+band*17;if(!x)g.moveTo(x,y);else g.lineTo(x,y);}g.stroke();}g.shadowBlur=0;
 for(const n of notes){if(n.done)continue;const x=100+(n.at-t)*130;if(x<0||x>440)continue;musicNote(g,x,waveY(n.at),1,'#ffdb8c');}
 for(const hazard of s.ryanHazards)drawRyanHazard(g,hazard,t,reduced);
 for(let i=0;i<Math.floor(hits/2);i++)drawPerson(g,24+i*41,557,brennoFan(i),{scale:1.08});
 const y=s.y+27;glow(g,100,y,50,t<s.ryanBumpUntil?'#ed846b77':'#68e7e955');
 const board=g.createLinearGradient(55,y-5,142,y+7);board.addColorStop(0,'#527c8e');board.addColorStop(.5,'#f1edc5');board.addColorStop(1,'#2d949e');g.fillStyle=board;g.beginPath();g.ellipse(100,y,43,7,-.1,0,7);g.fill();
 g.strokeStyle='#8dfff1';g.lineWidth=2;g.beginPath();g.ellipse(100,y+3,42,6,-.1,0,7);g.stroke();
 drawPerson(g,100,s.y+22,'ryan-ellis',{scale:1.65,lean:reduced?0:Math.sin(t*1.5)*.035});
 panel(g,23,15,374,34,6,'#10212de8','#d4ba7955');
 musicNote(g,47,32,.5,'#ffdb8c');label(g,'COLLECT GOLD',119,37,10,'#ffdb8c');
 panel(g,215,23,18,18,3,'#361f29','#fb8e7a');label(g,'×',224,37,16,'#fff0df');label(g,'DODGE RED X',309,37,10,'#ffac9b');
 caption(g,`${hits} NOTES  ·  ${s.ryanDodged} SPEAKERS DODGED`,490);
 if(s.ryanStatic)label(g,'FEEDBACK · NEXT NOTE LOSES ITS +10 BONUS',210,518,9,'#ffb09f');
}
function lj(g,{art,time:t,state:s,notes,reduced,targetPoint,drag,launchPlane}){
 background(g,art,'alley');
 for(let row=0;row<3;row++){
  const y=165+row*65;panel(g,27,y-49,366,57,3,'#101e26b8','#7f827d55');
  for(let col=1;col<6;col++){g.fillStyle='#8c8c8055';g.fillRect(27+col*61,y-47,2,52);}
  caseBox(g,210,y+10,384,8,'#788c98');
 }
 const n=notes.find(n=>!n.done);if(n){const q=targetPoint(n,t);glow(g,q.x,q.y-20,43,'#edc36b77');drawPerson(g,q.x,q.y+10,brennoFan(n.id),{scale:1.12});
  g.strokeStyle='#efcf83';g.lineWidth=2;g.beginPath();g.arc(q.x,q.y-20,34,0,Math.PI*2);g.stroke();label(g,'INVITE',q.x,q.y-62,9);}
 for(let i=0;i<Math.min(s.delivered,10);i++)drawPerson(g,24+i*41,427,brennoFan(i),{scale:.75});
 const p=s.plane||{x:210,y:502,vx:0,vy:-1};g.strokeStyle='#e5dcc0b0';g.lineWidth=2;g.beginPath();s.planeTrail.forEach((q,i)=>i?g.lineTo(q.x,q.y):g.moveTo(q.x,q.y));g.stroke();
 if(drag&&!s.plane){const launch=launchPlane(drag.start,drag.last);if(launch){g.fillStyle='#e5d7acaa';for(let i=1;i<14;i++){const a=i*.065,x=210+launch.vx*a,y=502+launch.vy*a+85*a*a;if(y<90)break;g.beginPath();g.arc(x,y,2,0,7);g.fill();}}}
 glow(g,p.x,p.y,28,'#efdb9060');g.save();g.translate(p.x,p.y);g.rotate(Math.atan2(p.vy,p.vx)+Math.PI/2);
 poly(g,[[0,-22],[-23,17],[0,9]],'#fff2ce');poly(g,[[0,-22],[0,9],[22,17]],'#a9c1c9');poly(g,[[0,-22],[-5,13],[0,9]],'#e9caa0');g.restore();
 portrait(g,'lj-the-messenger',60,550,1.85);panel(g,131,525,265,26,4,'#11202ce8');label(g,`${s.delivered} INVITES DELIVERED`,264,543,11);
}
function dearis(g,{art,time:t,state:s,focus,reduced}){
 background(g,art,'studio');deskPortrait(g,'dearis',367,131,250);logo(g,art,205,38,96);
 panel(g,21,83,284,45,5,'#15272cdb');label(g,`SESSION ${Math.min(4,s.board+1)} / 4`,163,101,12);label(g,t<s.revealUntil?'REMEMBER THE TAPES':s.board>=4?'ALL FILES RECOVERED':'MATCH THE STUDIO FILES',163,118,9,'#bce6cc');
 if(s.board<4)for(let i=0;i<10;i++){
  const x=20+i%3*128,y=140+Math.floor(i/3)*96,matched=s.matched.includes(i),visible=t<s.revealUntil||s.open.includes(i)||matched;
  g.save();g.shadowColor='#100900aa';g.shadowBlur=6;g.shadowOffsetY=4;panel(g,x,y,114,84,7,matched?'#214b3cdc':'#182b32ef',matched?'#c3dfb4':'#a7a88b');g.shadowBlur=0;g.shadowOffsetY=0;
  panel(g,x+5,y+5,104,74,4,'#00000015','#d0c8a033');
  if(visible){cassette(g,x+57,y+40,s.deck[i],1.04);if(matched){panel(g,x+20,y+60,74,18,3,'#19392fee','#a5d49a');label(g,'RECOVERED',x+57,y+73,8,'#d3ecc0');}}
  else {logo(g,art,x+57,y+35,80);label(g,'SESSION FILE',x+57,y+66,8,'#d0c4aa');}
  if(i===focus){g.strokeStyle='#ffdf96';g.lineWidth=2;g.strokeRect(x+2,y+2,110,80);}g.restore();
 }
 for(let i=0;i<4;i++){const x=184+i%2*107,y=458+Math.floor(i/2)*42;caseBox(g,x,y,94,29,i<s.board?'#aadaab':'#73818a');label(g,i<s.board?'✓ RECOVERED':`SESSION ${i+1}`,x,y+19,8,i<s.board?'#cde6ba':'#93a2a7');}
 if(s.board>=4){glow(g,210,300,145,'#dfc98c50');label(g,'SESSION SAVED',210,291,26);label(g,'EVERY FILE. BACK WHERE IT BELONGS.',210,323,10,'#d1e4cc');}
}
function tony(g,{art,time:t,state:s,notes,hits,reduced,platformX}){
 background(g,art,'alley');
 const altitude=Math.max(0,Math.floor((500-s.jumpY)/10));
 g.strokeStyle='#bdc5bd66';g.lineWidth=1;g.beginPath();g.moveTo(15,127);g.lineTo(15,462);g.stroke();
 for(let y=127;y<463;y+=25){g.beginPath();g.moveTo(12,y);g.lineTo(20,y);g.stroke();}
 s.platforms.forEach((p,i)=>{const y=p.y-s.camera;if(y<85||y>560)return;const x=platformX(p,t);
  g.strokeStyle='#7e979b';g.lineWidth=3;g.beginPath();g.moveTo(x-41,y+21);g.lineTo(x-31,y+33);g.moveTo(x+41,y+21);g.lineTo(x+31,y+33);g.stroke();
  caseBox(g,x,y,110,22,i<=s.lastPlatform?'#cad2aa':'#b3b8b4');
  if(i>0&&i<=20&&!notes[i-1].done)pass(g,x,y-25,.68,t,reduced);
 });
 const feet=s.jumpY-s.camera;glow(g,s.x,feet+1,33,'#edc77944');drawPerson(g,s.x,feet,'tonyxtrotter',{scale:1.65,lean:reduced?0:(s.targetX-s.x)*.001});
 panel(g,76,88,268,28,5,'#112432ec');label(g,`${altitude} m  ·  ${hits} / 20 PASSES`,210,107,12);
}
function releaseItem(g,art,kind,x,y,scale=1){
 g.save();g.translate(x,y);g.scale(scale,scale);g.shadowColor='#0008';g.shadowBlur=5;g.shadowOffsetY=3;
 panel(g,-39,-32,78,64,5,['#24473e','#574433','#34465d'][kind],['#b8d5ac','#ead2a6','#b0cde8'][kind]);g.shadowBlur=0;g.shadowOffsetY=0;
 if(kind===0){musicNote(g,0,-7,.85,'#c7e7bd');label(g,'SONG',0,24,9);}
 else if(kind===1){panel(g,-23,-25,46,36,2,'#101921','#bc9d6e');logo(g,art,0,-7,40);label(g,'COVER',0,24,9);}
 else {pass(g,0,-6,.53,0,true);label(g,'PASS',0,24,9);}
 g.restore();
}
function andrew(g,{art,time:t,state:s,notes,hits,reduced,drag,itemX}){
 background(g,art,'studio');deskPortrait(g,'andrew-prim',357,204,305);logo(g,art,200,36,100);
 panel(g,18,91,264,72,7,'#17292be8','#baad8255');label(g,['Final mix just landed.','Guest list is ready.','Cover art looks good.','Let’s get this released.'][Math.floor(t/5)%4],150,118,13);label(g,'THE CREW NEEDS YOU',150,145,9,'#c8ba98');
 caseBox(g,210,204,432,106);g.save();g.beginPath();g.rect(0,214,420,83);g.clip();
 for(let x=-30;x<450;x+=24){const dx=x+(reduced?0:t*45%24);g.strokeStyle='#75848b45';g.lineWidth=3;g.beginPath();g.moveTo(dx,214);g.lineTo(dx,296);g.stroke();}g.restore();
 for(const n of notes){if(n.done||t<n.at-3||drag?.note===n)continue;releaseItem(g,art,n.id%3,itemX(n,t),250);}
 for(let i=0;i<6;i++){const x=12+i*67;panel(g,x,336,59,48,4,i<s.packages?'#e0cda8':'#17272b80',i<s.packages?'#f1d8a4':'#baa77a55');if(i<s.packages){logo(g,art,x+29,355,45);label(g,'READY',x+29,376,7,'#3c493f');}else label(g,'·',x+29,366,22,'#b0b6a3');}
 label(g,`${s.packages} RELEASE PACKAGES READY`,210,403,11,'#e5cfa7');
 for(let i=0;i<3;i++){
  const x=70+i*140,active=s.sorted.has(i),color=['#afd7ae','#e4c88d','#a9c7e3'][i];
  caseBox(g,x,411,124,110,color);panel(g,x-53,419,106,91,5,['#254038dd','#554432dd','#2f4155dd'][i],color+'70');
  label(g,['SONG FILES','COVER ART','GUEST PASSES'][i],x,440,10,color);releaseItem(g,art,i,x,478,.7);
  if(active){glow(g,x,466,52,color+'44');label(g,'✓',x+44,508,16,'#dcf1bc');}
 }
 if(drag?.note&&s.cursor){const p=s.cursor;releaseItem(g,art,drag.note.id%3,p.x,p.y,1.07);}
}
export function drawArcadeScene(g,args){
 const {game,time,notes,reduced,message}=args;g.save();
 ({'ryan-ellis':ryan,'lj-the-messenger':lj,dearis,tonyxtrotter:tony,'andrew-prim':andrew})[game](g,args);
 if(message){panel(g,54,59,312,26,5,'#0d202be8','#d3ba7e77');label(g,message,210,77,11);}
 recentFeedback(g,notes,time,reduced);g.restore();
}
export function drawMerchScene(g,{art,time,px,notes,reduced,dropFor}){
 g.save();background(g,art,'studio');logo(g,art,210,45,125);
 // Display rail and tote use existing shirt art; no extra product downloads.
 g.strokeStyle='#aeb4ab';g.lineWidth=3;g.beginPath();g.moveTo(35,92);g.lineTo(385,92);g.stroke();
 for(let i=0;i<4;i++){const x=70+i*94;g.strokeStyle='#c7bba1';g.lineWidth=1.5;g.beginPath();g.moveTo(x,92);g.lineTo(x,103);g.stroke();drawMerchItem(g,art,i,x-25,102,50,55);}
 for(const n of notes){if(n.done)continue;const d=dropFor(n,time);if(d.y<140||d.y>520)continue;g.save();g.translate(d.x,d.y-40);g.rotate(reduced?0:d.rotation);glow(g,0,0,49,'#dfc38333');drawMerchItem(g,art,n.kind,-51,-51,102,102);g.restore();}
 glow(g,px,515,65,'#e6c98a40');g.strokeStyle='#dbc49a';g.lineWidth=7;
 for(const x of [-21,21]){g.beginPath();g.ellipse(px+x,475,12,25,0,Math.PI,Math.PI*2);g.stroke();}
 const fabric=g.createLinearGradient(px-43,475,px+43,535);fabric.addColorStop(0,'#cfb58d');fabric.addColorStop(.5,'#f0d6ac');fabric.addColorStop(1,'#a98b64');poly(g,[[px-43,475],[px+43,475],[px+37,540],[px-37,540]],fabric);
 g.setLineDash([2,3]);g.strokeStyle='#8d7759';g.lineWidth=1;g.strokeRect(px-33,482,66,51);g.setLineDash([]);
 panel(g,px-29,493,58,29,2,'#13262b');logo(g,art,px,507,49);
 label(g,'CATCH IN THE MIDDLE',210,184,10,'#ecdbb7');
 const caught=notes.filter(n=>n.done&&!n.rejected).length;panel(g,119,551,182,8,3,'#14272b');g.fillStyle='#d9c085';g.fillRect(120,552,180*caught/20,6);
 recentFeedback(g,notes,time,reduced);g.restore();
}
