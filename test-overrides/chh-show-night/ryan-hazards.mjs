import {panel,label,glow} from './arcade-drawing.mjs?v=apollo-25';

export const RYAN_HAZARD_WINDOW=.22,RYAN_HAZARD_RADIUS=44;
export const ryanHazardX=(hazard,time)=>100+(hazard.at-time)*130;
export function ryanHazards(notes,seed,waveY){
 let random=seed>>>0;
 // Two warm-up notes, then one speaker between alternate pairs. Leave the
 // original twenty note times intact and keep every route avoidable.
 return notes.slice(1,-1).filter((_,i)=>i%2===0).map((n,id)=>{
  random=(Math.imul(random,1664525)+1013904223)>>>0;
  const at=(n.at+notes[n.id+1].at)/2;
  return {id,at,y:waveY(at)+(random/4294967296-.5)*16,done:false,hit:false};
 });
}
export function touchesRyanHazard(h,from,to,y0,y1){
 if(to<from)return false;
 const begin=Math.max(from,h.at-RYAN_HAZARD_WINDOW),end=Math.min(to,h.at+RYAN_HAZARD_WINDOW);
 if(begin>end)return false;
 const yAt=t=>to===from?y1:y0+(y1-y0)*(t-from)/(to-from),a=yAt(begin),b=yAt(end);
 return h.y>=Math.min(a,b)-RYAN_HAZARD_RADIUS&&h.y<=Math.max(a,b)+RYAN_HAZARD_RADIUS;
}
export function drawRyanHazard(g,h,time,reduced){
 const age=time-(h.resolvedAt??time),x=ryanHazardX(h,time);
 if(x<-45||x>460||(h.done&&(!h.hit||age>.45)))return;
 g.save();g.translate(x,h.y);if(h.hit)g.globalAlpha=Math.max(0,1-age/.45);
 glow(g,0,0,40,'#ee645357');
 if(!reduced){g.strokeStyle='#ed7b6c77';g.lineWidth=1.5;g.beginPath();g.arc(0,0,30+Math.sin(time*5+h.id)*2,0,Math.PI*2);g.stroke();}
 panel(g,-23,-28,46,56,5,'#261d27','#ff9282');
 panel(g,-18,-23,36,46,3,'#101d27','#735363');
 for(const y of [-12,12]){g.fillStyle='#573b46';g.beginPath();g.arc(0,y,y<0?6:12,0,7);g.fill();g.strokeStyle='#b76962';g.lineWidth=1;g.stroke();}
 // The white X and square speaker silhouette distinguish danger without
 // relying on color alone; gold pickups retain their musical-note shape.
 g.strokeStyle='#fff0df';g.lineWidth=3.5;g.lineCap='round';g.beginPath();g.moveTo(-9,-9);g.lineTo(9,9);g.moveTo(9,-9);g.lineTo(-9,9);g.stroke();
 label(g,'AVOID',0,-38,9,'#ffb09f');g.restore();
}
