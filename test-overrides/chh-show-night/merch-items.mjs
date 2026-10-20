export const merchItems=['Apollo bird tee','Concert tee','Not 4 Sale tee','Not 4 Sale hoodie','Not 4 Sale cap','Apollo red script tee','Apollo white logo tee','Not 4 $ale cream print tee'];
export function drawMerchItem(g,images,index,x,y,width,height){
 if(!Number.isInteger(index)||index<0||index>=merchItems.length)return;
 const img=index<3?images.merch:index<5?images.merchExtras:images.merchEli;if(!img)return;
 const col=index<3?index:index<5?index-3:index-5,cw=img.width/3,ch=img.height,scale=Math.min(width/cw,height/ch);
 g.drawImage(img,col*cw,0,cw,ch,x+(width-cw*scale)/2,y+(height-ch*scale)/2,cw*scale,ch*scale);
}
