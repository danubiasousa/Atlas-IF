(() => {
  const ESPECIAIS = "!@#$%&*()-_=+[]{};:,.?/\\|~^";
  const testes = {
    min: s => s.length >= 6,
    mai: s => /[A-ZÀ-Ý]/.test(s),
    min_l: s => /[a-zß-ÿ]/.test(s),
    num: s => /\d/.test(s),
    esp: s => [...s].some(c => ESPECIAIS.includes(c)),
  };

  document.querySelectorAll('[data-form-senha]').forEach(form => {
    const nova = form.querySelector('[data-nova]'), conf = form.querySelector('[data-confirma]');
    const lista = form.querySelector('[data-regras]');
    if (!nova || !lista) return;
    function atualizar() {
      const s = nova.value;
      let ok = true;
      lista.querySelectorAll('li').forEach(li => {
        const r = li.dataset.regra;
        const passou = r === 'igual' ? (s !== '' && conf && s === conf.value) : testes[r](s);
        li.classList.toggle('ok', passou);
        ok = ok && passou;
      });
      nova.setCustomValidity(Object.values(testes).every(t => t(s)) ? '' : 'A senha não cumpre todos os requisitos.');
      if (conf) conf.setCustomValidity(conf.value && conf.value !== s ? 'As senhas não são iguais.' : '');
    }
    nova.addEventListener('input', atualizar);
    if (conf) conf.addEventListener('input', atualizar);
    atualizar();
  });

  document.querySelectorAll('[data-olho]').forEach(b => {
    b.addEventListener('click', () => {
      const i = document.getElementById(b.dataset.olho);
      const ver = i.type === 'password';
      i.type = ver ? 'text' : 'password';
      b.textContent = ver ? 'Ocultar' : 'Mostrar';
    });
  });