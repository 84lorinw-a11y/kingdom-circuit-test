// Shared floor positions keep portals, walking destinations and return points aligned.
export const andrewSpot={id:'andrew-prim',x:910,y:486,label:'Andrew Prim',tag:'ANDREW PRIM\nPLAY',action:'artist',radius:24,labelX:980,labelY:397};
export const vipSpot={id:'vip',x:985,y:582,label:'VIP',tag:'VIP →',action:'vip',labelY:614,radius:18};
export const merchSpot={id:'merch',x:172,y:625,label:'Merch',tag:'MERCH',action:'merch'};
export const vipReturn={x:950,y:595};
export const roomMusicEnabled=({room,profileReady,entryPending,dialogOpen,hidden,soundOn})=>
 room==='show'&&profileReady&&!entryPending&&!dialogOpen&&!hidden&&soundOn;
