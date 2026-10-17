const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {searchMatch, weekEnd, dateMatch, matches, artistMatches} = require('../test-overrides/fan-discovery.js');
test('search handles punctuation, accents and artist-name spacing', () => {
  for (const [hay,q] of [['626authentic','626 Authentic'],['Ky’Aliyah','kyaliyah'],['ÉGR — Live','egr live'],['nobigdyl.','nobigdyl']]) assert.equal(searchMatch(hay,q),true);
  assert.equal(searchMatch('Dallas','Houston'),false);
});
test('this week ends Sunday, rolls at Monday and handles year boundaries', () => {
  assert.equal(weekEnd('2026-10-15'),'2026-10-18');
  assert.equal(weekEnd('2026-10-18'),'2026-10-18');
  assert.equal(weekEnd('2026-10-19'),'2026-10-25');
  assert.equal(weekEnd('2026-12-31'),'2027-01-03');
});
test('week and coming-up do not overlap; expired and multi-day shows are truthful', () => {
  assert.equal(dateMatch('2026-10-17','','week','2026-10-15'),true);
  assert.equal(dateMatch('2026-10-19','','week','2026-10-15'),false);
  assert.equal(dateMatch('2026-10-19','','upcoming','2026-10-15'),true);
  assert.equal(dateMatch('2026-10-18','','upcoming','2026-10-15'),false);
  assert.equal(dateMatch('2026-10-25','','upcoming','2026-10-15'),true);
  assert.equal(dateMatch('2026-10-26','','upcoming','2026-10-15'),false);
  assert.equal(dateMatch('2026-10-18','2026-10-20','upcoming','2026-10-15'),false);
  assert.equal(dateMatch('2026-10-14','2026-10-18','weekend','2026-10-17'),true);
  assert.equal(dateMatch('2026-10-16','','weekend','2026-10-17'),false);
  assert.equal(dateMatch('2026-10-14','','all','2026-10-15'),false);
});
test('next-week dates roll across the year boundary and never broaden for empty filters', () => {
  assert.equal(dateMatch('2027-01-04','','upcoming','2026-12-31'),true);
  assert.equal(dateMatch('2027-01-10','','upcoming','2026-12-31'),true);
  assert.equal(dateMatch('2027-01-03','','upcoming','2026-12-31'),false);
  assert.equal(dateMatch('2027-01-11','','upcoming','2026-12-31'),false);
  const show = {date:'2026-10-23',state:'TX',artists:'guest',search:'Guest Dallas'};
  assert.equal(matches(show,{q:'guest',state:'TX',dates:'upcoming'},'2026-10-17'),true);
  assert.equal(matches(show,{state:'FL',dates:'upcoming'},'2026-10-17'),false);
  assert.equal(matches({...show,date:'2026-10-30'},{state:'TX',dates:'upcoming'},'2026-10-17'),false);
});
test('all filters combine, and a zero-results state never broadens to national', () => {
  const c = {date:'2026-10-17',state:'TX',artists:'626authentic|guest',type:'concert',search:'626authentic Dallas'};
  assert.equal(matches(c,{q:'626 Authentic',state:'TX',dates:'week'},'2026-10-15'),true);
  assert.equal(matches(c,{state:'Maine'},'2026-10-15'),false);
  assert.equal(matches(c,{artist:'unknown'},'2026-10-15'),false);
});
test('artist with no shows is still a searchable profile', () => {
  const artists = [{name:'Caleb Gordon',href:'/artists/caleb-gordon/',count:0},{name:'Other',count:2}];
  assert.equal(artistMatches(artists,'caleb gordon')[0].count,0);
  assert.deepEqual(artistMatches(artists,''),[]);
});

function renderProfile(artist) {
  const document = {
    readyState: 'loading', addEventListener() {},
    createElement(tag) {
      return {tag, children: [], style: {}, attributes: {}, listeners: {},
        append(...nodes) { nodes.forEach(n => { n.parent = this; this.children.push(n); }); },
        setAttribute(key,value) { this.attributes[key] = value; },
        addEventListener(name,fn) { this.listeners[name] = fn; },
        remove() { this.parent.children = this.parent.children.filter(n => n !== this); },
      };
    },
  };
  const context = {document, module:{exports:{}}};
  vm.runInNewContext(fs.readFileSync(require.resolve('../test-overrides/fan-discovery.js'),'utf8'),context);
  return context.module.exports.profileLink(artist);
}
test('artist search result is one profile link with a circular-photo hook and full copy', () => {
  const href = '/kingdom-circuit-test/artists/hulvey/';
  const src = '/kingdom-circuit-test/assets/hulvey-320.webp';
  const link = renderProfile({name:'Hulvey',href,count:2,portrait:{src,position:'50% 30%'}});
  assert.equal(link.href,href);
  assert.equal(link.className,'kc-profile-link');
  const [avatar,copy,action] = link.children;
  assert.equal(avatar.className,'kc-profile-avatar');
  assert.equal(avatar.attributes['aria-hidden'],'true');
  const photo = avatar.children.find(n=>n.tag==='img');
  assert.equal(photo.src,src);
  assert.equal(photo.alt,'');
  assert.equal(photo.style.objectPosition,'50% 30%');
  assert.equal(photo.width,72);
  assert.equal(copy.children[0].textContent,'Hulvey');
  assert.match(copy.children[1].textContent,/2 upcoming shows/);
  assert.equal(action.textContent,'View artist profile');
});
test('broken or missing search portrait keeps initials and the correct zero-show profile', () => {
  const artist = {name:'Caleb Gordon',href:'/kingdom-circuit-test/artists/caleb-gordon/',count:0};
  for (const portrait of [undefined,{src:'https://external.test/photo.jpg'},{src:'/kingdom-circuit-test/assets/photo.webp'}]) {
    const link = renderProfile({...artist,portrait});
    const avatar = link.children[0];
    const photo = avatar.children.find(n=>n.tag==='img');
    if (photo) photo.listeners.error();
    assert.equal(avatar.children.length,1);
    assert.equal(avatar.children[0].textContent,'CG');
    assert.equal(link.href,artist.href);
    assert.match(link.children[1].children[1].textContent,/No upcoming dates listed/);
  }
});
test('artist portrait does not allow an external profile destination', () => {
  assert.equal(renderProfile({name:'Hulvey',href:'https://external.test/artists/hulvey/'}),null);
});
