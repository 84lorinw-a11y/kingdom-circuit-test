// Angled flight-case booth; Andrew's approved cutout is drawn behind the console.
export const producerStation={x:922,y:535,prop:'producer-station'};
export function drawProducerStation(g,{x,y}=producerStation,art={}){
 if(!art.venueProps)return;
 const img=art.venueProps;g.save();g.drawImage(img,0,0,1110,img.height,x-122,y-191,228,210);
 g.restore();
}
