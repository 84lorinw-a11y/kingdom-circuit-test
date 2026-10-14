const test = require('node:test');
const assert = require('node:assert/strict');
const {normalize, activeOn, matches} = require('../test-overrides/national-discovery.js');
const card = {date:'2026-10-16', endDate:'2026-10-18', search:'Artist – Live in Dallas', artists:'artist|guest', state:'TX', type:'concert'};
test('multi-day shows remain available through their final date', () => {
  assert.equal(activeOn(card,'2026-10-18'),true);
  assert.equal(activeOn(card,'2026-10-19'),false);
});
test('all weekend filters combine without changing the underlying data', () => {
  assert.equal(matches(card,{q:'DALLAS',artist:'guest',state:'TX',type:'concert'},'2026-10-16'),true);
  for (const filter of [{state:'FL'},{artist:'other'},{type:'festival'},{q:'Miami'}]) {
    assert.equal(matches(card,filter,'2026-10-16'),false);
  }
  assert.equal(matches(card,{},'2026-10-19'),false);
});
test('cleared filters show every non-expired record', () => {
  assert.equal(matches(card,{q:'',artist:'',state:'',type:''},'2026-10-18'),true);
});
test('search handles accents and whitespace', () => {
  assert.equal(normalize('  ÉGR  '),'egr');
});
