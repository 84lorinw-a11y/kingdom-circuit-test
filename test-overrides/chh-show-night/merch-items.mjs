export const merchItems=['Concert tee','Apollo red script tee','Apollo white logo tee','Not 4 $ale cream print tee'];
export function drawMerchItem(g,images,index,x,y,width,height){
 if(!Number.isInteger(index)||index<0||index>=merchItems.length)return;
 const img=index===0?images.merch:images.merchEli;if(!img)return;
 const col=index===0?1:index-1,cw=img.width/3,ch=img.height,scale=Math.min(width/cw,height/ch);
 g.drawImage(img,col*cw,0,cw,ch,x+(width-cw*scale)/2,y+(height-ch*scale)/2,cw*scale,ch*scale);
}
