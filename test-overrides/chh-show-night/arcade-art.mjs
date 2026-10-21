import {loadImage} from './asset-loader.mjs?v=apollo-25';
export const gameArtwork={eli:'eli',brenno:'soundstage','ryan-ellis':'soundstage','lj-the-messenger':'alley',tonyxtrotter:'alley',dearis:'studio','andrew-prim':'studio',apollo:'studio'};
const jobs=new WeakMap();
// Only the selected setting downloads; games sharing a setting share its decode.
export function loadArcadeArt(game,art,{load=loadImage}={}){
 const setting=gameArtwork[game];if(!setting||art['arcade_'+setting])return Promise.resolve();
 if(!jobs.has(art))jobs.set(art,new Map());const pending=jobs.get(art);
 if(!pending.has(setting)){
  const job=load(new URL(`./assets/arcade-${setting}-v1.webp`,import.meta.url).href).then(img=>{art['arcade_'+setting]=img;});
  pending.set(setting,job);job.catch(()=>pending.delete(setting));
 }
 return pending.get(setting);
}
