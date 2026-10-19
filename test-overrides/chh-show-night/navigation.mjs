// Keep the venue's stage and merch display above one clear audience-floor edge.
// Sidewalk crowds and lounge furniture remain decorative and never obstruct routes.
export const roomBounds={left:32,right:992,top:170,bottom:644};
const floorTop=room=>room==='show'?444:room==='outside'?435:roomBounds.top;
export function clampPosition({x,y},room){
 return {x:Math.max(roomBounds.left,Math.min(roomBounds.right,Number.isFinite(x)?x:512)),y:Math.max(floorTop(room),Math.min(roomBounds.bottom,Number.isFinite(y)?y:570))};
}
export function walkable(room,x,y){
 return Number.isFinite(x)&&Number.isFinite(y)&&x>=roomBounds.left&&x<=roomBounds.right&&y>=floorTop(room)&&y<=roomBounds.bottom;
}
export function findPath(room,start,end){
 // Taps above the stage/table lead to the floor in front, without a pathfinding loop.
 return [clampPosition(end,room)];
}
// Never overshoot a destination or reject the final step against a room edge.
export function stepToward(room,start,end,distance){
 const target=clampPosition(end,room),from=clampPosition(start,room),d=Math.hypot(target.x-from.x,target.y-from.y);
 const ratio=d?Math.min(1,Math.max(0,distance)/d):1;
 return {x:from.x+(target.x-from.x)*ratio,y:from.y+(target.y-from.y)*ratio,arrived:ratio===1};
}
