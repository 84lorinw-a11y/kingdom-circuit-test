// Faster drops and an alternating sweep, while preserving the shared 20 × (40 + 10) scoring.
export const merchCatch={hit:38,clean:16};
export function merchDrop(note,time){
 const speed=245+Math.min(19,note.id)*3.5,remaining=Math.max(0,note.at-time);
 // Drift settles before the catch line, so the landing target stays readable.
 const drift=remaining>.3?Math.sin((remaining-.3)*3.2+note.id)*Math.min(22,(remaining-.3)*25):0;
 return {x:Math.max(54,Math.min(366,note.x+drift)),y:475-(note.at-time)*speed,rotation:Math.sin(time*3+note.id)*.08};
}
