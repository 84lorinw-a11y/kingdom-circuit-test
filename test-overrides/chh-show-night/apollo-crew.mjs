// Owner-approved artwork, preserved without regenerating faces or outfits.
export const apolloCrew=[
 {id:'marty',name:'Marty',file:'apollo-marty-v1',stageX:515,stageY:382,vipX:508,vipY:390},
 {id:'brenno',name:'Brenno',file:'apollo-brenno-v1',stageX:410,stageY:367,vipX:456,vipY:390},
 {id:'ryan-ellis',name:'Ryan Ellis',file:'apollo-ryan-ellis-v1',stageX:650,stageY:367,vipX:612,vipY:390},
 {id:'gavin-the-hotrod',name:'Gavin the HotRod',file:'apollo-gavin-the-hotrod-v1',stageX:250,stageY:367,vipX:352,vipY:390},
 {id:'lj-the-messenger',name:'LJ the Messenger',file:'apollo-lj-the-messenger-v1',stageX:725,stageY:367,vipX:664,vipY:390},
 {id:'dearis',name:'De’aris',file:'apollo-dearis-v1',stageX:800,stageY:367,vipX:716,vipY:390},
 {id:'tonyxtrotter',name:'tonyxtrotter',file:'apollo-tonyxtrotter-v1',stageX:330,stageY:367,vipX:404,vipY:390},
 {id:'eli-williams',name:'Eli Williams',file:'apollo-eli-williams-v1',stageX:570,stageY:345,vipX:560,vipY:390},
 {id:'andrew-prim',name:'Andrew Prim',file:'apollo-andrew-prim-v1',stageX:925,stageY:473,vipX:300,vipY:390}
];
export const frontCrew=apolloCrew.filter(person=>!['eli-williams','andrew-prim'].includes(person.id));
const dj=apolloCrew.find(person=>person.id==='eli-williams');
export const boothLayout={x:dj.stageX,y:dj.stageY,width:148,height:86};
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
 ctx.save();ctx.globalAlpha=.92;
 ctx.textAlign='center';ctx.fillStyle='#7f3028';ctx.font='bold 11px monospace';ctx.fillText('APOLLO RECORDS  /  NOT 4 SALE',655,95);
 ctx.fillStyle='#2d231e';ctx.font='900 23px "Arial Narrow",sans-serif';ctx.fillText('MARTY   /   BRENNO   /   RYAN ELLIS',655,122,500);
 ctx.font='900 18px "Arial Narrow",sans-serif';ctx.fillText('GAVIN THE HOTROD  /  LJ THE MESSENGER  /  DE’ARIS',655,149,500);
 ctx.fillText('TONYXTROTTER  /  ELI WILLIAMS  /  ANDREW PRIM',655,176,500);ctx.restore();
}
const mingleSpots=[[470,421],[298,359],[593,538],[305,532],[681,448],[735,593],[453,588],[601,338],[211,445]];
export function vipArtists(time=0,reduced=false,photo=false){
 if(photo)return vipCrew.map(p=>({...p}));
 return apolloCrew.map((p,i)=>{const [x,y]=mingleSpots[i];return {who:p.id,x:x+(reduced?0:Math.sin(time/9000+i)*9),y:y+(reduced?0:Math.sin(time/11000+i)*5),scale:2.3,artist:true,lean:reduced?0:Math.sin(time/1800+i)*.012};});
}
