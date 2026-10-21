// Wait for a completed tap before activating anything under a finger. A drag
// can start on a person or marker and still means walking, not opening a game.
export function createWorldGesture({onTap,onWalk,threshold=6}){
 let pointer=null;
 const distance=e=>Math.hypot(e.clientX-pointer.x,e.clientY-pointer.y);
 return {
  get active(){return !!pointer;},
  down(e,room){if(pointer)return false;pointer={id:e.pointerId,x:e.clientX,y:e.clientY,room,moved:false};return true;},
  move(e,point,room){
   if(!pointer||e.pointerId!==pointer.id)return;
   if(room!==pointer.room){pointer=null;return;}
   if(distance(e)>=threshold)pointer.moved=true;
   if(pointer.moved)onWalk(point);
  },
  up(e,point,room){
   if(!pointer||e.pointerId!==pointer.id)return;
   const sameRoom=room===pointer.room,tap=!pointer.moved&&distance(e)<threshold;
   pointer=null;
   if(sameRoom){if(tap)onTap(point);else onWalk(point);}
  },
  cancel(){pointer=null;}
 };
}
