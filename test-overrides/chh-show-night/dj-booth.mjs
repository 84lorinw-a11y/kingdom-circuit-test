import {djTrack} from './music-config.mjs';
import {mountRhythm} from './rhythm.mjs';
import {drawPerson} from './sprites.mjs';

export function mountDjBooth(container,options={}){
 const intro=document.createElement('div');intro.className='dj-character';
 const portrait=document.createElement('canvas');portrait.width=180;portrait.height=180;
 portrait.setAttribute('role','img');portrait.setAttribute('aria-label','Eli-inspired DJ with realistic facial features and a slim build, in a white CHRIST LIKE cap, black tee, and silver chain.');
 const g=portrait.getContext('2d');g.imageSmoothingEnabled=false;drawPerson(g,90,375,'dj',{scale:6.2});
 const copy=document.createElement('div');const name=document.createElement('h3');name.textContent=djTrack.artist;
 const greeting=document.createElement('p');greeting.textContent='One button to start. Ten beats to catch.';
 const tag=document.createElement('span');tag.className='dj-game-tag';tag.textContent='B–I–B–L–E · TAP THE BEAT';
 copy.append(tag,name,greeting);intro.append(portrait,copy);container.append(intro);
 const round=document.createElement('section');round.className='rhythm';container.append(round);
 return mountRhythm(round,options);
}
