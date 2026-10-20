// Slow show visuals on a fixed LED wall; no flashing or motion in reduced-motion mode.
export const screenSlides=['cover','not-for-sale','apollo-logo'];
const hold=10000,fade=1600;
export function screenFrame(time=0,reduced=false){
 if(reduced)return {current:0,next:0,mix:0};
 const elapsed=Math.max(0,time),current=Math.floor(elapsed/hold)%screenSlides.length;
 const progress=Math.max(0,(elapsed%hold-(hold-fade))/fade);
 return {current,next:(current+1)%screenSlides.length,mix:progress*progress*(3-2*progress)};
}
function fit(ctx,image,x,y,w,h){
 if(!image)return;
 const scale=Math.min(w/image.width,h/image.height);
 ctx.drawImage(image,x+(w-image.width*scale)/2,y+(h-image.height*scale)/2,image.width*scale,image.height*scale);
}
function slide(ctx,id,images){
 if(id==='cover')fit(ctx,images.albumCover||images.apolloPoster,329,119,442,180);
 if(id==='apollo-logo')fit(ctx,images.apolloGlobe,445,128,210,161);
 if(id==='not-for-sale'){
  ctx.textAlign='center';ctx.fillStyle='#f3eee6';ctx.font='900 56px "Arial Narrow",sans-serif';
  ctx.fillText('NOT 4 SALE',550,229);
 }
}
export function drawStageScreen(ctx,images,time=0,reduced=false){
 ctx.save();
 // Lettering sits directly on the existing dark stage drape above the screen.
 ctx.textAlign='center';ctx.fillStyle='#ede6da';ctx.font='900 36px "Arial Narrow",sans-serif';
 ctx.fillText('APOLLO RECORDS',550,95);
 // Slim metal frame and mounting details, with the display behind the performers.
 ctx.fillStyle='#090a0b';ctx.fillRect(317,108,466,202);
 ctx.strokeStyle='#434449';ctx.lineWidth=2;ctx.strokeRect(318,109,464,200);
 ctx.fillStyle='#25262a';for(const x of [320,780])for(const y of [111,307]){ctx.beginPath();ctx.arc(x,y,1.2,0,Math.PI*2);ctx.fill();}
 ctx.fillStyle='#060708';ctx.fillRect(323,114,454,190);
 ctx.beginPath();ctx.rect(323,114,454,190);ctx.clip();
 const {current,next,mix}=screenFrame(time,reduced);
 ctx.globalAlpha=1-mix;slide(ctx,screenSlides[current],images);
 if(mix){ctx.globalAlpha=mix;slide(ctx,screenSlides[next],images);}
 ctx.globalAlpha=1;
 // Subtle panel seams read as an LED wall, without obscuring the real artwork.
 ctx.strokeStyle='#a8b3c407';ctx.lineWidth=.5;
 for(let x=323;x<777;x+=38){ctx.beginPath();ctx.moveTo(x,114);ctx.lineTo(x,304);ctx.stroke();}
 for(let y=114;y<304;y+=38){ctx.beginPath();ctx.moveTo(323,y);ctx.lineTo(777,y);ctx.stroke();}
 ctx.restore();
}
