// A single designed cast travels through the entire night. Skin-tone groups describe
// the art direction, not information collected about players.
export const sharedCast=Array.from({length:30},(_,i)=>({
 id:`fan-${i}`,who:i===0?'women:0':i===12?'women:1':i===1?'brand:0':i===4?'brand:1':`fan:${i}`,
 appearance:i===0||i===12?'Black':['white','Black','brown'][i%3]
}));
// Reference-based fans keep their identity through all rooms and games.
export const clubFanPoses=Object.fromEntries([1,4,22,23,24,25,26,27].map((id,index)=>[sharedCast[id].who,index]));
export const actualFanPoses=Object.fromEntries([0,2,3,5,6,7,12,22].map((id,index)=>[sharedCast[id].who,index]));
export const brennoFan=id=>sharedCast[((id%sharedCast.length)+sharedCast.length)%sharedCast.length].who;
export function collectedFans(events){return events.filter(e=>e.hit).map(e=>brennoFan(e.id));}
// Deliberate crowd placement leaves the entrance, shop, stage center, and photo lane readable.
const fan=(x,y,i,extra={})=>({x,y,who:null,scale:2.15+(i%3)*.05,ambient:true,phase:i*1.71,flip:i%3===0,...extra});
const outside=[];
// Ten conversations, eight standing in line, and two overnight campers at the head.
const conversations=[[342,500],[405,508],[470,504],[532,512],[410,589],[475,601],
 [550,610],[615,601],[330,663],[392,670],[460,660],[520,671],
 [610,659],[670,666],[720,540],[785,551],[567,557],[625,550],[315,558],[350,583]];
const queue=[[931,515],[978,547],[933,578],[978,609],[931,640],[868,669],[803,651],[742,629]];
conversations.forEach(([x,y],i)=>outside.push(fan(x,y,i,{role:'conversation',outsidePose:i,flip:[1,3,4,12].includes(i),scale:2.08})));
queue.forEach(([x,y],i)=>outside.push(fan(x,y,20+i,{role:'queue',queueOrder:i+1,outsidePose:20+i,flip:i%2===0,scale:2.08})));
outside.push(fan(797,478,28,{role:'camper',campPose:0,flip:false,scale:2.08}),fan(875,490,29,{role:'camper',campPose:1,flip:false,scale:2.08}));
const show=[];
// An uneven crowd across the floor, with a few fans nearer the stage.
// Positions account for raised arms and bodies, keeping the floor circles clear.
[[423,536],[206,555],[810,553],[390,620],[614,548],[196,582],
 [610,604],[820,603],[247,627],[335,620],[505,626],[716,635],
 [785,625],[899,659],[170,654],[275,668],[395,653],[459,675],
 [575,638],[647,665],[762,674],[838,646],[965,660],[219,602],
 [340,659],[535,673],[701,668],[925,675],[215,661],[860,675]
].forEach(([x,y],i)=>show.push(fan(x,y,i,{scale:2.12+(i%3)*.04,back:true,hands:true})));
Object.assign(show[1],{x:290,y:590});
Object.assign(show[5],{x:225,y:635});
Object.assign(show[23],{x:300,y:570});
Object.assign(show[22],{x:675,y:610,back:false,hands:false,flip:false});
Object.assign(show[9],{x:48,y:574,scale:2.1,back:false,hands:false});
Object.assign(show[20],{x:165,y:578,scale:2.1,back:false,hands:false});
// Clear the performers' bodies without removing fans or changing their artwork.
Object.assign(show[0],{x:455,y:604});
Object.assign(show[4],{x:642,y:609});
Object.assign(show[23],{x:315,y:618});
Object.assign(show[2],{x:845,y:605});
const vip=[];
// Small conversation clusters, with an open photo line and snack counter.
// Keep everyone on the floor, clear of the couch, coffee table and serving table.
const vipSpots=[[50,292],[130,298],[310,292],[355,325],[690,310],[760,329],[680,430],[755,450],[820,350],[975,361],
 [395,490],[465,510],[535,475],[600,455],[775,475],[900,480],[975,471],
 [350,585],[395,645],[465,630],[545,598],[600,665],[675,623],[795,650],[860,592],[920,645],[975,568],
 [60,670],[145,655],[245,670]];
vipSpots.forEach(([x,y],i)=>vip.push(fan(x,y,i,{scale:2.08,flip:i%2===0,outsidePose:i<28?i:undefined})));
// Identical identities and outfits in every room; the stage uses matching rear poses.
for(const cast of [outside,show,vip])cast.forEach((a,i)=>{a.who=sharedCast[i].who;a.phase=i*1.71;});
export const crowdCounts={outside:outside.length,show:show.length,vip:vip.length};
export function crowdActors(room,time,reduceMotion,player){const newcomers=room==='show'?Array.from({length:Math.min(10,Math.ceil((player.crewDelivered||0)/2))},(_,i)=>({...fan(282+(i%5)*120,548+Math.floor(i/5)*63,i,{scale:2.1,back:true,hands:true}),who:brennoFan(20+i)})):[];return [...({outside,show,vip}[room]||[]),...newcomers].map(a=>{
 const animated=!reduceMotion&&a.role!=='camper';return{...a,y:a.y+(animated?Math.sin(time/420+a.phase)*1.7:0),lean:animated?Math.sin(time/650+a.phase)*.018:0,alpha:1};
});}
