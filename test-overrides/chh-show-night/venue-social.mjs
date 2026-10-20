export const snacks=['Popcorn','Pretzel','Fruit cup'];
export const drinks=['Water','Lemonade','Soda'];
export function drawSnackBar(g){
 g.save();g.fillStyle='#0d0f12';g.fillRect(731,268,263,31);g.fillStyle='#ddd6c6';g.font='bold 15px sans-serif';g.textAlign='center';g.fillText('SNACKS + COLD DRINKS',863,289);
 // Serving island, stocked shelves and ice cooler.
 g.fillStyle='#292a2d';g.fillRect(726,363,275,63);g.fillStyle='#777167';g.fillRect(718,357,291,8);g.strokeStyle='#55565a';g.lineWidth=2;g.strokeRect(726,365,275,61);
 g.fillStyle='#d1ab7b';g.fillRect(742,329,30,28);g.fillStyle='#f3dfb5';for(let j=0;j<9;j++){g.beginPath();g.arc(747+(j%3)*8,331-Math.floor(j/3)*5,5,0,7);g.fill();}
 g.fillStyle='#a4a19b';g.fillRect(785,349,37,6);g.strokeStyle='#bf884b';g.lineWidth=5;for(let i=0;i<3;i++){g.beginPath();g.ellipse(801,339-i*5,12,6,-.2,0,7);g.stroke();g.beginPath();g.moveTo(792,333-i*5);g.lineTo(810,344-i*5);g.stroke();}
 g.fillStyle='#c9bfa2';g.beginPath();g.ellipse(852,350,21,6,0,0,7);g.fill();g.fillRect(833,338,38,12);for(let i=0;i<9;i++){g.fillStyle=['#c56949','#c0b464','#799765'][i%3];g.beginPath();g.arc(838+(i%4)*9,338-Math.floor(i/4)*6,5,0,7);g.fill();}
 for(let i=0;i<5;i++){const x=889+i*19;g.fillStyle=i<2?'#7fa7b2':i<4?'#c3aa67':'#9d6964';g.fillRect(x,319,13,37);g.fillStyle='#c1c4b7';g.fillRect(x+3,313,7,7);g.fillStyle='#e0dfcc';g.fillRect(x+1,333,11,11);}
 g.fillStyle='#cfc5af';g.font='9px monospace';g.fillText('POPCORN · PRETZELS · FRUIT',809,391);g.fillText('WATER · LEMONADE · SODA',881,411);g.restore();
}
export function drawCypher(g,time,reduced,active=false){
 g.save();g.fillStyle='#19181c';g.beginPath();g.ellipse(108,577,86,35,0,0,7);g.fill();g.strokeStyle='#b27664';g.lineWidth=2;g.stroke();
 g.strokeStyle='#777';g.lineWidth=3;g.beginPath();g.moveTo(108,578);g.lineTo(108,482);g.stroke();g.fillStyle='#24262a';g.fillRect(104,477,8,19);g.fillStyle='#94948c';g.beginPath();g.ellipse(108,478,6,8,0,0,7);g.fill();g.strokeStyle='#515157';g.beginPath();g.moveTo(86,582);g.lineTo(108,575);g.lineTo(130,582);g.stroke();
 g.fillStyle='#0c0d10';g.fillRect(35,594,148,24);g.fillStyle=active?'#eabf80':'#dfd5c5';g.font='bold 12px monospace';g.textAlign='center';g.fillText(active?'PASS THE MIC!':'THE CYPHER',109,610);g.restore();
}
