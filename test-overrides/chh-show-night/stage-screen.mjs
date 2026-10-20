// The video surface is a DOM player aligned with this raised, unobstructed screen.
export const stageScreen={x:323,y:25,width:454,height:200};
export function screenPlacement({width,height,camera=0,viewWidth=1024}){
 const sx=width/viewWidth,sy=height/683;
 return {left:(stageScreen.x-camera)*sx,top:stageScreen.y*sy,width:stageScreen.width*sx,height:stageScreen.height*sy};
}
export function drawStageScreen(ctx){
 ctx.save();ctx.textAlign='center';ctx.fillStyle='#ede6da';ctx.font='900 30px "Arial Narrow",sans-serif';
 ctx.fillText('APOLLO RECORDS',550,22);
 const {x,y,width,height}=stageScreen;
 ctx.fillStyle='#090a0b';ctx.fillRect(x-6,y-4,width+12,height+8);
 ctx.strokeStyle='#434449';ctx.lineWidth=2;ctx.strokeRect(x-5,y-3,width+10,height+6);
 ctx.fillStyle='#ede6da';ctx.font='bold 16px sans-serif';ctx.fillText('APOLLO FILMS',550,115);
 ctx.fillStyle='#a5a6aa';ctx.font='12px sans-serif';ctx.fillText('Three films. One crew.',550,138);
 ctx.restore();
}
