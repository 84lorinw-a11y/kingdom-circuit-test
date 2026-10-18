export function walkable(room,x,y){
 if(x<32||x>992||y>644)return false;
 if(room==='outside'){const min=x<397?550:x<615?505:350;return y>=min&&!(x>491&&x<539&&y>421&&y<492)&&!(x>920&&y<505);}
 if(room==='show')return y>=(x<163?437:x>903?420:462);
 return y>=300&&!(x<315&&y>335&&y<619)&&!(x>748&&y<393);
}
// Split the segment at every collision edge, then check each interval.
// This prevents paths from shaving through a corner between sampled points.
const edges={outside:{x:[32,992,397,615,491,539,920],y:[644,550,505,350,421,492]},show:{x:[32,992,163,903],y:[644,437,420,462]},vip:{x:[32,992,315,748],y:[644,300,335,619,393]}};
const clear=(room,a,b)=>{const cuts=[0,1];for(const axis of ['x','y']){const delta=b[axis]-a[axis];if(delta)for(const edge of edges[room][axis]){const t=(edge-a[axis])/delta;if(t>0&&t<1)cuts.push(t);}}cuts.sort((a,b)=>a-b);const check=t=>walkable(room,a.x+(b.x-a.x)*t,a.y+(b.y-a.y)*t);for(let i=0;i<cuts.length;i++){if(!check(cuts[i]))return false;if(i&&!check((cuts[i-1]+cuts[i])/2))return false;}return true;};
export function findPath(room,start,end){
 if(!walkable(room,end.x,end.y))return [];
 if(clear(room,start,end))return [end];
 const step=12,key=(x,y)=>`${x},${y}`;
 const snap=p=>{let best=null;for(let dx=-2;dx<=2;dx++)for(let dy=-2;dy<=2;dy++){const x=Math.round(p.x/step)+dx,y=Math.round(p.y/step)+dy,q={x:x*step,y:y*step};if(walkable(room,q.x,q.y)&&clear(room,p,q)){const d=Math.hypot(q.x-p.x,q.y-p.y);if(!best||d<best.d)best={x,y,d};}}return best;};
 const a=snap(start),b=snap(end);if(!a||!b)return [];
 const open=[{x:a.x,y:a.y,g:0,f:0}],costs=new Map([[key(a.x,a.y),0]]),parents=new Map();let found=false;
 while(open.length){open.sort((a,b)=>b.f-a.f);const p=open.pop();if(p.x===b.x&&p.y===b.y){found=true;break;}if(p.g>costs.get(key(p.x,p.y)))continue;
 for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]){const x=p.x+dx,y=p.y+dy,q={x:x*step,y:y*step};if(!clear(room,{x:p.x*step,y:p.y*step},q))continue;const g=p.g+Math.hypot(dx,dy),k=key(x,y);if(g>=(costs.get(k)??Infinity))continue;costs.set(k,g);parents.set(k,key(p.x,p.y));open.push({x,y,g,f:g+Math.hypot(x-b.x,y-b.y)});}
 }
 if(!found)return [];const points=[end];let k=key(b.x,b.y);while(k){const [x,y]=k.split(',').map(Number);points.unshift({x:x*step,y:y*step});k=parents.get(k);}points.unshift(start);
 const result=[];let index=0;while(index<points.length-1){let next=points.length-1;while(next>index+1&&!clear(room,points[index],points[next]))next--;result.push(points[next]);index=next;}return result;
}
