const test = require('node:test');
const assert = require('node:assert/strict');
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
  assert.equal(dateMatch('2026-10-14','2026-10-18','weekend','2026-10-17'),true);
  assert.equal(dateMatch('2026-10-16','','weekend','2026-10-17'),false);
  assert.equal(dateMatch('2026-10-14','','all','2026-10-15'),false);
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
