// Transparent sprite atlases adapted from the supplied CHH scene references.
// Trim bounds are calculated once at load; sprites are composited at runtime.
const heroIds=['player','jay','grace','mc','dj','singer'];
 const atlases={};
// Generated rows have slightly different spacing; cut only through transparent gutters.
const rowCuts={};
export async function loadPeople(){
 await Promise.all([['heroes',6,2,'heroes-v3'],['brand',2,2,'brand-fans-v1'],['photographers',2,1,'pit-photographers-v1'],['eli',1,1,'artist-eli-v2'],['steven',1,1,'artist-steven-v1'],['joz',1,1,'artist-joz-v1'],['crowd-vip',6,6,'crowd-vip-v7'],['fansFront',6,5,'fans-front-v12'],['fansBack',6,5,'fans-back-v12']].map(async([name,cols,rows,file])=>{
  const img=new Image();img.src=`/play/assets/${file}.webp`;
  await img.decode();const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const g=c.getContext('2d',{willReadFrequently:true});g.drawImage(img,0,0);const pixels=g.getImageData(0,0,c.width,c.height).data;
  const cells=[];const cw=img.width/cols,ch=img.height/rows;
  const cuts=[0];for(let row=1;row<rows;row++){let cut=Math.round(row*ch),best=Infinity;for(let y=Math.max(0,Math.round(row*ch-ch*.3));y<Math.min(img.height,Math.round(row*ch+ch*.3));y++){let count=0;for(let x=0;x<img.width;x++)if(pixels[(y*img.width+x)*4+3]>100)count++;if(count<best){best=count;cut=y;}}cuts.push(cut);}cuts.push(img.height);rowCuts[name]=cuts;
  for(let row=0;row<rows;row++)for(let col=0;col<cols;col++){
   const top=rowCuts[name]?.[row]??Math.round(row*ch),bottom=rowCuts[name]?.[row+1]??Math.round((row+1)*ch),left=Math.round(col*cw),right=Math.round((col+1)*cw);
   let minX=right,minY=bottom,maxX=left,maxY=top;
   for(let y=top;y<bottom;y++)for(let x=left;x<right;x++)if(pixels[(y*img.width+x)*4+3]>100){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
   cells.push({x:minX,y:minY,w:maxX-minX+1,h:maxY-minY+1});
  }
  atlases[name]={img,cells};
 }));
}
export function drawPerson(ctx,x,y,who='player',{scale=2.25,frame=0,walking=false,back=false,hands=false,alpha=1,flip=false,lean=0}={}){
 const branded=typeof who==='string'&&who.startsWith('brand:')?Number(who.split(':')[1]):null;
 const photographer=typeof who==='string'&&who.startsWith('pit:')?Number(who.split(':')[1]):null;
 const roomFan=typeof who==='string'&&who.startsWith('crowd-')?who.split(':'):null;
 const sharedFan=typeof who==='string'&&who.startsWith('fan:')?Number(who.split(':')[1]):null;
 const isFan=typeof who==='number',solo=who==='dj'?'eli':who==='mc'?'steven':who==='singer'?'joz':null;const atlas=atlases[sharedFan!==null?(back||hands?'fansBack':'fansFront'):branded!==null?'brand':photographer!==null?'photographers':roomFan?.[0]||solo||(isFan?'heroes':'heroes')];if(!atlas)return;
 const index=sharedFan!==null?sharedFan:branded!==null?branded:photographer!==null?photographer:roomFan?Number(roomFan[1]):isFan?([0,3,5,1,5,4][who%6]):(who==='blonde-fan'?2:heroIds.indexOf(who));const src=atlas.cells[solo?0:Math.max(0,index)+(sharedFan===null&&!roomFan&&(back||hands)?branded!==null?2:6:0)];if(!src||src.w<1||src.h<1)return;
 const height=scale*57*(sharedFan!==null&&(back||hands)?1.1:1),width=height*src.w/src.h,bob=walking?Math.abs(Math.sin(frame))*3.5:0;
 ctx.save();ctx.globalAlpha=alpha;ctx.fillStyle='#0710194d';ctx.beginPath();ctx.ellipse(x,y,width*.44,height*.043,0,0,Math.PI*2);ctx.fill();
 ctx.translate(Math.round(x),Math.round(y-bob));if(flip)ctx.scale(-1,1);ctx.rotate(lean+(walking?Math.sin(frame)*.022:0));
 // Small alternating foot offsets and body bob give a readable walking cycle.
 if(walking&&!hands&&!back){const split=src.h*.75,upperH=height*.75,legH=height*.25,half=src.w/2;ctx.drawImage(atlas.img,src.x,src.y,src.w,split,-width/2,-height,width,upperH);for(let leg=0;leg<2;leg++){const lift=Math.max(0,Math.sin(frame+(leg?Math.PI:0)))*4;ctx.drawImage(atlas.img,src.x+half*leg,src.y+split,half,src.h-split,-width/2+width/2*leg,-legH-lift,width/2,legH);}}
 else ctx.drawImage(atlas.img,src.x,src.y,src.w,src.h,-width/2,-height,width,height);
 ctx.restore();
}
