// Owner-approved artwork, preserved without regenerating faces or outfits.
export const apolloCrew=[
 {id:'marty',name:'Marty',file:'apollo-marty-v1',stageX:550,stageY:368,vipX:508,vipY:390},
 {id:'brenno',name:'Brenno',file:'apollo-brenno-v1',stageX:420,stageY:350,vipX:456,vipY:390},
 {id:'ryan-ellis',name:'Ryan Ellis',file:'apollo-ryan-ellis-v1',stageX:650,stageY:350,vipX:612,vipY:390},
 {id:'gavin-the-hotrod',name:'Gavin the HotRod',file:'apollo-gavin-the-hotrod-v1',stageX:270,stageY:350,vipX:352,vipY:390},
 {id:'lj-the-messenger',name:'LJ the Messenger',file:'apollo-lj-the-messenger-v1',stageX:725,stageY:350,vipX:664,vipY:390},
 {id:'dearis',name:'De’aris',file:'apollo-dearis-v1',stageX:800,stageY:350,vipX:716,vipY:390},
 {id:'tonyxtrotter',name:'tonyxtrotter',file:'apollo-tonyxtrotter-v1',stageX:345,stageY:350,vipX:404,vipY:390},
 {id:'eli-williams',name:'Eli Williams (DJ)',file:'apollo-eli-williams-v1',stageX:570,stageY:326,vipX:560,vipY:390},
 {id:'andrew-prim',name:'Andrew Prim',role:'Producer / A&R',file:'apollo-andrew-prim-v1',stageX:910,stageY:472,vipX:300,vipY:390}
];
export const frontCrew=apolloCrew.filter(person=>!['eli-williams','andrew-prim'].includes(person.id));
const dj=apolloCrew.find(person=>person.id==='eli-williams');
export const boothLayout={x:dj.stageX,y:dj.stageY,width:140,height:70};
const producer=apolloCrew.find(person=>person.id==='andrew-prim');
export const producerActor={x:producer.stageX,y:producer.stageY,who:producer.id,scale:2.3,artist:true};
// The crew stands shoulder to shoulder for a traditional VIP meet-and-greet.
export const vipCrew=apolloCrew.map(p=>({x:p.vipX,y:p.vipY,who:p.id,scale:p.id==='marty'?2.45:2.3,artist:true}));
export function photoLineup(avatar='player'){
 const line=['andrew-prim','gavin-the-hotrod','tonyxtrotter','ryan-ellis','brenno','marty',avatar,'eli-williams','lj-the-messenger','dearis','jay','grace'];
 return line.map((who,i)=>({who,x:174+i*108,y:675,scale:4.8}));
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
