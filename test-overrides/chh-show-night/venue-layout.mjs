// Shared floor positions keep portals, walking destinations and return points aligned.
export const andrewSpot={id:'andrew-prim',x:910,y:504,label:'Andrew Prim',tag:'ANDREW PRIM · PLAY',action:'artist',radius:24,labelY:547};
export const vipSpot={id:'vip',x:985,y:582,label:'VIP',tag:'VIP →',action:'vip',labelY:614,radius:26};
export const merchSpot={id:'merch',x:105,y:407,label:'Merch',tag:'MERCH',action:'merch'};
export const vipReturn={x:950,y:595};
export const roomMusicEnabled=({room,profileReady,entryPending,dialogOpen,hidden,soundOn})=>
 room==='show'&&profileReady&&!entryPending&&!dialogOpen&&!hidden&&soundOn;
