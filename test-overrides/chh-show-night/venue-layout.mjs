// Shared floor positions keep portals, walking destinations and return points aligned.
export const andrewSpot={id:'andrew-prim',x:910,y:504,label:'Andrew Prim',tag:'ANDREW PRIM · PLAY',action:'artist',radius:24,labelY:547};
export const vipSpot={id:'vip',x:210,y:480,label:'VIP',tag:'← VIP',action:'vip'};
export const vipReturn={x:235,y:505};
export const roomMusicEnabled=({room,profileReady,entryPending,dialogOpen,hidden,soundOn})=>
 room==='show'&&profileReady&&!entryPending&&!dialogOpen&&!hidden&&soundOn;
