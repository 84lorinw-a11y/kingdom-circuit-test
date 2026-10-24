const test=require('node:test'),assert=require('node:assert/strict');
const {STORE,TEST_GA,testDestination,safeText,clean,today,countShows,tracker,attemptState}=require('../test-overrides/fan-engagement.js');
function storage(){const s=new Map();return{getItem:k=>s.get(k),setItem:(k,v)=>s.set(k,v)};}
test('count matches inclusive end dates, deduplicates events and crosses Pacific midnight',()=>{
 const shows=[{path:'/a',date:'2026-10-23'},{path:'/b',date:'2026-10-21',end:'2026-10-24'},{path:'/c',date:'2027-01-02'},{path:'/a',date:'2026-10-23'}];
 assert.equal(today(new Date('2026-10-24T06:59:59Z')),'2026-10-23');assert.equal(today(new Date('2026-10-24T07:00:00Z')),'2026-10-24');
 assert.equal(countShows(shows,'2026-10-23'),3);assert.equal(countShows(shows,'2026-10-24'),2);assert.equal(countShows(shows,'2026-10-25'),1);
 assert.equal(countShows([...shows,{path:'/new',date:'2026-11-01'}],'2026-10-25'),2);
});
test('test events go only to the Google test property, without a local event log or personal fields',()=>{
 const calls=[],s=storage();const track=tracker({mode:'test',measurementId:TEST_GA,pageType:'artist'},{storage:s,path:'/kingdom-circuit-test/artists/mike/',host:'84lorinw-a11y.github.io',width:()=>390,gtag:(...args)=>calls.push(args)});
 track('artist_view',{artist_name:'Mike Malagies',email:'private@example.com',search_term:'contact@example.com',form_data:'secret',page_location:'https://site/?email=secret'});
 assert.equal(s.getItem(STORE),undefined);assert.equal(calls.length,1);const row=calls[0][2];assert.equal(row.send_to,TEST_GA);assert.equal(row.debug_mode,true);assert.equal(row.search_term,'[redacted]');assert.equal(row.viewport,'mobile');assert.equal(row.email,undefined);assert.equal(row.page_location,undefined);assert.equal(row.form_data,undefined);
 track('unknown_event');assert.equal(calls.length,1);
});
test('test delivery rejects wrong measurement IDs, hosts, roots and local previews',()=>{
 let calls=0;
 for(const[host,path,id]of[['kingdomcircuit.com','/kingdom-circuit-test/',TEST_GA],['localhost','/kingdom-circuit-test/',TEST_GA],['84lorinw-a11y.github.io','/another-repo/',TEST_GA],['84lorinw-a11y.github.io','/kingdom-circuit-test/','G-N2KK9XF4TJ'],['84lorinw-a11y.github.io','/kingdom-circuit-test/',undefined]]) {
  const config={mode:'test',measurementId:id},env={storage:storage(),host,path,width:()=>390,gtag:()=>calls++};assert.equal(testDestination(config,env),false);tracker(config,env)('artist_view');
 }
 assert.equal(calls,0);
});
test('production adapter requires both explicit production mode and production hostname',()=>{
 let calls=[];for(const[mode,host]of[['test','kingdomcircuit.com'],['production','localhost'],['production','84lorinw-a11y.github.io'],['production','kingdomcircuit.com']]){
 tracker({mode,pageType:'show'},{storage:storage(),path:'/event/a/',host,width:()=>1400,gtag:(...a)=>calls.push(a)})('ticket_referral',{show_name:'A',destination_host:'eventbrite.com'});
 }
 assert.equal(calls.length,1);assert.equal(calls[0][1],'ticket_referral');assert.equal(calls[0][2].transport_type,'beacon');
});
test('storage rejection cannot interrupt navigation or form completion',()=>{
 assert.doesNotThrow(()=>tracker({mode:'test'},{storage:{getItem(){throw Error()},setItem(){throw Error()}},path:'/',width:()=>400})('form_success',{form_type:'new_show'}));
});
test('submission requires an attempt and a server acknowledgment; duplicates suppressed, retries work',()=>{
 const f={},s=attemptState();assert.equal(s.finish(f,'success'),null);assert.ok(s.start(f,'show_correction'));assert.equal(s.start(f,'show_correction'),null);
 assert.ok(s.attempt(f,'show_correction'));assert.equal(s.attempt(f,'new_show'),null);assert.equal(s.finish(f,'sending'),null);
 assert.deepEqual(s.finish(f,'error'),{type:'show_correction',status:'error'});assert.equal(s.finish(f,'success'),null);
 assert.ok(s.attempt(f,'show_correction'));assert.deepEqual(s.finish(f,'success'),{type:'show_correction',status:'success'});assert.equal(s.finish(f,'success'),null);
});
test('contact details, query URLs and long input cannot enter analytics',()=>{
 for(const input of ['a@b.com','https://site/?token=private','(555) 123-4567','www.example.com'])assert.equal(safeText(input),'[redacted]');
 assert.equal(safeText('Hulvey'),'Hulvey');assert.equal(safeText('x'.repeat(300)).length,100);assert.deepEqual(clean({raw_error:'secret',result_count:0}),{result_count:0});
});

test('safe public hosts and dated event paths survive sanitization, query strings do not',()=>{
 assert.deepEqual(clean({destination_host:'www.miketeezymusic.com',page_path:'/event/show-2026-10-24/?email=secret'}),{destination_host:'www.miketeezymusic.com',page_path:'/event/show-2026-10-24/'});
});
