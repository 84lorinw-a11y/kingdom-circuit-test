export const merchItems=['Heart badge tee','Concert tee','Not 4 Sale tee','Not 4 Sale hoodie','Not 4 Sale cap','Apollo canvas tote'];
export function drawMerchItem(g,images,index,x,y,width,height){
 const img=index<3?images.merch:images.merchExtras;if(!img)return;
 const col=index%3,cw=img.width/3,ch=img.height,scale=Math.min(width/cw,height/ch);
 g.drawImage(img,col*cw,0,cw,ch,x+(width-cw*scale)/2,y+(height-ch*scale)/2,cw*scale,ch*scale);
}
