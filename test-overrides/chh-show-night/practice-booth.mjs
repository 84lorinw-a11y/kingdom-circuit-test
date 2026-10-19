import {drawPerson} from './sprites.mjs?v=apollo-02';
import {boothLayout} from './apollo-crew.mjs?v=apollo-02';
export const practiceSpot={x:boothLayout.x,y:475};
export function drawPracticeBooth(ctx,time=0,booth){
 const {x,y,width,height}=boothLayout;
 drawPerson(ctx,x,y,'eli-williams',{scale:2.1});
 // Detailed decks, mixer, road case and stage lights share the venue's perspective.
 if(booth)ctx.drawImage(booth,x-width/2,y-height+8,width,height);
}
