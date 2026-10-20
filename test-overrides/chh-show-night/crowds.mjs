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
// Downtown sidewalk: all heads stay below the exterior posters and marquee.
for(let row=0;row<3;row++)for(let col=0;col<10;col++){
 const x=55+col*101+(row%2?22:0),y=548+row*61+(col%3)*4;
 outside.push(fan(Math.min(974,x),y,row*10+col,{scale:2.08+row*.07}));
}
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
const vipSpots=[[220,355],[355,376],[640,352],[475,462],[752,467],[250,550],[358,554],[557,560],[625,601],[799,617],
 [53,320],[115,355],[55,420],[130,440],[56,500],[139,528],[56,596],[145,626],[248,658],[372,660],
 [487,667],[620,666],[745,660],[854,659],[940,652],[969,555],[900,543],[969,482],[905,599],[845,582]];
vipSpots.forEach(([x,y],i)=>vip.push(fan(x,y,i,{scale:2.08,flip:i%2===0})));
// Identical identities and outfits in every room; the stage uses matching rear poses.
for(const cast of [outside,show,vip])cast.forEach((a,i)=>{a.who=sharedCast[i].who;a.phase=i*1.71;});
export const crowdCounts={outside:outside.length,show:show.length,vip:vip.length};
export function crowdActors(room,time,reduceMotion,player){const newcomers=room==='show'?Array.from({length:Math.min(10,Math.ceil((player.crewDelivered||0)/2))},(_,i)=>({...fan(282+(i%5)*120,548+Math.floor(i/5)*63,i,{scale:2.1,back:true,hands:true}),who:brennoFan(20+i)})):[];return [...({outside,show,vip}[room]||[]),...newcomers].map(a=>{
 const overlap=a.y>player.y-8&&a.y<player.y+105&&Math.abs(a.x-player.x)<65;
 const animated=!reduceMotion;return{...a,y:a.y+(animated?Math.sin(time/420+a.phase)*1.7:0),lean:animated?Math.sin(time/650+a.phase)*.018:0,alpha:overlap?.35:1};
});}
