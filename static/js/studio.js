(function () {
  const form = document.getElementById('tf'), go = document.getElementById('go'), err = document.getElementById('err');
  document.querySelectorAll('#tf select').forEach(s => s.classList.add('form-select'));
  const ready = {};
  function check() { go.disabled = !(ready.person && ready.garment); }
  document.querySelectorAll('.dropzone').forEach(zone => {
    const input = zone.querySelector('input'), img = zone.querySelector('.preview');
    ['dragenter', 'dragover'].forEach(ev => zone.addEventListener(ev, () => zone.classList.add('drag')));
    ['dragleave', 'drop'].forEach(ev => zone.addEventListener(ev, () => zone.classList.remove('drag')));
    input.addEventListener('change', () => {
      const f = input.files[0];
      if (!f || !f.type.startsWith('image/')) { ready[input.name] = false; zone.classList.remove('has-img'); check(); return; }
      img.src = URL.createObjectURL(f);
      zone.classList.add('has-img');
      ready[input.name] = true; check();
    });
  });
  form.addEventListener('submit', async e => {
    e.preventDefault();
    err.classList.add('d-none');
    go.disabled = true;
    go.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Subiendo…';
    try {
      const r = await fetch(location.href, { method: 'POST', body: new FormData(form), headers: { 'X-Requested-With': 'fetch' } });
      const j = await r.json();
      if (j.ok) { location.href = j.url; return; }
      err.textContent = j.error || 'No se pudo enviar.';
    } catch (_) { err.textContent = 'Error de red al subir las imágenes.'; }
    err.classList.remove('d-none');
    go.disabled = false; go.innerHTML = '<i class="bi bi-magic"></i> Probar';
  });
})();
