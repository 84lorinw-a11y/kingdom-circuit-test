// Deliberate crowd placement leaves the entrance, shop, stage center, and photo lane readable.
const fan=(x,y,i,extra={})=>({x,y,who:null,scale:2.15+(i%3)*.05,ambient:true,phase:i*1.71,flip:i%3===0,...extra});
const outside=[];
// Friends by the riverside and waiting around the benches.
[[75,345],[137,350],[245,348],[306,351],[85,490],[153,493],[260,470],[322,472],[58,570],[115,570],[68,642],[136,640],[270,649],[342,647],[408,649]].forEach(([x,y],i)=>outside.push(fan(x,y,i,{scale:y<400?2.08:2.25})));
// A busy queue on each side of the open entrance.
[[633,368],[860,371],[648,419],[873,422],[631,475],[878,476],[657,532],[890,532],[659,589],[883,589],[965,602],[961,544],[967,653]].forEach(([x,y],i)=>outside.push(fan(x,y,i+2,{scale:y<430?2.12:2.25})));
outside.push(fan(459,650,28),fan(946,490,29));
const show=[];
// An uneven crowd across the floor, with a few fans nearer the stage.
// Positions account for raised arms and bodies, keeping the floor circles clear.
[[423,536],[206,555],[856,548],[390,620],[614,548],[196,582],
 [610,604],[866,592],[247,627],[335,620],[505,626],[716,635],
 [785,625],[899,659],[170,654],[275,668],[395,653],[459,675],
 [575,638],[647,665],[762,674],[838,646],[944,626],[72,600],
 [340,659],[535,673],[701,668],[925,675],[215,661],[860,675],
 [628,627],[308,640],[464,633],[560,664]].forEach(([x,y],i)=>show.push(fan(x,y,i,{scale:2.12+(i%3)*.04,back:true,hands:true})));
const vip=[];
[[62,315],[196,320],[264,322],[352,309],[98,435],[183,443],[261,445],[85,553],[173,566],[262,559],[52,635],[149,640],[258,642],[763,360],[829,358],[962,366],[765,475],[835,488],[968,478],[759,579],[835,590],[965,583],[803,648],[925,649]].forEach(([x,y],i)=>vip.push(fan(x,y,i,{scale:y<370?2.08:2.25,flip:i%2===0})));
vip.push(fan(361,630,24),fan(708,643,25));
// Every room uses a separate cast; no cell is reused within or between scenes.
for(const [room,cast] of Object.entries({outside,show,vip}))cast.forEach((a,i)=>{a.who=`crowd-${room}:${i}`;a.phase=i*1.71;});
export const crowdCounts={outside:outside.length,show:show.length,vip:vip.length};
const avatarLookalikes={gold:[0,31],blue:[1,34],beanie:[2,33],teal:[3,30],pink:[5,31],sunset:[4,32],blonde:[6,32]};
export function crowdActors(room,time,reduceMotion,player){return({outside,show,vip}[room]||[]).map(a=>{
 const overlap=a.y>player.y-8&&a.y<player.y+105&&Math.abs(a.x-player.x)<65;
 const swap=room!=='show'&&avatarLookalikes[player.avatar];const who=swap&&a.who===`crowd-${room}:${swap[0]}`?`crowd-${room}:${swap[1]}`:a.who;
 const animated=!reduceMotion;return{...a,who,y:a.y+(animated?Math.sin(time/420+a.phase)*1.7:0),lean:animated?Math.sin(time/650+a.phase)*.018:0,alpha:overlap?.35:1};
});}
