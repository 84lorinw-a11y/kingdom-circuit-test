import {drawStageScreen} from './stage-screen.mjs?v=apollo-21';
// Owner-supplied artwork, composited into the venue.
function contain(ctx,image,x,y,w,h){
 if(!image)return;const fit=Math.min(w/image.width,h/image.height);
 ctx.drawImage(image,x+(w-image.width*fit)/2,y+(h-image.height*fit)/2,image.width*fit,image.height*fit);
}
export function drawRoomArtwork(ctx,room,images,time=0,reduced=false,stageFrame=null){
 ctx.save();ctx.textAlign='center';
 if(room==='show'){
  drawStageScreen(ctx,stageFrame);
  // Real cloth and hems replace the rigid sign. Keep Eli's supplied logo intact.
  if(images.bannerCloth)ctx.drawImage(images.bannerCloth,406,10,288,96);
  ctx.save();ctx.globalAlpha=.94;
  contain(ctx,images.eliBanner,440,29,220,67);
  ctx.restore();
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
