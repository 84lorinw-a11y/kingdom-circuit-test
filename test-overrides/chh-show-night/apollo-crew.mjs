// Owner-approved artwork, preserved without regenerating faces or outfits.
export const apolloCrew=[
 {id:'marty',name:'Marty',file:'apollo-marty-v1',stageX:570,stageY:368,vipX:550,vipY:550},
 {id:'brenno',name:'Brenno',file:'apollo-brenno-v1',stageX:420,stageY:350,vipX:245,vipY:430},
 {id:'ryan-ellis',name:'Ryan Ellis',file:'apollo-ryan-ellis-v1',stageX:650,stageY:350,vipX:510,vipY:310},
 {id:'gavin-the-hotrod',name:'Gavin the HotRod',file:'apollo-gavin-the-hotrod-v1',stageX:270,stageY:350,vipX:300,vipY:310},
 {id:'lj-the-messenger',name:'LJ the Messenger',file:'apollo-lj-the-messenger-v1',stageX:725,stageY:350,vipX:445,vipY:425},
 {id:'dearis',name:'De’aris',file:'apollo-dearis-v1',stageX:800,stageY:350,vipX:660,vipY:430},
 {id:'tonyxtrotter',name:'tonyxtrotter',file:'apollo-tonyxtrotter-v1',stageX:495,stageY:350,vipX:345,vipY:550},
 {id:'eli-williams',name:'Eli Williams (DJ)',file:'apollo-eli-williams-v1',stageX:850,stageY:300,vipX:720,vipY:310},
 {id:'andrew-prim',name:'Andrew Prim',file:'apollo-andrew-prim-v1',stageX:345,stageY:350,vipX:755,vipY:550}
];
export const frontCrew=apolloCrew.filter(person=>person.id!=='eli-williams');
export const boothLayout={x:850,y:300,width:140,height:70};
// Each artist has a separate, reachable lounge area for a future game entrance.
// Keep these positions in the roster so room art and future interactions agree.
export const vipCrew=apolloCrew.map(p=>({x:p.vipX,y:p.vipY,who:p.id,scale:p.id==='marty'?2.45:2.3,artist:true}));
export function photoLineup(avatar='player'){
 const back=['gavin-the-hotrod','ryan-ellis','eli-williams','lj-the-messenger','dearis','tonyxtrotter'];
 const front=['andrew-prim','brenno','marty',avatar,'jay','grace'];
 return [...back.map((who,i)=>({who,x:310+i*180,y:600,scale:4.3})),...front.map((who,i)=>({who,x:260+i*200,y:920,scale:4.6}))];
}
export function drawApolloStage(ctx,time,reduced,drawPerson){
 for(const person of [...frontCrew].sort((a,b)=>a.stageY-b.stageY))drawPerson(ctx,person.stageX,person.stageY,person.id,{scale:person.id==='marty'?2.55:2.35,lean:reduced?0:Math.sin(time/1300+person.stageX)*.008});
}
export function drawApolloMarquee(ctx){
 // Text stays sharp and correctly spelled at every device resolution.
 ctx.save();ctx.textAlign='center';ctx.fillStyle='#181920';
 ctx.font='900 25px sans-serif';ctx.fillText('APOLLO RECORDS',654,108,450);
 ctx.font='bold 11.7px sans-serif';
 ctx.fillText('MARTY  ·  BRENNO  ·  RYAN ELLIS',654,133,465);
 ctx.fillText('GAVIN THE HOTROD  ·  LJ THE MESSENGER  ·  DE’ARIS',654,151,465);
 ctx.fillText('TONYXTROTTER  ·  ELI WILLIAMS (DJ)  ·  ANDREW PRIM',654,169,465);
 ctx.restore();
}
