import {drawPerson} from './sprites.mjs?v=apollo-25';
import {apolloCrew,boothLayout} from './apollo-crew.mjs?v=apollo-25';
// Keep Eli's floor entrance clear of Marty's while the booth sits behind the lead.
export const practiceSpot={x:boothLayout.x,y:449};
export function isBoothTap({x,y}){
 const lead=apolloCrew.find(person=>person.id==='marty');
 if(Math.abs(x-lead.stageX)<30&&y>lead.stageY-145&&y<lead.stageY)return false;
 return Math.abs(x-boothLayout.x)<boothLayout.width/2&&y>boothLayout.y-125&&y<boothLayout.y+8;
}
export function drawPracticeBooth(ctx,time=0,booth){
 const {x,y,width,height}=boothLayout;
 drawPerson(ctx,x,y,'eli-williams',{scale:2.1});
 // Detailed decks, mixer, road case and stage lights share the venue's perspective.
 if(booth)ctx.drawImage(booth,x-width/2,y-height+8,width,height);
}
