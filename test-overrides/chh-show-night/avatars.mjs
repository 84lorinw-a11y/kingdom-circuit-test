export const avatars=[
 {id:'red',sprite:'player',label:'Red hoodie',color:'#ff7555'},
 {id:'gold',sprite:0,label:'Golden hour',color:'#eeb542'},
 {id:'blue',sprite:1,label:'Blue crew',color:'#71a6ff'},
 {id:'beanie',sprite:2,label:'Beat keeper',color:'#ffa346'},
 {id:'teal',sprite:3,label:'Fresh mint',color:'#53ded1'},
 {id:'pink',sprite:5,label:'Joy bringer',color:'#f584cf'},
 {id:'sunset',sprite:4,label:'Sunset crew',color:'#ed883c'},
 {id:'blonde',sprite:'blonde-fan',label:'Sunday blue',color:'#82adf4'}
];
export const avatarFor=s=>avatars.find(a=>a.id===s.avatar)||avatars[0];
export function playerName(value){return String(value??'').replace(/[\u0000-\u001f\u007f]/g,'').trim().slice(0,18);}
