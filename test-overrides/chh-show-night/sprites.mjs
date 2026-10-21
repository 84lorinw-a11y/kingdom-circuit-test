import {loadImage} from './asset-loader.mjs?v=apollo-22';
import {clubFanPoses,actualFanPoses} from './crowds.mjs?v=apollo-22';
import {apolloCrew} from './apollo-crew.mjs?v=apollo-22';
import {playerSpritePose} from './avatars.mjs?v=apollo-22';
// Transparent sprite atlases adapted from the supplied CHH scene references.
// Trim bounds are calculated once at load; sprites are composited at runtime.
const heroIds=['player','jay','grace'];
const peaceIds={player:0,'crowd-vip:32':1,'crowd-vip:34':2,1:3,5:4,4:5,grace:6};
 const atlases={};
// Generated rows have slightly different spacing; cut only through transparent gutters.
const rowCuts={};
// Only current cast atlases are preloaded. The legacy women/brand IDs resolve to
// actualFans/clubFans above their old fallback branches; saved avatar IDs resolve
// to playersA/playersB. Keep all current poses and original cutout pixels.
const peopleAssets=[['jay',3,1,'jay-apollo-v2'],['peace',5,2,'vip-peace-v18'],['heroes',6,2,'heroes-v3'],['cameraOne',3,1,'camera-operator-one-v1'],['cameraTwo',3,1,'camera-operator-two-v1'],['social',6,5,'fans-social-v1'],['campers',2,1,'campers-v1'],['clubFans',8,4,'club-fans-v1'],['actualFans',4,4,'actual-fans-v1'],['playersA',3,3,'players-a-eli-v1'],['playersB',3,3,'players-b-eli-v1'],...apolloCrew.map(p=>[p.id,1,1,p.file]),['fansFront',6,5,'fans-front-v12'],['fansBack',6,5,'fans-back-v12']];
export const peopleAssetCount=peopleAssets.length;
export async function loadPeople({onProgress=()=>{}}={}){
 await Promise.all(peopleAssets.map(async([name,cols,rows,file,extension='webp'])=>{
  const img=await loadImage(`/play/assets/${file}.${extension}`);const c=document.createElement('canvas');c.width=img.width;c.height=img.height;const g=c.getContext('2d',{willReadFrequently:true});g.drawImage(img,0,0);const pixels=g.getImageData(0,0,c.width,c.height).data;
  const cells=[];const cw=img.width/cols,ch=img.height/rows;
  const cuts=[0];for(let row=1;row<rows;row++){let cut=Math.round(row*ch),best=Infinity;for(let y=Math.max(0,Math.round(row*ch-ch*.3));y<Math.min(img.height,Math.round(row*ch+ch*.3));y++){let count=0;for(let x=0;x<img.width;x++)if(pixels[(y*img.width+x)*4+3]>100)count++;if(count<best){best=count;cut=y;}}cuts.push(cut);}cuts.push(img.height);rowCuts[name]=cuts;
  for(let row=0;row<rows;row++)for(let col=0;col<cols;col++){
   const top=rowCuts[name]?.[row]??Math.round(row*ch),bottom=rowCuts[name]?.[row+1]??Math.round((row+1)*ch),left=Math.round(col*cw),right=Math.round((col+1)*cw);
   let minX=right,minY=bottom,maxX=left,maxY=top;
   for(let y=top;y<bottom;y++)for(let x=left;x<right;x++)if(pixels[(y*img.width+x)*4+3]>100){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
   cells.push({x:minX,y:minY,w:maxX-minX+1,h:maxY-minY+1});
  }
  atlases[name]={img,cells};onProgress();
 }));
}
export function drawPerson(ctx,x,y,who='player',{scale=2.25,frame=0,walking=false,back=false,hands=false,alpha=1,flip=false,lean=0,peace=false,outsidePose,campPose,cameraPose=0}={}){
 const playerPose=playerSpritePose(who,{peace,back,hands});
 const woman=typeof who==='string'&&who.startsWith('women:')?Number(who.split(':')[1]):null;
 const branded=typeof who==='string'&&who.startsWith('brand:')?Number(who.split(':')[1]):null;
 const photographer=typeof who==='string'&&who.startsWith('pit:')?Number(who.split(':')[1]):null;
 const roomFan=typeof who==='string'&&who.startsWith('crowd-')?who.split(':'):null;
 const sharedFan=typeof who==='string'&&who.startsWith('fan:')?Number(who.split(':')[1]):null;
 const isFan=typeof who==='number',solo=apolloCrew.some(p=>p.id===who)?who:null;
 const peaceIndex=peace?peaceIds[who]:undefined,jay=who==='jay',blueSoul=who==='crowd-vip:32';
 const actualIndex=actualFanPoses[who],clubIndex=clubFanPoses[who],isCamp=Number.isInteger(campPose),socialPose=Number.isInteger(outsidePose)&&woman===null;
 const atlas=atlases[playerPose?playerPose.atlas:isCamp?'campers':actualIndex!==undefined?'actualFans':clubIndex!==undefined?'clubFans':photographer!==null?(photographer===0?'cameraOne':'cameraTwo'):socialPose?'social':blueSoul?'blueSoul':jay?'jay':peaceIndex!==undefined?'peace':woman!==null?'women':sharedFan!==null?(back||hands?'fansBack':'fansFront'):branded!==null?'brand':roomFan?.[0]||solo||'heroes'];if(!atlas)return;
 const index=woman!==null?woman:sharedFan!==null?sharedFan:branded!==null?branded:photographer!==null?photographer:roomFan?Number(roomFan[1]):isFan?([0,3,5,1,5,4][who%6]):(who==='blonde-fan'?2:heroIds.indexOf(who));
 const cell=playerPose?playerPose.cell:isCamp?campPose:actualIndex!==undefined?actualIndex+(back||hands?8:0):clubIndex!==undefined?clubIndex+(back||hands?16:0):photographer!==null?Math.max(0,Math.min(2,cameraPose)):socialPose?outsidePose:blueSoul?(peace?1:0):jay?(peace?2:back||hands?1:0):peaceIndex!==undefined?peaceIndex:solo?0:Math.max(0,index)+(sharedFan===null&&!roomFan&&(back||hands)?woman!==null||branded!==null?2:6:0);
 const src=atlas.cells[cell];if(!src||src.w<1||src.h<1)return;
 // Raised hands add space above the head; don't shrink the whole body to fit them.
 // Scale both axes together, preserving the approved artwork's proportions.
 const poseHeight=playerPose?playerPose.height:(back||hands)?(sharedFan!==null||woman!==null||jay?1.18:branded!==null?1.08:1):1;
 const height=scale*57*(isCamp?.73:poseHeight),width=height*src.w/src.h,bob=walking?Math.abs(Math.sin(frame))*3.5:0;
 ctx.save();ctx.globalAlpha=alpha;ctx.fillStyle='#0710194d';ctx.beginPath();ctx.ellipse(x,y,width*.44,height*.043,0,0,Math.PI*2);ctx.fill();
 ctx.translate(Math.round(x),Math.round(y-bob));if(flip)ctx.scale(-1,1);ctx.rotate(lean+(walking?Math.sin(frame)*.022:0));
 // Move the complete cutout; slicing the lower quarter made walking legs look cut off.
 ctx.drawImage(atlas.img,src.x,src.y,src.w,src.h,-width/2,-height,width,height);
 ctx.restore();
}
