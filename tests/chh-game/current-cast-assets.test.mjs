import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {loadPeople,drawPerson} from '../../test-overrides/chh-show-night/sprites.mjs';
import {avatars} from '../../test-overrides/chh-show-night/avatars.mjs';
import {sharedCast,crowdActors} from '../../test-overrides/chh-show-night/crowds.mjs';
import {apolloCrew} from '../../test-overrides/chh-show-night/apollo-crew.mjs';

test('Every current person and pose still draws after retired atlases are removed',async()=>{
 const previousImage=globalThis.Image,previousDocument=globalThis.document;
 const requested=[];
 globalThis.Image=class {
  width=80;height=80;
  set src(value){this.file=value;requested.push(value);}
  async decode(){assert.ok(existsSync(new URL('../../test-overrides/chh-show-night/'+this.file.replace('/play/',''),import.meta.url)),`Missing sprite ${this.file}`);}
 };
 const pixels=new Uint8ClampedArray(80*80*4).fill(255);
 globalThis.document={createElement(){return {getContext(){return {drawImage(){},getImageData(){return {data:pixels};}};}};}};
 try{
  await loadPeople();let draws=0;
  const context=new Proxy({drawImage(){draws++;}},{get(target,key){return target[key]??(()=>{});}});
  const cases=[];
  for(const who of [...avatars.map(a=>a.sprite),'player','jay','grace',...apolloCrew.map(a=>a.id),...sharedCast.map(a=>a.who)])
   for(const options of [{},{back:true},{hands:true},{peace:true},{walking:true,flip:true}])cases.push([who,options]);
  for(const room of ['outside','show','vip'])for(const person of crowdActors(room,0,true,{crewDelivered:20}))cases.push([person.who,person]);
  for(const who of ['pit:0','pit:1'])for(let cameraPose=0;cameraPose<3;cameraPose++)cases.push([who,{cameraPose}]);
  for(const [who,options] of cases){const before=draws;drawPerson(context,180,380,who,options);assert.equal(draws-before,1,`${who} is invisible in ${JSON.stringify(options)}`);}
  for(const retired of ['blue-soul-v25','crowd-vip-v7','fan-women-v13','apollo-fans-v1'])assert.ok(!requested.some(src=>src.includes(retired)),`Retired asset still requested: ${retired}`);
 }finally{globalThis.Image=previousImage;globalThis.document=previousDocument;}
});
