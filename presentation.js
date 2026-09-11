/* Presentation only: never a codec, normalization pass, or hidden channel. */
(function (root) {
  'use strict';
  const ASCII = /[A-Za-z]/;
  const LITERAL = /https?:\/\/[^\s<>()]+|(?:[\w./-]+)?\.(?:md|py|js|mjs|cjs|json|html|css|png|zip|txt|wav|mp3|mid)\b|\bU\+[0-9A-Fa-f]{4,6}\b|“[^”\n]*”|"[^"\n]*"/g;
  const SKIP = 'script,style,noscript,template,textarea,input,pre,code,kbd,samp,svg,math,[data-literal],.sr-only,.specimen';
  function letters(text, voice = 'house') {
    return Array.from(text, char => {
      if (!ASCII.test(char)) return char;
      const lower = char.toLowerCase(), n = lower.charCodeAt(0) - 97;
      if (voice === 'bold-script') return String.fromCodePoint(0x1d4ea + n);
      if (voice === 'bold-fraktur') return String.fromCodePoint(0x1d586 + n);
      if (voice === 'monospace') return String.fromCodePoint(0x1d68a + n);
      return String.fromCodePoint(('aeiou'.includes(lower) ? 0x1d41a : 0x1d5ba) + n);
    }).join('');
  }
  function prose(text, voice = 'house') {
    let end = 0, out = '';
    for (const match of text.matchAll(LITERAL)) {
      out += letters(text.slice(end, match.index), voice) + match[0];
      end = match.index + match[0].length;
    }
    return out + letters(text.slice(end), voice);
  }
  function install(doc, options = {}) {
    if (!doc.body || doc.body.dataset.gardenReady) return;
    for (const selector of options.raw || []) {
      for (const element of doc.querySelectorAll(selector)) element.setAttribute('data-literal', '');
    }
    doc.body.dataset.gardenReady = 'true';
    doc.body.classList.add('garden-presentation');
    const ownedLabels = new WeakSet();
    function accessible(element, plain) {
      if (!plain.trim()) return;
      if (!element.hasAttribute('aria-label') || ownedLabels.has(element)) {
        element.setAttribute('aria-label', plain);
        ownedLabels.add(element);
      }
    }
    function paint() {
      observer.disconnect();
      // Only authored hints opt in to attribute lettering. Never touch control
      // values, downloaded bytes, transcript text, ARIA text, or source titles.
      for (const element of doc.querySelectorAll('[data-garden-placeholder],[data-garden-title]')) {
        if (element.closest('[data-literal]')) continue;
        if (element.hasAttribute('data-garden-placeholder')) {
          const plain = element.getAttribute('placeholder') || '';
          if (ASCII.test(plain)) {
            accessible(element, plain.normalize('NFKC'));
            element.setAttribute('placeholder', prose(plain));
          }
        }
        if (element.hasAttribute('data-garden-title')) {
          if (element.tagName === 'TITLE') element.textContent = prose(element.textContent);
          else if (element.hasAttribute('title')) element.setAttribute('title', prose(element.getAttribute('title')));
        }
      }
      for (const element of doc.querySelectorAll('button,a,label,summary,option,h1,h2,h3,h4,h5,h6')) {
        if (element.closest(SKIP) || !ASCII.test(element.textContent)) continue;
        const plain = element.textContent.normalize('NFKC');
        accessible(element, plain);
        if (element.tagName === 'LABEL' && element.htmlFor) {
          const control = doc.getElementById(element.htmlFor);
          if (control) accessible(control, plain);
        }
        // Option labels may change; their underlying values must not.
        if (element.tagName === 'OPTION' && !element.hasAttribute('value')) element.value = element.value;
      }
      const walker = doc.createTreeWalker(doc.body, 4);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      for (const node of nodes) {
        const parent = node.parentElement;
        if (!parent || parent.closest(SKIP) || !ASCII.test(node.data)) continue;
        const heading = parent.closest('h1,h2,h3');
        const voice = heading ? (heading.tagName === 'H1' ? options.titleVoice || 'bold-script' : 'monospace') : 'house';
        const decorated = prose(node.data, voice);
        if (node.data !== decorated) node.data = decorated;
      }
      observer.observe(doc.body, { childList: true, subtree: true, characterData: true,
        attributes: true, attributeFilter: ['placeholder', 'title'] });
    }
    const observer = new doc.defaultView.MutationObserver(paint);
    paint();
    return { refresh: paint };
  }
  const api = { letters, prose, install, skipSelector: SKIP };
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.GardenPresentation = api;
  if (typeof document !== 'undefined') {
    const script = document.currentScript;
    const options = { titleVoice: script?.dataset.titleVoice || 'bold-script',
      raw: (script?.dataset.raw || '').split(';').filter(Boolean) };
    install(document, options);
    for (const frame of document.querySelectorAll('iframe[data-garden-frame]')) {
      const decorate = () => {
        try {
          const doc = frame.contentDocument;
          install(doc, { raw: ['#bloom', '#decoded', '#accessible-output', '#chips', '#glyph-big', '#cp-list', '.formula'] });
          const link = doc.createElement('link');
          link.rel = 'stylesheet'; link.href = 'presentation.css'; doc.head.append(link);
          const size = () => { frame.style.height = Math.ceil(doc.body.scrollHeight) + 'px'; };
          new doc.defaultView.ResizeObserver(size).observe(doc.body);
          size();
        } catch { /* A frame outside this origin is never inspected. */ }
      };
      frame.addEventListener('load', decorate);
      if (frame.contentDocument?.readyState === 'complete') decorate();
    }
  }
})(typeof globalThis === 'undefined' ? this : globalThis);
