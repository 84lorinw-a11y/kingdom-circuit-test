// Turn both camera operators inward toward the artists; feet stay above the listening circles.
export const pitPhotographers=[
 {x:263,y:444,who:'pit:0',scale:2.2,photographer:0,flip:true},
 {x:800,y:444,who:'pit:1',scale:2.2,photographer:1,flip:true}
];
export function drawCameraFlash(ctx,person,time,reduceMotion){
 if(reduceMotion)return;
 const phase=(time+person.photographer*1900)%4300;
 if(phase>100)return;
 const x=person.x+(person.photographer?27:-29)*(person.flip?-1:1),y=person.y-119;
 ctx.save();ctx.globalAlpha=(1-phase/100)*.85;ctx.translate(x,y);ctx.fillStyle='#fff0bd';
 ctx.beginPath();ctx.moveTo(0,-8);ctx.lineTo(2,-2);ctx.lineTo(8,0);ctx.lineTo(2,2);ctx.lineTo(0,8);ctx.lineTo(-2,2);ctx.lineTo(-8,0);ctx.lineTo(-2,-2);ctx.closePath();ctx.fill();ctx.restore();
}
