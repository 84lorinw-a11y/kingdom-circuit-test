import test from 'node:test';
import assert from 'node:assert/strict';
import {createBassDetector,createBassPulse} from '../../test-overrides/chh-show-night/bass-fx.mjs';

function fixture(options={}){
 const animations=[],vibrations=[];
 const panel={animate(frames,timing){const animation={frames,timing,cancel(){this.cancelled=true;}};animations.push(animation);return animation;}};
 const pulse=createBassPulse([panel,panel],{mobile:true,vibrate:pattern=>vibrations.push(pattern),...options});
 return {pulse,animations,vibrations};
}

test('Phone bass kicks visibly move and rotate the panel, then return it to rest',()=>{
 const f=fixture();assert.equal(f.pulse.hit(),true);assert.equal(f.animations.length,1);
 const animation=f.animations[0];
 assert.ok(animation.frames.some(f=>Math.abs(parseFloat(f.transform.slice(10)))>=12));
 assert.ok(animation.frames.some(f=>/rotate\(-?0\.[1-9]/.test(f.transform)));
 assert.equal(animation.frames.at(-1).transform,'translate(0px,0px) rotate(0deg)');
 assert.ok(animation.timing.duration>=250);
 const pattern=f.vibrations.at(-1);assert.equal(pattern.length,3);assert.ok(pattern[0]+pattern[2]>=100);
});

test('New hits cancel old animations; turning effects off stops motion and vibration immediately',()=>{
 const f=fixture();f.pulse.hit();f.pulse.hit();assert.equal(f.animations[0].cancelled,true);
 assert.equal(f.pulse.setEnabled(false),false);assert.equal(f.animations[1].cancelled,true);assert.equal(f.vibrations.at(-1),0);
 assert.equal(f.pulse.hit(),false);assert.equal(f.animations.length,2);
 assert.equal(f.pulse.setEnabled(true),true);assert.equal(f.pulse.hit(),true);
 f.pulse.clear();assert.equal(f.animations[2].cancelled,true);assert.equal(f.vibrations.at(-1),0);
});

test('Reduced motion prevents both shakes and vibration, including after a toggle',()=>{
 const f=fixture({reduceMotion:true});assert.equal(f.pulse.hit(),false);assert.equal(f.pulse.setEnabled(true),false);
 assert.equal(f.pulse.hit(),false);assert.equal(f.animations.length,0);assert.ok(f.vibrations.every(v=>v===0));
});

test('Visual shake works when vibration is unsupported or denied',()=>{
 for(const vibrate of [()=>false,()=>{throw new Error('Unsupported');}]){
  const f=fixture({vibrate});assert.doesNotThrow(()=>f.pulse.hit());assert.equal(f.animations.length,1);assert.doesNotThrow(()=>f.pulse.clear());
 }
});

test('Quieter bass transients trigger while silence and sustained bass do not',()=>{
 const detector=createBassDetector();
 for(let time=0;time<500;time+=16)assert.equal(detector.sample(.003,time),false);
 assert.equal(detector.sample(.04,500),true);
 for(let time=516;time<1500;time+=16)assert.equal(detector.sample(.04,time),false);
});
