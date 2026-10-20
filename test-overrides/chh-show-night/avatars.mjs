export const avatars=[
 // Keep saved choice IDs so an existing night retains its progress.
 {id:'red',sprite:'ref-player:0',label:'Green cap',color:'#72ad89'},
 {id:'teal',sprite:'ref-player:1',label:'Bowie 83',color:'#cbbd96'},
 {id:'blonde',sprite:'ref-player:2',label:'Striped polo',color:'#5da989'},
 {id:'blue',sprite:'ref-player:3',label:'Graphic tee',color:'#d6b65f'},
 {id:'pink',sprite:'ref-player:4',label:'Pink top',color:'#ed79ad'},
 {id:'sunset',sprite:'ref-player:5',label:'Blue jersey',color:'#6ba3ed'}
];
export const avatarFor=s=>avatars.find(a=>a.id===s.avatar)||avatars[0];
export function playerSpritePose(who,{peace=false,back=false,hands=false}={}){
 const match=typeof who==='string'&&/^ref-player:([0-5])$/.exec(who);
 if(!match)return null;
 const index=Number(match[1]);
 return {atlas:index<3?'playersA':'playersB',cell:index%3+(peace?6:back||hands?3:0),height:!peace&&(back||hands)?1.18:1};
}
export function playerName(value){return String(value??'').replace(/[\u0000-\u001f\u007f]/g,'').trim().slice(0,18);}
