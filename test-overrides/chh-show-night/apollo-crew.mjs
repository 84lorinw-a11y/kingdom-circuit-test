// Owner-approved artwork, preserved without regenerating faces or outfits.
export const apolloCrew=[
 {id:'marty',name:'Marty',file:'apollo-marty-v1',stageX:724},
 {id:'brenno',name:'Brenno',file:'apollo-brenno-v1',stageX:367},
 {id:'ryan-ellis',name:'Ryan Ellis',file:'apollo-ryan-ellis-v1',stageX:590},
 {id:'gavin-the-hotrod',name:'Gavin the HotRod',file:'apollo-gavin-the-hotrod-v1',stageX:300},
 {id:'lj-the-messenger',name:'LJ the Messenger',file:'apollo-lj-the-messenger-v1',stageX:657},
 {id:'dearis',name:'De’aris',file:'apollo-dearis-v1',stageX:791},
 {id:'tonyxtrotter',name:'tonyxtrotter',file:'apollo-tonyxtrotter-v1',stageX:501},
 {id:'eli-williams',name:'Eli Williams (DJ)',file:'apollo-eli-williams-v1',stageX:546},
 {id:'andrew-prim',name:'Andrew Prim',file:'apollo-andrew-prim-v1',stageX:434}
];
export const frontCrew=apolloCrew.filter(person=>person.id!=='eli-williams');
export const boothLayout={x:546,y:339,width:164,height:82};
export function drawApolloStage(ctx,time,reduced,drawPerson){
 for(const person of frontCrew)drawPerson(ctx,person.stageX,369,person.id,{scale:2.35,lean:reduced?0:Math.sin(time/1300+person.stageX)*.008});
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
