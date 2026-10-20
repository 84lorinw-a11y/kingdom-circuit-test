import test from 'node:test';
import assert from 'node:assert/strict';
import {gameIds,roundSchedule,roundScore,roundSeconds} from '../../test-overrides/chh-show-night/scoring.mjs';
import {crewGames,currentPrompt,correctChoice,judgeChoice,judgePosition,laneCenter,roadLane,spotlightX,wordOptions,phrases} from '../../test-overrides/chh-show-night/crew-games.mjs';
import {offerLane,offerX,offerPrompt,judgeOffer} from '../../test-overrides/chh-show-night/marty-offers.mjs';
import {act,initialState,restore,score} from '../../test-overrides/chh-show-night/state.mjs';

test('Every artist has a game, with existing scoring and saved scores preserved',()=>{
 assert.equal(gameIds.length,10);assert.equal(Object.keys(crewGames).length,7);
 let state=act(act(act(initialState(),'invite','jay'),'invite','grace'),'enter');
 for(const game of gameIds){state=act(state,'round',{id:game,game,events:roundSchedule(game,42).map(n=>({id:n.id,hit:true,perfect:true}))});}
 assert.equal(score(state),10030);assert.deepEqual(restore(JSON.stringify(state)).totals,state.totals);
 const old=restore(JSON.stringify({...state,totals:{eli:550,marty:400,brenno:200,apollo:100}}));assert.equal(old.totals['andrew-prim'],0);assert.equal(score(old),1280);
});
test('Marty rejects a buyout at a stationary table, keeps legitimate offers, and cannot double score',()=>{
 const notes=roundSchedule('marty',23),n=notes[0],lane=offerLane(n);
 assert.equal(judgeOffer(notes,lane,-.1),null);assert.equal(judgeOffer(notes,3,.2),null);
 assert.equal(judgeOffer(notes,(lane+1)%3,.2).hit,false);
 assert.equal(judgeOffer(notes,lane,.2).perfect,true);assert.equal(judgeOffer(notes,lane,1.1).perfect,false);
 assert.equal(judgeOffer(notes,lane,n.at+.1),null);
 n.done=true;assert.equal(judgeOffer(notes,lane,.2),null,'Next proposal does not open until its time');
 assert.ok(offerX(lane)>=70&&offerX(lane)<=350);
});
test('All seven crew prototypes have achievable clean rounds and a hard 1000-point maximum',()=>{
 for(const game of Object.keys(crewGames)){
  const notes=roundSchedule(game,66),events=[];
  for(const note of notes){let result;
   if(['slider','spotlight'].includes(crewGames[game].mode))result=judgePosition(game,note,game==='gavin-the-hotrod'?laneCenter(roadLane(note)):note.x);
   else {const start=currentPrompt(notes,0,game).start;result=judgeChoice(game,notes,correctChoice(game,note),start+.2);assert.ok(result,game);}
   assert.ok(result.hit,game);assert.ok(result.perfect,game);events.push({id:note.id,hit:result.hit,perfect:result.perfect});note.done=true;
  }
  assert.equal(roundScore(events).total,1000,game);assert.equal(roundScore([...events,...events]).total,1000,game);assert.ok(notes.at(-1).at<roundSeconds[game]);
 }
});
test('Wrong, early, late and invalid answers cannot earn points; memory hides input during preview',()=>{
 for(const game of ['brenno','gavin-the-hotrod','lj-the-messenger','tonyxtrotter','andrew-prim']){
  const notes=roundSchedule(game,31),n=notes[0],start=currentPrompt(notes,0,game).start,index=correctChoice(game,n);
  assert.equal(judgeChoice(game,notes,-1,start+.1),null);assert.equal(judgeChoice(game,notes,9,start+.1),null);assert.equal(judgeChoice(game,notes,index,n.at+.1),null);
  const wrong=judgeChoice(game,notes,(index+1)%crewGames[game].labels.length,start+.1);assert.equal(wrong.hit,false);
  if(game==='andrew-prim')assert.equal(judgeChoice(game,notes,index,.9),null);
  n.done=true;assert.notEqual(judgeChoice(game,notes,index,start+.1)?.note.id,0);
 }
});
test('Position games require the open lane / note / subject and word puzzles keep all four choices',()=>{
 const n=roundSchedule('ryan-ellis',5)[0];assert.equal(judgePosition('ryan-ellis',n,n.x+60).hit,false);
 assert.equal(spotlightX(n,n.at),n.x);assert.equal(judgePosition('dearis',n,n.x+60).hit,false);
 assert.equal(judgePosition('gavin-the-hotrod',n,laneCenter((roadLane(n)+1)%3)).hit,false);
 for(const note of roundSchedule('tonyxtrotter',4)){assert.deepEqual([...wordOptions(note)].sort(),[...phrases[Math.floor(note.id/4)]].sort());}
});
