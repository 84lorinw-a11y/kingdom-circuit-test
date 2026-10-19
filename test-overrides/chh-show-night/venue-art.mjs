// Real owner-supplied artwork, composited as flat prints. No generated logos.
function contain(ctx,image,x,y,w,h){
 if(!image)return;const fit=Math.min(w/image.width,h/image.height);
 ctx.drawImage(image,x+(w-image.width*fit)/2,y+(h-image.height*fit)/2,image.width*fit,image.height*fit);
}
export function drawRoomArtwork(ctx,room,images){
 ctx.save();ctx.textAlign='center';
 if(room==='show'){
  contain(ctx,images.apolloPoster,315,82,158,200);
  ctx.fillStyle='#eee8de';ctx.font='900 44px sans-serif';
  ctx.fillText('APOLLO',630,154);ctx.fillText('RECORDS',630,199);
  ctx.fillStyle='#d24b48';ctx.font='bold 16px sans-serif';ctx.fillText('NOT 4 SALE',630,236);
 }else if(room==='vip'){
  contain(ctx,images.apolloPoster,375,54,91,116);
  ctx.fillStyle='#eee8de';ctx.font='900 27px sans-serif';
  ctx.fillText('APOLLO',558,99);ctx.fillText('RECORDS',558,130);
  ctx.fillStyle='#d77770';ctx.font='bold 11px sans-serif';ctx.fillText('NOT 4 SALE · VIP',558,153);
 }else if(room==='outside'){
  contain(ctx,images.apolloBadge,202,237,90,94);
  ctx.fillStyle='#f0e5cf';ctx.font='900 12px sans-serif';
  ctx.fillText('APOLLO',247,350);ctx.fillText('RECORDS',247,365);
  ctx.font='bold 8px sans-serif';ctx.fillText('NOT 4 SALE',247,380);
  contain(ctx,images.apolloPoster,313,233,94,157);
  ctx.fillStyle='#eee5d4';ctx.fillRect(425,234,89,154);
  ctx.fillStyle='#1c1b1b';ctx.font='900 29px sans-serif';
  ctx.fillText('NOT',469,273);ctx.fillText('4',469,307);ctx.fillText('SALE',469,341);
  ctx.fillStyle='#b52e2b';ctx.font='bold 8px sans-serif';ctx.fillText('APOLLO RECORDS',469,374);
 }
 const logo={show:[925,174],outside:[929,220],vip:[900,63]}[room];
 if(logo&&images.venueLogo)ctx.drawImage(images.venueLogo,...logo,64,64);
 ctx.restore();
}
