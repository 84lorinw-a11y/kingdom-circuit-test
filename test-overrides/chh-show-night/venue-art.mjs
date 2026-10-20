import {drawStageScreen} from './stage-screen.mjs?v=apollo-19';
// Owner-supplied artwork, composited into the venue.
function contain(ctx,image,x,y,w,h){
 if(!image)return;const fit=Math.min(w/image.width,h/image.height);
 ctx.drawImage(image,x+(w-image.width*fit)/2,y+(h-image.height*fit)/2,image.width*fit,image.height*fit);
}
export function drawRoomArtwork(ctx,room,images,time=0,reduced=false,stageFrame=null){
 ctx.save();ctx.textAlign='center';
 if(room==='show'){
  drawStageScreen(ctx,stageFrame);
  // The supplied two-line mark keeps its proportions on a small rigged fabric banner.
  const fabric=ctx.createLinearGradient(426,0,674,0);
  fabric.addColorStop(0,'#131416');fabric.addColorStop(.28,'#242527');fabric.addColorStop(.55,'#101113');fabric.addColorStop(.84,'#202123');fabric.addColorStop(1,'#121315');
  ctx.fillStyle=fabric;ctx.fillRect(426,17,248,87);
  ctx.strokeStyle='#454446';ctx.lineWidth=.6;ctx.strokeRect(428,19,244,83);
  for(const x of [432,668]){
   ctx.strokeStyle='#9b9993';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,8);ctx.lineTo(x,23);ctx.stroke();
   ctx.beginPath();ctx.arc(x,23,1.7,0,Math.PI*2);ctx.stroke();
  }
  contain(ctx,images.eliBanner,440,24,220,75);
 }else if(room==='vip'){
  contain(ctx,images.apolloPoster,375,54,91,116);
  ctx.fillStyle='#eee8de';ctx.font='900 27px sans-serif';
  ctx.fillText('APOLLO',558,99);ctx.fillText('RECORDS',558,130);
  ctx.fillStyle='#d77770';ctx.font='bold 11px sans-serif';ctx.fillText('NOT 4 SALE · VIP',558,153);
 }else if(room==='outside'){
  for(const [x,art] of [[202,images.eliNot4Sale],[425,images.eliCollage]]){
   ctx.fillStyle='#111214';ctx.fillRect(x,234,89,154);
   contain(ctx,art,x+5,245,79,132);
   const glass=ctx.createLinearGradient(x,234,x+89,388);glass.addColorStop(0,'#e3cba314');glass.addColorStop(.45,'#ffffff00');glass.addColorStop(1,'#00000016');
   ctx.fillStyle=glass;ctx.fillRect(x,234,89,154);
  }
  contain(ctx,images.apolloPoster,313,233,94,157);
 }
 const logo={show:[925,174],outside:[929,220],vip:[900,63]}[room];
 if(logo&&images.venueLogo)ctx.drawImage(images.venueLogo,...logo,64,64);
 ctx.restore();
}
