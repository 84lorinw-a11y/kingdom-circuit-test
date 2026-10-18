export const avatars=[
 {id:'red',sprite:'player',label:'Red hoodie',color:'#ff7555'},
 {id:'teal',sprite:'crowd-vip:32',label:'Blue soul',color:'#53ded1'},
 {id:'blonde',sprite:'crowd-vip:34',label:'Lilac crew',color:'#c8a3f6'},
 {id:'blue',sprite:1,label:'Blue crew',color:'#71a6ff'},
 {id:'pink',sprite:5,label:'Golden hour',color:'#f584cf'},
 {id:'sunset',sprite:4,label:'Sunday cream',color:'#ed883c'}
];
export const avatarFor=s=>avatars.find(a=>a.id===s.avatar)||avatars[0];
export function playerName(value){return String(value??'').replace(/[\u0000-\u001f\u007f]/g,'').trim().slice(0,18);}
