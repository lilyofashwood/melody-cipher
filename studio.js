const $ = id => document.getElementById(id);
// Launcher links can choose declared settings, never inject text or endpoints.
const settings = new URLSearchParams(location.search);
for (const id of ['mode', 'phrasing']) {
  const requested = settings.get(id);
  if ([...$(id).options].some(option => option.value === requested)) $(id).value = requested;
}
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
  $('text-filename').textContent = file?.name || '';
  if (!file) return;
  try { if (file.size > 512) throw new Error('Choose a file of at most 512 bytes.');
    $('text').value = new TextDecoder('utf-8', {fatal:true}).decode(await file.arrayBuffer());
  } catch(e) { $('status').textContent = e.message; }
});
$('recording').addEventListener('change', () => {
  $('recording-filename').textContent = $('recording').files[0]?.name || '';
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
  $('result').textContent = '';
  const file = $('recording').files[0]; if (!file) { $('decode-status').textContent = 'Choose a WAV first.'; return; }
  if (file.size > 50*1024*1024) { $('decode-status').textContent = 'File exceeds 50 MiB.'; return; }
  $('decode').disabled = true; $('decode-status').textContent = 'Listening to the waveform…'; $('events').textContent = '';
  try { const r = await post('/decode', file, 'application/octet-stream');
    $('decode-status').textContent = 'VERIFIED · CRC32 valid'; $('result').textContent = r.text; $('events').textContent = JSON.stringify(r,null,2);
  } catch(e) { $('decode-status').textContent = 'REJECTED · '+e.message; }
  finally { $('decode').disabled = false; }
});
