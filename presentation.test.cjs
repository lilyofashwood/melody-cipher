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

// Optional development dependency: NODE_PATH can point at the installed Playwright package.
let chromium;
try { ({ chromium } = require('playwright')); } catch {}
test('authored hints and dynamic UI dress up while literals and accessible names stay exact',
  { skip: !chromium && 'Install Playwright to run browser presentation checks' }, async () => {
    const browser = await chromium.launch({
      headless: true,
      ...(process.env.GARDEN_CHROME_BIN ? { executablePath: process.env.GARDEN_CHROME_BIN } : {})
    });
    try {
      const page = await browser.newPage();
      await page.setContent(`<!doctype html><title data-garden-title>Garden workshop</title>
        <label for="message">Exact message</label>
        <input id="message" data-garden-placeholder placeholder="Write a little rain" value="Case EXACT é 👩‍🔬">
        <input id="unowned" placeholder="Literal unowned hint" value="Unchanged">
        <button id="action">Open the door</button>
        <select id="mode"><option>CaseSensitiveMode</option><option value="wire-v1">Historical mode</option></select>
        <p id="status">Ready for the garden</p>
        <div data-literal><h2 id="source-title">My EXACT Title</h2><p id="source">Case EXACT é 👩‍🔬</p>
          <input id="raw-hint" data-garden-placeholder placeholder="Raw EXACT hint"></div>
        <pre id="receipt">{"Case":"EXACT","wire":"é"}</pre>
        <code id="code">const Case = "EXACT";</code>
        <a id="link" href="/download/Case.json">Download</a>`);
      await page.addScriptTag({ path: require('node:path').join(__dirname, 'presentation.js') });
      assert.equal(await page.title(), prose('Garden workshop'));
      assert.equal(await page.locator('#message').getAttribute('placeholder'), prose('Write a little rain'));
      assert.equal(await page.locator('#message').inputValue(), 'Case EXACT é 👩‍🔬');
      assert.equal(await page.locator('#message').getAttribute('aria-label'), 'Exact message');
      assert.equal(await page.locator('#unowned').getAttribute('placeholder'), 'Literal unowned hint');
      assert.equal(await page.locator('#raw-hint').getAttribute('placeholder'), 'Raw EXACT hint');
      assert.equal(await page.locator('#source-title').textContent(), 'My EXACT Title');
      assert.equal(await page.locator('#source').textContent(), 'Case EXACT é 👩‍🔬');
      assert.equal(await page.locator('#receipt').textContent(), '{"Case":"EXACT","wire":"é"}');
      assert.equal(await page.locator('#code').textContent(), 'const Case = "EXACT";');
      assert.equal(await page.locator('#link').getAttribute('href'), '/download/Case.json');
      assert.equal(await page.locator('#mode').inputValue(), 'CaseSensitiveMode');
      await page.locator('#mode').selectOption('wire-v1');
      assert.equal(await page.locator('#mode').inputValue(), 'wire-v1');
      await page.evaluate(() => {
        document.querySelector('#status').textContent = 'Rejected: choose a waveform';
        document.querySelector('#message').placeholder = 'Try another message';
        document.querySelector('#source').textContent = 'NEW Literal U+0344';
        document.querySelector('#action').textContent = 'Try again';
      });
      await page.waitForFunction(() => !/[A-Za-z]/.test(document.querySelector('#status').textContent));
      assert.equal(await page.locator('#message').getAttribute('placeholder'), prose('Try another message'));
      assert.equal(await page.locator('#action').getAttribute('aria-label'), 'Try again');
      assert.equal(await page.locator('#source').textContent(), 'NEW Literal U+0344');
    } finally { await browser.close(); }
  });

test('variant links select only declared options and preserve form payloads',
  { skip: !chromium && 'Install Playwright to run variant-link checks' }, async () => {
    const browser = await chromium.launch({ headless: true,
      ...(process.env.GARDEN_CHROME_BIN ? { executablePath: process.env.GARDEN_CHROME_BIN } : {}) });
    try {
      const page = await browser.newPage();
      await page.route(/^https?:/, route => route.abort());
      const { pathToFileURL } = require('node:url');
      const path = require('node:path');
      for (const [file, id, fallback, modes] of [["index.html","cipherSelect","chromatic",["chromatic","octatonicHalfWhole","locrianPlus2","dorianFlat2","diminishedOctatonic","bebopMixolydian"]],["studio.html","mode","nocturne",["nocturne","luminous"]],["studio.html","phrasing","bloom",["bloom","baseline"]]]) {
        for (const mode of [...modes, 'not-a-declared-mode', '𝓵𝓲𝓵𝔂']) {
          const url = pathToFileURL(path.join(__dirname, file));
          url.searchParams.set(id === 'cipherSelect' ? 'mode' : id, mode);
          await page.goto(url.href);
          assert.equal(await page.locator('#' + id).inputValue(), modes.includes(mode) ? mode : fallback);
        }
      }
    } finally { await browser.close(); }
  });
