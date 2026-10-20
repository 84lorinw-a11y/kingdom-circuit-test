// The screen rests just above the rear stage floor; performers draw in front.
export const stageScreen={x:323,y:110,width:454,height:200};
export function screenPlacement({width,height,camera=0,viewWidth=1024}){
 const sx=width/viewWidth,sy=height/683;
 return {left:(stageScreen.x-camera)*sx,top:stageScreen.y*sy,width:stageScreen.width*sx,height:stageScreen.height*sy};
}
export function drawStageScreen(ctx,frame=null){
 const {x,y,width,height}=stageScreen;
 ctx.save();ctx.textAlign='center';ctx.fillStyle='#ede6da';ctx.font='900 30px "Arial Narrow",sans-serif';
 ctx.fillText('APOLLO RECORDS',x+width/2,y-8);
 ctx.fillStyle='#090a0b';ctx.fillRect(x-6,y-4,width+12,height+8);
 ctx.strokeStyle='#434449';ctx.lineWidth=2;ctx.strokeRect(x-5,y-3,width+10,height+6);
 const fw=frame?.videoWidth||frame?.naturalWidth,fh=frame?.videoHeight||frame?.naturalHeight;
 if(fw&&fh){
  const fit=Math.max(width/fw,height/fh),sw=width/fit,sh=height/fit;
  ctx.drawImage(frame,(fw-sw)/2,(fh-sh)*.32,sw,sh,x,y,width,height);
 }else{
  ctx.fillStyle='#ede6da';ctx.font='bold 16px sans-serif';ctx.fillText('APOLLO FILMS',x+width/2,y+90);
  ctx.fillStyle='#a5a6aa';ctx.font='12px sans-serif';ctx.fillText('NOT 4 SALE',x+width/2,y+113);
 }
 ctx.restore();
}
