import test from 'node:test';
import assert from 'node:assert/strict';
import {apolloCrew,frontCrew,producerActor,vipCrew,photoLineup,boothLayout,drawApolloStage} from '../../test-overrides/chh-show-night/apollo-crew.mjs';
import {findPath} from '../../test-overrides/chh-show-night/navigation.mjs';
import {stageSpots,stageArtistAt} from '../../test-overrides/chh-show-night/worship.mjs';
import {practiceSpot,isBoothTap} from '../../test-overrides/chh-show-night/practice-booth.mjs';
import {createScoreStore,createOnlineScores} from '../../test-overrides/chh-show-night/leaderboard.mjs';
import {initialState,act} from '../../test-overrides/chh-show-night/state.mjs';

test('The nine-person crew has one producer, a centered DJ and seven front performers',()=>{
 assert.equal(apolloCrew.length,9);
 assert.equal(new Set(apolloCrew.map(p=>p.id)).size,9);
 const drawn=[];drawApolloStage({},0,true,(ctx,x,y,id,options)=>drawn.push({x,y,id,...options}));
 assert.equal(drawn.length,7);
 assert.deepEqual(drawn.map(p=>p.id).sort(),frontCrew.map(p=>p.id).sort());
 assert.equal(drawn.at(-1).id,'marty');
 assert.ok(drawn.slice(0,-1).every(p=>p.y<drawn.at(-1).y));
 assert.ok(drawn.every(p=>p.id!=='eli-williams'&&p.y>boothLayout.y+8));
 for(const spot of stageSpots)assert.equal(spot.x,apolloCrew.find(p=>p.id===spot.id).stageX);
 assert.ok(Math.abs(boothLayout.x-apolloCrew.find(p=>p.id==='marty').stageX)<=25,'Eli stays centered immediately behind Marty');
 assert.ok(Math.abs(practiceSpot.x-boothLayout.x)>100,'Eli’s entrance must not trigger Marty’s round');
 assert.deepEqual([...drawn.map(p=>p.id),producerActor.who,'eli-williams'].sort(),apolloCrew.map(p=>p.id).sort());
 assert.ok(producerActor.x>850&&producerActor.y>=444,'Andrew stands beside the stage on the audience floor');
 assert.ok(isBoothTap({x:boothLayout.x,y:boothLayout.y-115}));
 assert.ok(!isBoothTap({x:550,y:250}),'Marty’s body must not trigger the DJ game');
 assert.equal(stageArtistAt({x:550,y:250}),'marty');
 assert.equal(stageArtistAt({x:570,y:211}),null);
 assert.ok(!isBoothTap({x:850,y:230}),'The old side booth is no longer a DJ target');
 assert.ok(boothLayout.width<222&&boothLayout.y<363);
});

test('All nine crew members share one close VIP line; every photo includes the crew and guests',()=>{
 const ids=apolloCrew.map(p=>p.id).sort();
 assert.deepEqual(vipCrew.map(p=>p.who).sort(),ids);
 for(const artist of vipCrew){
  const target={x:artist.x,y:artist.y+35};
  assert.deepEqual(findPath('vip',{x:500,y:620},target),[target]);

 }
 assert.equal(new Set(vipCrew.map(p=>p.y)).size,1);
 const line=[...vipCrew].sort((a,b)=>a.x-b.x);
 for(let i=1;i<line.length;i++)assert.ok(line[i].x-line[i-1].x>=48&&line[i].x-line[i-1].x<=56,'Close shoulders with separate faces');
 for(const avatar of ['player','crowd-vip:32',4]){
  const photo=photoLineup(avatar);
  assert.deepEqual(photo.filter(p=>ids.includes(p.who)).map(p=>p.who).sort(),ids);
  assert.equal(photo.length,12);
  assert.equal(new Set(photo.map(p=>p.y)).size,1,'The exported VIP photo is one line, not separated rows');
  assert.equal(new Set(photo.map(p=>p.x)).size,12);
  assert.ok(photo.every(p=>p.x>130&&p.x<1400),'Keep the entire lineup within the shared photo crop');
  assert.equal(photo.filter(p=>p.who===avatar).length,1);
  assert.ok(photo.some(p=>p.who==='jay')&&photo.some(p=>p.who==='grace'));
 }
});

test('Apollo cannot read or overwrite the original competition or call it during play',async()=>{
 const original=JSON.stringify({best:{nickname:'Original player',total:99999},players:{}});
 const data=new Map([['kc-show-night-scores-v2',original],['kc-show-night-v1','production save']]);
 const storage={getItem:key=>data.get(key),setItem:(key,value)=>data.set(key,value)};
 const store=createScoreStore(storage);
 assert.equal((await store.board()).rows.length,0);
 const state=act(initialState(),'profile',{name:'Apollo test',avatar:'red'});
 store.record(state);
 assert.equal((await store.board()).rows.length,1);
 assert.equal(data.get('kc-show-night-scores-v2'),original);
 assert.equal(data.get('kc-show-night-v1'),'production save');
 let requests=0;
 const online=createOnlineScores(storage,{base:'',fetcher:()=>{requests++;throw Error('Unexpected network call');}});
 await online.connect(state);online.journey('invite','jay');await online.start('marty');await online.finish({});
 assert.equal(requests,0);
 assert.throws(()=>createOnlineScores(storage,{base:'https://script.google.com/macros/s/original/exec'}),/cannot use the original competition/);
});
