// Bound image decoding so a stalled request can offer a retry instead of hanging.
export function loadImage(src,{timeoutMs=90000,imageFactory=()=>new Image()}={}){
 return new Promise((resolve,reject)=>{
  const image=imageFactory();
  const timer=setTimeout(()=>{image.src='';reject(Error('Image took too long to load'));},timeoutMs);
  image.src=src;
  Promise.resolve().then(()=>image.decode()).then(()=>{
   if(!image.width||!image.height)throw Error('Image is empty');
   clearTimeout(timer);resolve(image);
  }).catch(error=>{clearTimeout(timer);reject(error);});
 });
}
