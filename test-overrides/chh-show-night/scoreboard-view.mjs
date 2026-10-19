export const scoreColumns=[['nickname','Player'],['total','Total']];
export function createScoreTable(label){
 const wrap=document.createElement('div');wrap.className='score-table-wrap';wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label',label);
 const table=document.createElement('table');table.className='score-table';table.setAttribute('aria-label',label);
 const head=document.createElement('thead'),heading=document.createElement('tr');
 for(const [,label] of scoreColumns){const cell=document.createElement('th');cell.scope='col';cell.textContent=label;heading.append(cell);}
 head.append(heading);const body=document.createElement('tbody');table.append(head,body);wrap.append(table);
 return {element:wrap,append(rows){for(const row of rows){
  const tr=document.createElement('tr'),name=document.createElement('th'),total=document.createElement('td');
  name.scope='row';name.textContent=row.nickname||'Player';total.textContent=Number(row.total||0).toLocaleString();
  tr.append(name,total);body.append(tr);
 }}};
}
