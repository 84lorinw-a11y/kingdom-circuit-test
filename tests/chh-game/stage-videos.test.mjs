import test from 'node:test';
import assert from 'node:assert/strict';
import {stageFilm,stageCanPlay,createStageVideos} from '../../test-overrides/chh-show-night/stage-videos.mjs';
const active={room:'show',ready:true,blocked:false,hidden:false,visible:1,width:1024,height:683,viewWidth:1024,camera:0};
const settle=()=>new Promise(resolve=>setImmediate(resolve));
function harness(t,{reduced=false,playResult=()=>Promise.resolve()}={}){
 const saved={};for(const k of ['window','document','IntersectionObserver'])saved[k]=globalThis[k];
 t.after(()=>{for(const [k,v] of Object.entries(saved))if(v===undefined)delete globalThis[k];else globalThis[k]=v;});
 const node=()=>({hidden:false,style:{},attributes:{},events:{},setAttribute(k,v){this.attributes[k]=v;},addEventListener(k,fn){this.events[k]=fn;},replaceChildren(...children){this.children=children;}});
 const root={...node(),hidden:true},buttons=Object.fromEntries(['toggle','status'].map(key=>[`#stage-video-${key}`,node()]));
 const tools={...node(),hidden:true,querySelector:key=>buttons[key]};let observation,video;const events={},created=[];
 globalThis.document={hidden:false,createElement:tag=>{
  const element=node();created.push(tag);
  if(tag==='video')video=Object.assign(element,{paused:true,commands:[],play(){this.commands.push('play');this.paused=false;return playResult();},pause(){this.commands.push('pause');this.paused=true;},load(){this.commands.push('load');}});
  return element;
 },addEventListener:(key,fn)=>events[key]=fn};
 globalThis.window={addEventListener:(key,fn)=>events[key]=fn};
 globalThis.IntersectionObserver=class{constructor(fn){observation=fn;}observe(){}};
 const controller=createStageVideos({root,tools,reduced});
 return {controller,root,tools,buttons,events,created,get video(){return video;},see(ratio=1){observation([{intersectionRatio:ratio}]);},async enter(){controller.update(active);this.see();await settle();}};
}
test('Playback requires an admitted visible stage; reduced motion waits for a request',()=>{
 assert.equal(stageCanPlay(active),true);
 for(const override of [{room:'vip'},{room:'outside'},{ready:false},{blocked:true},{hidden:true},{visible:.49},{reduced:true},{paused:true}])
  assert.equal(stageCanPlay({...active,...override}),false,JSON.stringify(override));
 assert.equal(stageCanPlay({...active,reduced:true,requested:true}),true);
});
test('Stage lazily creates one local silent looping video without third-party UI',async t=>{
 const h=harness(t);h.controller.update({...active,room:'outside'});assert.equal(h.created.length,0);
 await h.enter();h.controller.update(active);
 assert.deepEqual(h.created,['img','video']);assert.equal(h.video.src,stageFilm.src);
 assert.ok(stageFilm.src.startsWith('/play/assets/video/'));assert.equal(h.video.poster,stageFilm.poster);
 assert.equal(h.video.loop,true);assert.equal(h.video.playsInline,true);assert.equal(h.video.controls,false);
 assert.equal(h.video.preload,'none');assert.equal(h.video.defaultMuted,true);
 assert.equal(h.video.muted,true);assert.equal(h.video.volume,0);assert.equal(h.video.paused,false);
 assert.equal(h.tools.hidden,true);assert.equal(h.controller.controls,h.tools);
});
test('Manual pause survives room changes and menu suspension',async t=>{
 const h=harness(t);await h.enter();
 h.controller.update({...active,blocked:true});assert.equal(h.video.paused,true);assert.equal(h.root.hidden,true);
 h.buttons['#stage-video-toggle'].onclick();assert.equal(h.buttons['#stage-video-toggle'].textContent,'Play screen');
 h.controller.update(active);assert.equal(h.video.paused,true);
 h.controller.update({...active,room:'vip'});h.controller.update(active);assert.equal(h.video.paused,true);
 h.controller.update({...active,blocked:true});h.buttons['#stage-video-toggle'].onclick();
 h.controller.update(active);assert.equal(h.video.paused,false);
});
test('Games, other rooms, hidden tabs and offscreen walls pause; return resumes',async t=>{
 const h=harness(t);await h.enter();
 for(const changes of [{blocked:true},{room:'outside'},{room:'vip'},{hidden:true}]){
  h.controller.update({...active,...changes});assert.equal(h.video.paused,true);
  h.controller.update(active);assert.equal(h.video.paused,false);
 }
 h.see(.3);assert.equal(h.video.paused,true);h.see();assert.equal(h.video.paused,false);
 document.hidden=true;h.events.visibilitychange();assert.equal(h.video.paused,true);
 document.hidden=false;h.events.visibilitychange();assert.equal(h.video.paused,false);
 h.events.pagehide();assert.equal(h.video.paused,true);
});
test('Reduced motion shows the still frame until Play screen is chosen',async t=>{
 const h=harness(t,{reduced:true});await h.enter();assert.equal(h.video.paused,true);
 assert.equal(h.video.commands.includes('play'),false);assert.equal(h.video.poster,stageFilm.poster);
 h.controller.update({...active,blocked:true});h.buttons['#stage-video-toggle'].onclick();assert.equal(h.video.paused,true);
 h.controller.update(active);assert.equal(h.video.paused,false);
});
test('Rejected autoplay offers an explicit retry without a frame-by-frame retry loop',async t=>{
 let fail=true;const h=harness(t,{playResult:()=>fail?Promise.reject(Object.assign(new Error(),{name:'NotAllowedError'})):Promise.resolve()});
 await h.enter();assert.equal(h.buttons['#stage-video-status'].textContent,'Tap Play screen');
 for(let i=0;i<10;i++)h.controller.update(active);
 assert.equal(h.video.commands.filter(c=>c==='play').length,1);
 fail=false;h.buttons['#stage-video-toggle'].onclick();await settle();assert.equal(h.video.paused,false);
});
test('Load errors leave a still image and retry only when requested',async t=>{
 const h=harness(t);await h.enter();h.video.events.error();assert.equal(h.video.hidden,true);assert.equal(h.video.paused,true);
 assert.equal(h.root.children[0].src,stageFilm.poster);assert.equal(h.buttons['#stage-video-toggle'].textContent,'Retry video');
 for(let i=0;i<10;i++)h.controller.update(active);assert.equal(h.video.commands.includes('load'),false);
 h.buttons['#stage-video-toggle'].onclick();await settle();assert.equal(h.video.hidden,false);assert.equal(h.video.paused,false);
 assert.ok(h.video.commands.includes('load'));
});
test('The scene gets a decoded video frame or the loaded poster while waiting or recovering',async t=>{
 const h=harness(t);assert.equal(h.controller.frame,null);await h.enter();
 const poster=h.root.children[0];poster.complete=true;poster.naturalWidth=960;
 assert.equal(h.controller.frame,poster);
 h.video.readyState=2;assert.equal(h.controller.frame,h.video);
 h.video.events.error();assert.equal(h.controller.frame,poster);
});
test('A play promise resolving after leaving the stage cannot restart playback',async t=>{
 let resolve;const h=harness(t,{playResult:()=>new Promise(r=>resolve=r)});await h.enter();
 h.controller.update({...active,room:'vip'});h.video.paused=false;resolve();await settle();assert.equal(h.video.paused,true);
});
test('Phone camera preserves picture scale and suspends playback beyond the wall',async t=>{
 const h=harness(t);await h.enter();
 h.controller.update({...active,width:375,viewWidth:375,camera:300});
 assert.equal(h.root.style.left,'23px');assert.equal(h.root.style.width,'454px');assert.equal(h.video.paused,false);
 h.controller.update({...active,width:375,viewWidth:375,camera:0});assert.equal(h.video.paused,true);
 h.controller.update({...active,width:375,viewWidth:375,camera:900});assert.equal(h.root.hidden,true);
});
test('Volume changes cannot enable sound, including while the game music is on',async t=>{
 const h=harness(t);await h.enter();h.video.muted=false;h.video.volume=.8;h.video.events.volumechange();
 assert.equal(h.video.muted,true);assert.equal(h.video.volume,0);
 h.video.muted=false;h.controller.update(active);assert.equal(h.video.muted,true);
});
