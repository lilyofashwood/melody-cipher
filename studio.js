const $ = id => document.getElementById(id);
let session;
async function post(path, body, type) {
  session ??= await fetch('/session').then(r => r.json());
  const r = await fetch(path, {method:'POST', headers:{'Content-Type':type,'X-Studio-Token':session.token}, body});
  const result = await r.json();
  if (!r.ok) throw new Error(result.error);
  return result;
}
$('text-file').addEventListener('change', async () => {
  const file = $('text-file').files[0];
  if (!file) return;
  try { if (file.size > 512) throw new Error('Choose a file of at most 512 bytes.');
    $('text').value = new TextDecoder('utf-8', {fatal:true}).decode(await file.arrayBuffer());
  } catch(e) { $('status').textContent = e.message; }
});
$('compose').addEventListener('click', async () => {
  $('compose').disabled = true; $('status').textContent = 'Composing, then decoding fresh audio…';
  $('downloads').replaceChildren(); $('player').removeAttribute('src');
  try {
    const result = await post('/encode', JSON.stringify({text:$('text').value,mode:$('mode').value,bpm:Number($('bpm').value),phrasing:$('phrasing').value}), 'application/json');
    $('player').src = result.wav;
    for (const [label, url] of [['Download WAV',result.wav],['Download MIDI',result.midi]]) {
      const a = document.createElement('a'); a.href = url; a.textContent = label; a.download = ''; $('downloads').append(a);
    }
    $('status').textContent = 'Verified from audio alone. Press Play to listen.';
    $('events').textContent = JSON.stringify(result.receipt, null, 2);
  } catch(e) { $('status').textContent = 'Rejected: '+e.message; }
  finally { $('compose').disabled = false; }
});
$('decode').addEventListener('click', async () => {
  const file = $('recording').files[0]; if (!file) { $('result').textContent = 'Choose a WAV first.'; return; }
  if (file.size > 50*1024*1024) { $('result').textContent = 'File exceeds 50 MiB.'; return; }
  $('decode').disabled = true; $('result').textContent = 'Listening to the waveform…'; $('events').textContent = '';
  try { const r = await post('/decode', file, 'application/octet-stream');
    $('result').textContent = 'VERIFIED · CRC32 valid\n\n'+r.text; $('events').textContent = JSON.stringify(r,null,2);
  } catch(e) { $('result').textContent = 'REJECTED · '+e.message; }
  finally { $('decode').disabled = false; }
});
