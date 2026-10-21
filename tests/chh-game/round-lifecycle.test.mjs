import test from 'node:test';
import assert from 'node:assert/strict';
import {mountRound} from '../../test-overrides/chh-show-night/rounds.mjs';

function harness(game){
 const saved=Object.fromEntries(['document','matchMedia','requestAnimationFrame','cancelAnimationFrame'].map(k=>[k,globalThis[k]]));
 const callbacks=new Map(),listeners=new Map(),finished=[];let serial=0,now=performance.now();
 const gradient={addColorStop(){}},ctx=new Proxy({},{get:(o,k)=>o[k]??(()=>gradient),set:(o,k,v)=>(o[k]=v,true)});
 class Element{
  constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.hidden=false;this.className='';this.textContent='';this.style={setProperty(){},removeProperty(){}};const c=new Set();this.classList={add:x=>c.add(x),remove:x=>c.delete(x),toggle:(x,on)=>on?c.add(x):c.delete(x)};}
  append(...xs){this.children.push(...xs);}replaceChildren(...xs){this.children=xs;}setAttribute(){}getContext(){return ctx;}focus(){}addEventListener(){}removeEventListener(){}
  getBoundingClientRect(){return {width:390,height:500,left:0,top:0};}animate(){return {cancel(){}};}
  querySelector(selector){return all(this).find(e=>e.className===selector.slice(1));}
 }
 const all=e=>[e,...e.children.flatMap(all)];
 globalThis.document={hidden:false,createElement:tag=>new Element(tag),addEventListener:(type,fn)=>listeners.set(type,fn),removeEventListener:type=>listeners.delete(type)};
 globalThis.matchMedia=()=>({matches:false});globalThis.requestAnimationFrame=fn=>{callbacks.set(++serial,fn);return serial;};globalThis.cancelAnimationFrame=id=>callbacks.delete(id);
 const audio={time:0,running:true,muted:true,unlock:async()=>{},preload:async()=>{},play:async()=>{audio.time=0;audio.running=true;return true;},stop:()=>{audio.running=false;}};
 const art={arcade_eli:{width:640,height:960},arcade_studio:{width:640,height:853}},host=new Element('div');
 const dispose=mountRound(host,{game,audio,art,name:'Test',onFinish:r=>finished.push(r),onExit:()=>{},autostart:false});
 return {host,audio,finished,callbacks,find:cls=>all(host).find(e=>e.className===cls),
  frame(time){audio.time=time;const [id,fn]=callbacks.entries().next().value;callbacks.delete(id);fn(now+=50);},
  key(key){listeners.get('keydown')({key,repeat:false,target:{},preventDefault(){}});},
  hide(){document.hidden=true;listeners.get('visibilitychange')();},
  close(){dispose();Object.assign(globalThis,saved);}
 };
}
for(const game of ['eli','apollo'])test(`${game}: artwork-ready round completes once, replays, and releases its animation on exit`,async()=>{
 const h=harness(game);try{
  assert.equal(h.host.dataset.phase,'ready');await h.find('round-start').onclick();h.frame(26);
  assert.equal(h.host.dataset.phase,'result');assert.equal(h.finished.length,1);assert.equal(h.finished[0].events.length,20);
  h.frame(26);assert.equal(h.finished.length,1);
  await h.find('round-start').onclick();assert.equal(h.host.dataset.phase,'playing');h.frame(26);
  assert.equal(h.finished.length,2);assert.notEqual(h.finished[0].id,h.finished[1].id);
 }finally{h.close();}assert.equal(h.callbacks.size,0);
});
test('Eli still scores a clean live-audio hit and interruption does not bank a partial round',async()=>{
 const h=harness('eli');try{
  await h.find('round-start').onclick();h.frame(2.58);h.key(' ');
  assert.equal(h.find('round-stats').children[0].children[1].textContent,50);
  h.hide();assert.equal(h.host.dataset.phase,'ready');assert.equal(h.finished.length,0);
 }finally{h.close();}
});
