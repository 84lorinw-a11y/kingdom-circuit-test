// Both operators work the front pit, keeping feet and shadows above the game circles.
export const pitPhotographers=[
 {x:263,y:444,who:'pit:0',scale:2.2,photographer:0,video:true,flip:false},
 {x:800,y:444,who:'pit:1',scale:2.2,photographer:1,video:true,flip:false}
];
const cameraRoutes=[
 [[263,444],[320,438],[235,442]],
 [[800,444],[748,438],[820,442]]
];
const cycle=60000;
const smooth=t=>t*t*(3-2*t);
// Forty-two seconds filming the stage, six filming fans, twelve moving between angles.
// The second operator is offset so they never both turn to the audience together.
export function cameraActors(time=0,reduceMotion=false){
 const now=Number.isFinite(time)?Math.max(0,time):0;
 return pitPhotographers.map((person,i)=>{
  if(reduceMotion)return {...person,cameraPose:0,shot:'stage',walking:false};
  const t=(now+i*14000)%cycle,route=cameraRoutes[i];
  let from=0,to=0,start=0,walking=false,shot='stage';
  if(t>=56000){from=2;to=0;start=56000;walking=true;}
  else if(t>=44000){from=to=2;}
  else if(t>=40000){from=1;to=2;start=40000;walking=true;}
  else if(t>=34000){from=to=1;shot='crowd';}
  else if(t>=22000){from=to=1;}
  else if(t>=18000){from=0;to=1;start=18000;walking=true;}
  const p=walking?smooth((t-start)/4000):0;
  const [ax,ay]=route[from],[bx,by]=route[to];
  // Walking artwork points right for operator one and left for operator two.
  const flip=walking?(bx>ax)!==(i===0):false;
  return {...person,x:ax+(bx-ax)*p,y:ay+(by-ay)*p,flip,walking,
   walkFrame:now/190,cameraPose:walking?2:shot==='crowd'?1:0,
   shot:walking?'reposition':shot};
 });
}
export function drawCameraFlash(ctx,person,time,reduceMotion){
 if(reduceMotion||person.video)return;
 const phase=(time+person.photographer*1900)%4300;
 if(phase>100)return;
 const x=person.x+(person.photographer?27:-29)*(person.flip?-1:1),y=person.y-119;
 ctx.save();ctx.globalAlpha=(1-phase/100)*.85;ctx.translate(x,y);ctx.fillStyle='#fff0bd';
 ctx.beginPath();ctx.moveTo(0,-8);ctx.lineTo(2,-2);ctx.lineTo(8,0);ctx.lineTo(2,2);ctx.lineTo(0,8);ctx.lineTo(-2,2);ctx.lineTo(-8,0);ctx.lineTo(-2,-2);ctx.closePath();ctx.fill();ctx.restore();
}
