// A single designed cast travels through the entire night. Skin-tone groups describe
// the art direction, not information collected about players.
export const sharedCast=Array.from({length:30},(_,i)=>({
 id:`fan-${i}`,who:i===0?'women:0':i===12?'women:1':i===1?'brand:0':i===4?'brand:1':`fan:${i}`,
 appearance:i===0||i===12?'Black':['white','Black','brown'][i%3]
}));
export const brennoFan=id=>sharedCast[((id%sharedCast.length)+sharedCast.length)%sharedCast.length].who;
export function collectedFans(events){return events.filter(e=>e.hit).map(e=>brennoFan(e.id));}
// Deliberate crowd placement leaves the entrance, shop, stage center, and photo lane readable.
const fan=(x,y,i,extra={})=>({x,y,who:null,scale:2.15+(i%3)*.05,ambient:true,phase:i*1.71,flip:i%3===0,...extra});
const outside=[];
// Conversation groups and a loose queue leave the doors and load-in readable.
[[62,548],[139,587],[70,642],[214,568],[269,633],[198,666],
 [326,547],[387,597],[328,661],[451,563],[500,631],[438,671],
 [566,552],[586,631],[646,670],[782,501],[838,529],[888,564],
 [943,595],[973,652],[768,615],[820,665],[699,581],[702,638],
 [857,609],[954,525],[886,670],[520,588],[230,515],[138,524]
].forEach(([x,y],i)=>outside.push(fan(x,y,i,{scale:2.08+(i%3)*.05})));
const show=[];
// An uneven crowd across the floor, with a few fans nearer the stage.
// Positions account for raised arms and bodies, keeping the floor circles clear.
[[423,536],[206,555],[810,553],[390,620],[614,548],[196,582],
 [610,604],[820,603],[247,627],[335,620],[505,626],[716,635],
 [785,625],[899,659],[170,654],[275,668],[395,653],[459,675],
 [575,638],[647,665],[762,674],[838,646],[965,660],[219,602],
 [340,659],[535,673],[701,668],[925,675],[215,661],[860,675]
].forEach(([x,y],i)=>show.push(fan(x,y,i,{scale:2.12+(i%3)*.04,back:true,hands:true})));
Object.assign(show[9],{x:48,y:574,scale:2.1,back:false,hands:false});
Object.assign(show[20],{x:165,y:578,scale:2.1,back:false,hands:false});
const vip=[];
// Small conversation clusters, with an open photo line and snack counter.
// Keep everyone on the floor, clear of the couch, coffee table and serving table.
const vipSpots=[[50,292],[130,298],[310,292],[385,318],[460,310],[540,329],[680,326],[755,329],[820,350],[975,361],
 [350,478],[420,490],[535,475],[600,455],[775,475],[900,480],[975,471],
 [350,585],[395,645],[465,630],[545,598],[600,665],[675,623],[795,650],[860,592],[920,645],[975,568],
 [60,670],[145,655],[245,670]];
vipSpots.forEach(([x,y],i)=>vip.push(fan(x,y,i,{scale:2.08,flip:i%2===0})));
// Identical identities and outfits in every room; the stage uses matching rear poses.
for(const cast of [outside,show,vip])cast.forEach((a,i)=>{a.who=sharedCast[i].who;a.phase=i*1.71;});
export const crowdCounts={outside:outside.length,show:show.length,vip:vip.length};
export function crowdActors(room,time,reduceMotion,player){const newcomers=room==='show'?Array.from({length:Math.min(10,Math.ceil((player.crewDelivered||0)/2))},(_,i)=>({...fan(282+(i%5)*120,548+Math.floor(i/5)*63,i,{scale:2.1,back:true,hands:true}),who:brennoFan(20+i)})):[];return [...({outside,show,vip}[room]||[]),...newcomers].map(a=>{
 const overlap=a.y>player.y-8&&a.y<player.y+105&&Math.abs(a.x-player.x)<65;
 const animated=!reduceMotion;return{...a,y:a.y+(animated?Math.sin(time/420+a.phase)*1.7:0),lean:animated?Math.sin(time/650+a.phase)*.018:0,alpha:overlap?.35:1};
});}
