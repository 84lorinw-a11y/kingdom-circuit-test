import {drawPerson} from './sprites.mjs?v=blue-25';
export const practiceSpot={x:512,y:475};
export function drawPracticeBooth(ctx,time=0,booth){
 const x=512,y=363;
 drawPerson(ctx,x,y,'dj',{scale:2.9});
 // Detailed decks, mixer, road case and stage lights share the venue's perspective.
 if(booth)ctx.drawImage(booth,x-111,y-100,222,111);
}
