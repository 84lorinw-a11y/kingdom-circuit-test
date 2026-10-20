// Reverse three-quarter booth view; retain the approved Andrew cutout.
export const producerStation={x:922,y:535,prop:'producer-station'};
export function drawProducerStation(g,{x,y}=producerStation,art={}){
 if(!art.andrewBooth)return;
 const img=art.andrewBooth;
 g.drawImage(img,x-122,y-150,220,220*img.height/img.width);
}
