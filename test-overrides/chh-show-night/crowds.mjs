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
[[423,536],[206,555],[856,548],[390,620],[614,548],[196,582],
 [610,604],[866,592],[247,627],[335,620],[505,626],[716,635],
 [785,625],[899,659],[170,654],[275,668],[395,653],[459,675],
 [575,638],[647,665],[762,674],[838,646],[944,626],[72,600],
 [340,659],[535,673],[701,668],[925,675],[215,661],[860,675]
].forEach(([x,y],i)=>show.push(fan(x,y,i,{scale:2.12+(i%3)*.04,back:true,hands:true})));
const vip=[];
[[62,315],[196,320],[264,322],[352,309],[98,435],[183,443],[261,445],[85,553],[173,566],[262,559],[52,635],[149,640],[258,642],[763,360],[829,358],[962,366],[765,475],[835,488],[968,478],[759,579],[835,590],[965,583],[803,648],[925,649]].forEach(([x,y],i)=>vip.push(fan(x,y,i,{scale:y<370?2.08:2.25,flip:i%2===0})));
vip.push(fan(361,630,24),fan(708,643,25),fan(331,493,26),fan(712,535,27),fan(930,650,28),fan(330,575,29));
// Identical identities and outfits in every room; the stage uses matching rear poses.
for(const cast of [outside,show,vip])cast.forEach((a,i)=>{a.who=sharedCast[i].who;a.phase=i*1.71;});
export const crowdCounts={outside:outside.length,show:show.length,vip:vip.length};
export function crowdActors(room,time,reduceMotion,player){return({outside,show,vip}[room]||[]).map(a=>{
 const overlap=a.y>player.y-8&&a.y<player.y+105&&Math.abs(a.x-player.x)<65;
 const animated=!reduceMotion;return{...a,y:a.y+(animated?Math.sin(time/420+a.phase)*1.7:0),lean:animated?Math.sin(time/650+a.phase)*.018:0,alpha:overlap?.35:1};
});}
