(function() {
  // Override encodeBase8 to include '/' for spaces and '\n' tokens
  window.encodeBase8 = function(config, text) {
    const notes = [];
    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (ch === ' ') {
        notes.push('/');
      } else if (ch === '\n') {
        notes.push('\n');
      } else if (/[A-Za-z]/.test(ch)) {
        const idx = ch.toUpperCase().charCodeAt(0) - 65;
        if (idx >= 0 && idx < 26) {
          const hi = Math.floor(idx / 8);
          const lo = idx % 8;
          notes.push(config.notes[hi], config.notes[lo]);
        }
      } else {
        const code = ch.charCodeAt(0);
        let oct = code.toString(8).padStart(3, '0');
        for (let j = 0; j < oct.length; j += 2) {
          const hi = parseInt(oct[j], 8);
          const lo = parseInt(oct[j+1], 8);
          notes.push(config.notes[hi], config.notes[lo]);
        }
      }
    }
    return notes;
  };

  // Override renderNotes to display '/' and newlines appropriately
  window.renderNotes = function(notes, config) {
    return notes.map(n => {
      if (n === '/') return '/';
      if (n === '\n') return '<br>';
      const color = config.colors[n] || '#58a6ff';
      return "<span class=\"note\" style=\"color:" + color + ";\">" + n + "</span>";
    }).join(' ');
  };

  function decodeBase12(config, noteStr) {
    const noteMap = {};
    config.notes.forEach((note,i) => { noteMap[note] = i; });
    let out = '';
    const lines = noteStr.trim().split('\n');
    lines.forEach((line, li) => {
      if (li > 0) out += '\n';
      const tokens = line.trim().split(/\s+/);
      for (let i = 0; i < tokens.length; i += 2) {
        const hiTok = tokens[i];
        const loTok = tokens[i+1];
        if (!hiTok || !loTok) {
          out += '?';
          continue;
        }
        if (noteMap[hiTok] === undefined || noteMap[loTok] === undefined) {
          out += '?';
          continue;
        }
        const code = noteMap[hiTok] * config.notes.length + noteMap[loTok];
        out += String.fromCharCode(code);
      }
    });
    return out;
  }

  function decodeBase8(config, noteStr) {
    const noteMap = {};
    config.notes.forEach((note,i) => { noteMap[note] = i; });
    let out = '';
    const lines = noteStr.split('\n');
    lines.forEach((line, li) => {
      if (li > 0) out += '\n';
      const tokens = line.trim().split(/\s+/).filter(t => t.length > 0);
      for (let i = 0; i < tokens.length;) {
        const tok = tokens[i];
        if (tok === '/') {
          out += ' ';
          i++;
          continue;
        }
        const hiTok = tokens[i];
        const loTok = tokens[i+1];
        if (!hiTok || !loTok) {
          out += '?';
          break;
        }
        if (noteMap[hiTok] === undefined || noteMap[loTok] === undefined) {
          out += '?';
          i += 2;
          continue;
        }
        const val = noteMap[hiTok] * 8 + noteMap[loTok];
        if (val >= 0 && val < 26) {
          out += String.fromCharCode(65 + val);
        } else {
          out += '?';
        }
        i += 2;
      }
    });
    return out;
  }

  // Setup decode button event after DOM ready
  document.addEventListener('DOMContentLoaded', function() {
    const decodeBtn = document.getElementById('decodeBtn');
    if (decodeBtn) {
      decodeBtn.addEventListener('click', function() {
        const cipherKey = document.getElementById('cipherSelect').value;
        const config = cipherConfigs[cipherKey];
        const input = document.getElementById('inputText').value;
        let result = '';
        if (config.type === 'base12') {
          result = decodeBase12(config, input);
        } else {
          result = decodeBase8(config, input);
        }
        document.getElementById('output').innerText = result;
      });
    }
  });
})();
