'use strict';
(() => {
  const key='kc-fan-test-events-v1';
  function records(){try{return JSON.parse(sessionStorage.getItem(key))||[];}catch(_){return [];}}
  function render(){
    const list=records(),summary=document.querySelector('#analytics-summary'),events=document.querySelector('#analytics-events');summary.replaceChildren();events.replaceChildren();
    const metrics=[['Artist views','artist_view'],['Show views','show_view'],['Ticket referrals','ticket_referral'],['Instagram referrals','instagram_referral'],['Panel impressions','empty_shows_impression'],['Panel clicks','empty_shows_click'],['Successful submissions','form_success'],['Zero-result searches','search_results']];
    for(const[label,type]of metrics){const p=document.createElement('p'),strong=document.createElement('strong');strong.textContent=list.filter(e=>e.event===type&&(label!=='Zero-result searches'||e.result_count===0)).length;p.append(strong,document.createTextNode(label));summary.append(p);}
    for(const row of list.slice().reverse()){const details=document.createElement('details'),title=document.createElement('summary'),pre=document.createElement('pre');title.textContent=`${new Date(row.time).toLocaleTimeString()} · ${row.event} · ${row.viewport}`;pre.textContent=JSON.stringify(row,null,2);details.append(title,pre);events.append(details);}
    document.querySelector('#analytics-status').textContent=`${list.length} test events. Stored in this tab only; most recent 500 retained. No form contents are recorded.`;
  }
  document.querySelector('#refresh-events').addEventListener('click',render);
  document.querySelector('#clear-events').addEventListener('click',()=>{sessionStorage.removeItem(key);sessionStorage.removeItem('kc-fan-empty-journey-v1');render();});
  document.querySelector('#export-events').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(records(),null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='kingdom-circuit-test-events.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
  render();
})();
