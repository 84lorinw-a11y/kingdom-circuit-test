export const roomStops={outside:['jay','grace','enter'],show:['merch','brenno','dj','marty','vip','outside'],vip:['photo','refresh','show']};
export const stopNames={jay:'Invite Jay',grace:'Invite Grace',enter:'Enter the show',merch:'Merch',brenno:'Brenno',dj:'Eli',marty:'Marty',vip:'VIP',outside:'Outside',photo:'VIP photo',refresh:'Take a breather',show:'Main stage'};
export const visitIds=[...new Set(Object.values(roomStops).flat())];
export function hasVisited(s,id){
 if(s.visited?.includes(id))return true;
 if(id==='jay'||id==='grace')return s.friends.includes(id);
 if(id==='enter'||id==='show')return s.entered;
 if(id==='outside')return true;
 if(id==='vip')return s.room==='vip'||s.photo;
 if(id==='photo')return s.photo;
 if(id==='merch')return !!s.merch;
 if(id==='dj')return s.eli;
 return (s.totals?.[id]||0)>0;
}
export function nextStop(s){
 if(s.room==='outside')return !s.friends.includes('jay')?'jay':!s.friends.includes('grace')?'grace':'enter';
 return roomStops[s.room].find(id=>!hasVisited(s,id))||null;
}
export function journeyObjective(s){
 const id=nextStop(s);
 if(id==='jay'||id==='grace')return `Next: ${stopNames[id]}. Tap them, then choose “Bring ${id==='jay'?'Jay':'Grace'} along”.`;
 if(s.room==='outside')return 'Crew ready! Tap Enter show below to head inside.';
 if(id)return `Next: ${stopNames[id]}. Tap its glowing circle or the button below.`;
 return s.room==='vip'?'Crew refreshed. Tap Main stage to play again.':'All stops visited! Replay any game or head to VIP.';
}
