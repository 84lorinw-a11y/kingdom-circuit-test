export const snacks=['Popcorn','Pretzel','Fruit cup'];
export const drinks=['Water','Lemonade','Soda'];
export function drawSnackBar(g){
 // The photographed-style food and drinks live on the existing draped table.
 g.save();g.fillStyle='#c5bca9';g.globalAlpha=.8;g.font='bold 10px sans-serif';g.textAlign='center';g.fillText('SNACKS + COLD DRINKS',891,270);g.restore();
}
