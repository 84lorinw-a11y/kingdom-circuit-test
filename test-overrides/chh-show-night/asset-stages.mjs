import {apolloCrew} from './apollo-crew.mjs?v=apollo-24';

export const venueImageFiles={venueLogo:'venue-logo-v15.webp',apolloPoster:'apollo-official-not4sale.webp',eliBanner:'eli-apollo-blue-v1.webp',bannerCloth:'stage-banner-cloth-v1.webp',hazer:'stage-hazer-v1.webp',eliNot4Sale:'eli-not4sale-white-v1.webp',eliCollage:'eli-collage-v1.webp',booth:'dj-booth-v13.webp',merch:'merch-apollo-v2.webp',merchEli:'merch-eli-v1.webp',andrewBooth:'andrew-booth-v2.webp',roadies:'roadies-v1.webp',kcLogo:'kingdom-circuit-instagram.webp',martyBg:'show-entry-v1.webp',brennoBg:'outside-entry-v1.webp',apolloBg:'show-entry-v1.webp',outside:'outside-entry-v1.webp',show:'show-entry-v1.webp',vip:'vip-entry-v1.webp'};
const players=['playersA','playersB'],friends=['jay','heroes'],fans=['actualFans','clubFans'],artists=apolloCrew.map(p=>p.id);
export const venueAssetGroups={
 players:{people:players,images:[]},
 outside:{people:[...players,...friends,...fans,'social','campers'],images:['outside','venueLogo','apolloPoster','eliNot4Sale','eliCollage','roadies']},
 show:{people:[...players,...friends,...fans,...artists,'fansFront','fansBack','cameraOne','cameraTwo'],images:['show','venueLogo','apolloPoster','eliBanner','bannerCloth','hazer','booth','andrewBooth','merch','merchEli','apolloBg','martyBg','brennoBg','outside']},
 vip:{people:[...players,...friends,...fans,...artists,'fansFront','peace'],images:['vip','venueLogo','apolloPoster']},
 artists:{people:artists,images:[]},
 merch:{people:[],images:['merch','merchEli']},
 scores:{people:[],images:['kcLogo']},
};

// Cache successful files across rooms. A failed file can retry without fetching
// every completed image again; aliases share both the download and decoded image.
export function createStagedAssets({images,loadImage,loadPeople,groups=venueAssetGroups,files=venueImageFiles}){
 const pending=new Map(),loaded=new Set();
 function once(key,load){
  if(!pending.has(key)){
   const promise=Promise.resolve().then(load).then(value=>{loaded.add(key);return value;});
   pending.set(key,promise);
   promise.catch(()=>{if(pending.get(key)===promise)pending.delete(key);});
  }
  return pending.get(key);
 }
 function plan(group){const result=groups[group];if(!result)throw Error('Unknown asset group');return result;}
 return {
  ready(group){const p=plan(group);return p.people.every(name=>loaded.has('person:'+name))&&p.images.every(name=>!!images[name]);},
  async load(group,{onProgress=()=>{}}={}){
   const p=plan(group),jobs=new Map();
   for(const name of p.people)jobs.set('person:'+name,()=>once('person:'+name,()=>loadPeople({names:[name]})));
   for(const name of p.images){
    const file=files[name];if(!file)throw Error('Unknown image');
    const key='image:'+file,previous=jobs.get(key);
    jobs.set(key,async()=>{await previous?.();images[name]=await once(key,()=>loadImage(`/play/assets/${file}`));});
   }
   let done=0;onProgress(0);
   await Promise.all([...jobs.values()].map(async job=>{await job();onProgress(Math.round(++done/jobs.size*100));}));
   onProgress(100);
  },
 };
}
