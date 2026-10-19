export const scoreColumns=[['rank','#'],['nickname','Player'],['eli','Eli'],['joz','Joz'],['steven','Steven'],['chamblissnation','Merch'],['journey','Journey'],['total','Total']];
export function createScoreTable(label){
 const wrap=document.createElement('div');wrap.className='score-table-wrap';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label',label);
 const table=document.createElement('table');table.className='score-table';table.setAttribute('role','table');const caption=document.createElement('caption');caption.textContent=label;table.append(caption);
 const head=document.createElement('thead'),tr=document.createElement('tr');head.setAttribute('role','rowgroup');tr.setAttribute('role','row');
 for(const [id,label] of scoreColumns){const th=document.createElement('th');th.scope='col';th.setAttribute('role','columnheader');th.textContent=label;if(id==='chamblissnation')th.setAttribute('aria-label','Chamblissnation merch');if(id==='total')th.className='score-final';tr.append(th);}head.append(tr);
 const body=document.createElement('tbody');body.setAttribute('role','rowgroup');table.append(head,body);wrap.append(table);
 return {element:wrap,append(rows){for(const row of rows){const tr=document.createElement('tr');tr.setAttribute('role','row');for(const [id,label] of scoreColumns){const cell=document.createElement(id==='nickname'?'th':'td');cell.dataset.label=label;cell.dataset.score=id;cell.setAttribute('role',id==='nickname'?'rowheader':'cell');if(id==='nickname'){cell.scope='row';cell.textContent=row.nickname||'Player';}else cell.textContent=Number(row[id]||0).toLocaleString();if(id==='total')cell.className='score-final';tr.append(cell);}body.append(tr);}}};
}
