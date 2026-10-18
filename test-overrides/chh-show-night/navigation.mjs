// Scenery is decorative. Only the outer room edges constrain movement.
export const roomBounds={left:32,right:992,top:170,bottom:644};
export function clampPosition({x,y}){
 return {x:Math.max(roomBounds.left,Math.min(roomBounds.right,Number.isFinite(x)?x:512)),y:Math.max(roomBounds.top,Math.min(roomBounds.bottom,Number.isFinite(y)?y:570))};
}
export function walkable(room,x,y){
 return Number.isFinite(x)&&Number.isFinite(y)&&x>=roomBounds.left&&x<=roomBounds.right&&y>=roomBounds.top&&y<=roomBounds.bottom;
}
export function findPath(room,start,end){
 // Direct movement cannot get caught in grass, furniture or a pathfinding loop.
 return [clampPosition(end)];
}
