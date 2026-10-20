import test from 'node:test';
import assert from 'node:assert/strict';
import {createDialogLifecycle} from '../../test-overrides/chh-show-night/dialog-lifecycle.mjs';
import {initialState,act,restore,score,objective} from '../../test-overrides/chh-show-night/state.mjs';
import {hasVisited,nextStop} from '../../test-overrides/chh-show-night/journey-guide.mjs';
import {stepToward,walkable} from '../../test-overrides/chh-show-night/navigation.mjs';
import {breakProgress,breakDuration} from '../../test-overrides/chh-show-night/water-break.mjs';
import {merchDrop,merchCatch} from '../../test-overrides/chh-show-night/merch-motion.mjs';
import {roundSchedule,roundScore,roundSeconds} from '../../test-overrides/chh-show-night/scoring.mjs';
const atShow=()=>act(act(act(initialState(),'invite','jay'),'invite','grace'),'enter');

test('A queued close from the previous screen does not stop a newly opened activity',()=>{
 const classes=new Set(['game-dialog']);const dialog={open:true,classList:{remove(...values){values.forEach(v=>classes.delete(v));}},close(){this.open=false;}};
 const content={className:'round',dataset:{phase:'result',game:'eli'},replaceChildren(){}};
 const modal=createDialogLifecycle(dialog,content);let oldStops=0,newStops=0;
 modal.attach(()=>oldStops++);modal.close();assert.equal(oldStops,1);
 modal.prepare();dialog.open=true;classes.add('game-dialog');content.className='round';modal.attach(()=>newStops++);
 assert.equal(modal.onNativeClose(),false);assert.equal(newStops,0);assert.equal(content.className,'round');assert.ok(classes.has('game-dialog'));
 dialog.open=false;assert.equal(modal.onNativeClose(),true);assert.equal(newStops,1);assert.equal(content.className,'');
 modal.onNativeClose();assert.equal(newStops,1);
});

test('Replacing a round in the same dialog cleans it up before the next view is mounted',()=>{
 const dialog={open:true,classList:{remove(){}},close(){this.open=false;}},content={className:'round',dataset:{phase:'playing'},replaceChildren(){}};
 const modal=createDialogLifecycle(dialog,content);let stops=0;modal.attach(()=>stops++);modal.prepare();assert.equal(stops,1);assert.equal(content.className,'');assert.equal(content.dataset.phase,undefined);
});

test('Short movement steps reach room edges without overshooting or stranding a route',()=>{
 for(const room of ['outside','show','vip'])for(const fps of [25,60,120])for(const target of [{x:992,y:644},{x:32,y:444},{x:940,y:447}]){
  let current={x:500,y:575},arrived=false;
  for(let frame=0;frame<fps*7&&!arrived;frame++){const step=stepToward(room,current,target,180/fps);assert.ok(walkable(room,step.x,step.y));current={x:step.x,y:step.y};arrived=step.arrived;}
  assert.ok(arrived);assert.deepEqual(current,target);
 }
 assert.deepEqual(stepToward('show',{x:990,y:444},{x:992,y:300},7.2),{x:992,y:444,arrived:true});
});

test('Guidance follows friends, visits and free VIP entry without inventing points',()=>{
 let s=initialState();assert.equal(nextStop(s),'jay');assert.match(objective(s),/Bring Jay along/);
 s=act(s,'invite','jay');assert.equal(nextStop(s),'grace');s=act(s,'invite','grace');assert.equal(nextStop(s),'enter');
 s=act(s,'enter');assert.equal(nextStop(s),'merch');const before=score(s);
 for(const id of ['merch','brenno','dj','marty'])s=act(s,'visit',id);
 assert.equal(score(s),before);assert.equal(nextStop(s),'vip');assert.ok(hasVisited(restore(JSON.stringify(s)),'marty'));
 s=act(act(s,'unlockVip','NOT4SALE'),'vip');assert.equal(nextStop(s),'photo');s=act(s,'photo');assert.equal(nextStop(s),'refresh');s=act(s,'visit','refresh');assert.equal(nextStop(s),null);
 assert.equal(act(act(atShow(),'unlockVip','NOT4SALE'),'vip').room,'vip');assert.deepEqual(act(initialState(),'visit','merch').visited,[]);
});

test('A completed zero-score game is still a visited stop',()=>{
 const s=act(atShow(),'round',{game:'marty',id:'zero',events:Array.from({length:20},(_,id)=>({id,hit:false,perfect:false}))});
 assert.equal(s.totals.marty,0);assert.ok(hasVisited(s,'marty'));assert.ok(hasVisited(restore(JSON.stringify(s)),'marty'));
});

test('Water breaks expire after six seconds, including after returning from a backgrounded tab',()=>{
 assert.equal(breakProgress(1000,1000).remaining,6);assert.equal(breakProgress(1000,4001).remaining,3);
 assert.equal(breakProgress(1000,1000+breakDuration).done,true);assert.equal(breakProgress(1000,90000).remaining,0);
});

test('Merch requires left/right movement, with faster readable drops and the same score budget',()=>{
 const notes=roundSchedule('apollo',26);
 for(const [i,n] of notes.entries()){
  const at=merchDrop(n,n.at);assert.equal(at.y,475);assert.equal(at.x,n.x);
  assert.ok(at.x>=65&&at.x<=355);assert.ok(merchDrop(n,n.at-.5).y<390);
  if(i)assert.ok(Math.abs(n.x-notes[i-1].x)>100);
  assert.ok(n.at<roundSeconds.apollo);
 }
 assert.ok(merchCatch.hit<52);assert.ok(merchCatch.clean<23);
 assert.equal(roundScore(notes.map(n=>({id:n.id,hit:true,perfect:true}))).total,1000);
});
