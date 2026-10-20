import test from 'node:test';
import assert from 'node:assert/strict';
import {stageVideos,didVideoWrap,stageCanPlay,stageEmbedUrl,createStageVideos} from '../../test-overrides/chh-show-night/stage-videos.mjs';
const active={room:'show',ready:true,blocked:false,hidden:false,visible:1,width:1024,height:683,viewWidth:1024,camera:0};
test('Only the three supplied Shorts use privacy-enhanced embeds with an origin',()=>{
 assert.deepEqual(stageVideos.map(v=>v.id),['igVFE1_Dl1A','a0lIU4jiL6M','XyZJtJ3t0Vc']);
 for(let i=0;i<3;i++){
  const url=new URL(stageEmbedUrl(i,'https://84lorinw-a11y.github.io'));
  assert.equal(url.origin,'https://www.youtube-nocookie.com');
  assert.equal(url.pathname,`/embed/${stageVideos[i].id}`);
  assert.equal(url.searchParams.get('origin'),'https://84lorinw-a11y.github.io');
  assert.equal(url.searchParams.get('controls'),'1');
 }
});
test('Playback requires an admitted, visible main stage; reduced motion waits for a gesture',()=>{
 assert.equal(stageCanPlay(active),true);
 for(const override of [{room:'vip'},{room:'outside'},{ready:false},{blocked:true},{hidden:true},{visible:.49},{reduced:true},{paused:true}])
  assert.equal(stageCanPlay({...active,...override}),false,JSON.stringify(override));
 assert.equal(stageCanPlay({...active,reduced:true,requested:true}),true);
});
function harness(t,{reduced=false,reject=false}={}){
 const saved={};for(const k of ['window','document','location','IntersectionObserver'])saved[k]=globalThis[k];
 t.after(()=>{for(const [k,v] of Object.entries(saved))if(v===undefined)delete globalThis[k];else globalThis[k]=v;});
 const node=()=>({hidden:true,style:{},attributes:{},setAttribute(k,v){this.attributes[k]=v;},replaceChildren(...children){this.children=children;}});
 const root=node(),buttons=Object.fromEntries(['toggle','next','status','link'].map(key=>[`#stage-video-${key}`,node()]));
 const tools={...node(),querySelector:key=>buttons[key]};let observation,player,time=0;const events={};
 globalThis.location={origin:'https://test.example'};
 globalThis.document={hidden:false,createElement:()=>node(),addEventListener:(key,fn)=>events[key]=fn};
 globalThis.window={addEventListener:(key,fn)=>events[key]=fn};
 globalThis.IntersectionObserver=class{constructor(fn){observation=fn;}observe(){}};
 class Player{
  constructor(iframe,{events}){player=this;this.events=events;this.commands=[];this.muted=false;this.state=-1;queueMicrotask(()=>events.onReady());}
  mute(){this.muted=true;}
  isMuted(){return this.muted;}
  getPlayerState(){return this.state;}
  getCurrentTime(){return this.current||0;}
  getDuration(){return 26.161;}
  playVideo(){this.commands.push('play');}
  pauseVideo(){this.commands.push('pause');}
  loadVideoById(id){this.commands.push(['load',id]);}
  cueVideoById(id){this.commands.push(['cue',id]);}
  emit(data){this.state=data;this.events.onStateChange({data});}
 }
 let loads=0;
 const controller=createStageVideos({root,tools,reduced,now:()=>time,loadAPI:()=>{loads++;return reject?Promise.reject(new Error('offline')):Promise.resolve({Player});}});
 return {controller,root,tools,buttons,events,tick(current){time+=300;player.current=current;controller.update(active);},get player(){return player;},get loads(){return loads;},see(ratio=1){observation([{intersectionRatio:ratio}]);},async enter(){controller.update(active);this.see();await new Promise(resolve=>setImmediate(resolve));}};
}
test('One lazy player loops all three, ignoring transient pause events while switching clips',async t=>{
 const h=harness(t);h.controller.update({...active,room:'outside'});assert.equal(h.loads,0);
 await h.enter();assert.equal(h.loads,1);assert.equal(h.player.muted,true);h.player.emit(1);
 for(const id of ['a0lIU4jiL6M','XyZJtJ3t0Vc','igVFE1_Dl1A']){
  h.player.emit(0);assert.ok(h.player.commands.some(c=>Array.isArray(c)&&c[0]==='load'&&c[1]===id));
  h.player.emit(2);assert.equal(h.buttons['#stage-video-toggle'].textContent,'Pause screen');h.player.emit(1);
 }
 h.controller.update(active);assert.equal(h.loads,1);
});
test('Pause survives room changes; games, invisible screens and background tabs suspend playback',async t=>{
 const h=harness(t);await h.enter();h.player.emit(1);
 h.controller.update({...active,blocked:true});assert.equal(h.player.commands.at(-1),'pause');assert.equal(h.root.hidden,true);
 h.controller.update(active);h.player.emit(1);h.see(.3);assert.equal(h.player.commands.at(-1),'pause');
 h.see();h.player.emit(1);h.buttons['#stage-video-toggle'].onclick();assert.equal(h.player.commands.at(-1),'pause');
 h.controller.update({...active,room:'vip'});h.controller.update(active);assert.equal(h.player.commands.at(-1),'pause');
 h.buttons['#stage-video-toggle'].onclick();h.player.emit(1);document.hidden=true;h.events.visibilitychange();assert.equal(h.player.commands.at(-1),'pause');
});
test('Reduced motion requires Play screen; unavailable clips stop after one attempt each',async t=>{
 const h=harness(t,{reduced:true});await h.enter();assert.equal(h.player.commands.at(-1),'pause');
 h.buttons['#stage-video-toggle'].onclick();assert.equal(h.player.commands.at(-1),'play');h.player.emit(1);
 for(let i=0;i<3;i++)h.player.events.onError({data:150});
 assert.equal(h.buttons['#stage-video-status'].textContent,'Video unavailable');
 assert.equal(h.buttons['#stage-video-next'].disabled,true);assert.equal(h.player.commands.at(-1),'pause');
 assert.equal(h.player.commands.filter(c=>Array.isArray(c)&&c[0]==='load').length,2);
});
test('API failures leave a working external link and an explicit retry',async t=>{
 const h=harness(t,{reject:true});await h.enter();assert.equal(h.buttons['#stage-video-status'].textContent,'Video unavailable');
 assert.equal(h.buttons['#stage-video-link'].href,'https://www.youtube.com/shorts/igVFE1_Dl1A');
 h.controller.update(active);assert.equal(h.loads,1);h.buttons['#stage-video-toggle'].onclick();assert.equal(h.loads,2);
 await new Promise(resolve=>setImmediate(resolve));
});

test('The Shorts internal loop advances exactly once after the full clip, without needing ENDED',async t=>{
 const h=harness(t);await h.enter();h.player.emit(1);
 h.tick(25.8);h.tick(.1);
 assert.equal(h.buttons['#stage-video-status'].textContent,'2 / 3');
 h.tick(.2);assert.equal(h.buttons['#stage-video-status'].textContent,'2 / 3');
 assert.equal(didVideoWrap(10,.2,26),false);
 assert.equal(didVideoWrap(25.9,.2,26),true);
 assert.equal(didVideoWrap(25.9,.2,NaN),false);
});
test('Phone camera keeps the native controls inside the visible wall and pauses when it leaves view',async t=>{
 const h=harness(t);await h.enter();h.player.emit(1);
 h.controller.update({...active,width:375,viewWidth:375,camera:300});
 assert.equal(h.root.style.left,'23px');assert.equal(h.root.style.width,'352px');assert.equal(h.root.hidden,false);
 h.controller.update({...active,width:375,viewWidth:375,camera:0});
 assert.equal(h.root.hidden,true);assert.equal(h.player.commands.at(-1),'pause');
});
