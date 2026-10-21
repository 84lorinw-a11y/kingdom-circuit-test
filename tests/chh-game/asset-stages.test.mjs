import test from 'node:test';
import assert from 'node:assert/strict';
import {existsSync} from 'node:fs';
import {createStagedAssets,venueAssetGroups,venueImageFiles} from '../../test-overrides/chh-show-night/asset-stages.mjs';
import {avatars} from '../../test-overrides/chh-show-night/avatars.mjs';
import {crowdActors} from '../../test-overrides/chh-show-night/crowds.mjs';
import {apolloCrew} from '../../test-overrides/chh-show-night/apollo-crew.mjs';

test('Character selection requests only the two current player atlases',async()=>{
 const images={},people=[],files=[];
 const assets=createStagedAssets({images,loadImage:async src=>{files.push(src);return {};},loadPeople:async({names})=>people.push(...names)});
 assert.equal(assets.ready('players'),false);await assets.load('players');
 assert.deepEqual(people,['playersA','playersB']);assert.deepEqual(files,[]);
 assert.equal(assets.ready('players'),true);for(const group of ['outside','show','vip'])assert.equal(assets.ready(group),false);
 await assets.load('outside');
 assert.ok(!people.some(p=>apolloCrew.some(a=>a.id===p)));assert.ok(!files.some(p=>p.includes('show-entry')||p.includes('vip-entry')));
});

test('Concurrent room requests share downloads and decoded background aliases',async()=>{
 const images={},counts=new Map();
 const record=async key=>{counts.set(key,(counts.get(key)||0)+1);await Promise.resolve();return {key};};
 const assets=createStagedAssets({images,loadImage:record,loadPeople:async({names})=>Promise.all(names.map(record))});
 await Promise.all([assets.load('show'),assets.load('vip'),assets.load('artists')]);
 assert.ok([...counts.values()].every(count=>count===1));assert.ok(images.show);assert.ok(![...counts.keys()].some(k=>/outdoor-merch|show-entry|outside-entry/.test(k)),'retired scene aliases do not download');
 assert.equal(assets.ready('show'),true);assert.equal(assets.ready('vip'),true);assert.equal(assets.ready('outside'),false);
});

test('An incomplete room stays unready and retry fetches only failed artwork',async()=>{
 const images={},requests=[],people=[];let fail=true,release;
 const blocked=new Promise(resolve=>{release=resolve;});
 const assets=createStagedAssets({images,groups:{room:{people:['artist'],images:['one','two']}},files:{one:'one.webp',two:'two.webp'},loadPeople:async({names})=>{people.push(...names);await blocked;},loadImage:async src=>{requests.push(src);if(fail&&src.endsWith('two.webp'))throw Error('offline');return {src};}});
 await assert.rejects(assets.load('room'),/offline/);assert.equal(assets.ready('room'),false);
 fail=false;const retry=assets.load('room');assert.equal(assets.ready('room'),false);release();await retry;
 assert.equal(assets.ready('room'),true);assert.deepEqual(people,['artist']);
 assert.equal(requests.filter(p=>p.endsWith('one.webp')).length,1);assert.equal(requests.filter(p=>p.endsWith('two.webp')).length,2);
});

test('Each room alone loads every visible person, follower, camera and photo pose',async()=>{
 const previousImage=globalThis.Image,previousDocument=globalThis.document;
 globalThis.Image=class {width=80;height=80;set src(value){this.file=value;}async decode(){assert.ok(existsSync(new URL('../../test-overrides/chh-show-night/'+this.file.replace('/play/',''),import.meta.url)),this.file);}};
 const pixels=new Uint8ClampedArray(80*80*4).fill(255);
 globalThis.document={createElement(){return {getContext(){return {drawImage(){},getImageData(){return {data:pixels};}};}};}};
 try{
  for(const room of ['players','outside','show','vip']){
   const {loadPeople,drawPerson}=await import(`../../test-overrides/chh-show-night/sprites.mjs?asset-test=${room}`);
   await loadPeople({names:venueAssetGroups[room].people});let draws=0;
   const g=new Proxy({drawImage(){draws++;}},{get(target,key){return target[key]??(()=>{});}});
   const cases=avatars.map(a=>[a.sprite,{}]);
   if(room!=='players'){
    for(const person of crowdActors(room,0,true,{crewDelivered:20}))cases.push([person.who,person]);
    for(const who of ['jay','grace'])for(const pose of [{},{back:true},{walking:true}])cases.push([who,pose]);
   }
   if(['show','vip'].includes(room))for(const person of apolloCrew)cases.push([person.id,{}]);
   if(room==='show')for(const who of ['pit:0','pit:1'])for(let cameraPose=0;cameraPose<3;cameraPose++)cases.push([who,{cameraPose}]);
   if(room==='vip')cases.push(['marty-seated',{}]);
   if(room==='vip')for(const who of [...avatars.map(a=>a.sprite),'jay','grace',...apolloCrew.map(a=>a.id)])cases.push([who,{peace:true}]);
   for(const [who,pose]of cases){const before=draws;drawPerson(g,100,300,who,pose);assert.equal(draws-before,1,`${room}: ${who} invisible in ${JSON.stringify(pose)}`);}
   for(const key of venueAssetGroups[room].images)assert.ok(existsSync(new URL('../../test-overrides/chh-show-night/assets/'+venueImageFiles[key],import.meta.url)),key);
  }
 }finally{globalThis.Image=previousImage;globalThis.document=previousDocument;}
});
