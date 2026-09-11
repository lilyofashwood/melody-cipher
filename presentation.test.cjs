const test = require('node:test');
const assert = require('node:assert/strict');
const { letters, prose } = require('./presentation.js');

test('house lettering uses serif-bold vowels and sans-serif regular consonants', () => {
  assert.equal(letters('Abc E'), '\u{1d41a}\u{1d5bb}\u{1d5bc} \u{1d41e}');
  assert.equal(letters('Case stays readable').normalize('NFKC'), 'case stays readable');
});
test('garden heading voices are distinct and normalization-readable', () => {
  const voices = ['house', 'bold-script', 'bold-fraktur', 'monospace'].map(v => letters('Garden', v));
  assert.equal(new Set(voices).size, 4);
  for (const value of voices) assert.equal(value.normalize('NFKC'), 'garden');
});
test('pre-existing Unicode, combining sequences and emoji are untouched', () => {
  const text = '𝓵𝓲𝓵𝔂 👩🏽‍🔬 \u0301\uFEFF\u0000';
  assert.equal(letters(text), text);
});
test('quoted source, Unicode identifiers, URLs and filenames remain literal', () => {
  const raw = '"Case EXACT" “Original source” U+0344 https://example.test/Case?q=X README.md examples/sample.wav .json';
  assert.equal(prose(raw), raw);
  assert.equal(prose('Read README.md').normalize('NFKC'), 'read README.md');
});
test('presentation is idempotent and does not add combining mark channels', () => {
  const once = prose('A letter remembers its weather.');
  assert.equal(prose(once), once);
  assert(!/\p{M}/u.test(once));
});
