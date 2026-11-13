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

  function mascaraTelefone(v) {
    let d = v.replace(/\D/g, '');
    if (d.length > 11 && d.startsWith('55')) d = d.slice(2);
    d = d.slice(0, 11);
    if (!d) return '';
    if (d.length <= 2) return `(${d}`;
    const ddd = d.slice(0, 2), n = d.slice(2);
    if (n.length <= 4) return `(${ddd})${n}`;
    if (d.length < 11) return `(${ddd})${n.slice(0, 4)}-${n.slice(4)}`;   
    return `(${ddd})${n.slice(0, 5)}-${n.slice(5)}`;                      
  }
  document.querySelectorAll('[data-telefone]').forEach(i => {
    const aplicar = () => { i.value = mascaraTelefone(i.value); };
    i.addEventListener('input', aplicar);
    aplicar();
  });

  document.querySelectorAll('[data-sugestoes]').forEach(input => {
    const lista = input.parentElement.querySelector('.sugestoes');
    let itens = [], ativo = -1, pedido = 0, timer;
    const fechar = () => { lista.hidden = true; ativo = -1; input.setAttribute('aria-expanded', 'false'); };
    const escolher = valor => {
      input.value = valor; fechar();
      const senha = input.form.querySelector('input[type=password]');
      if (senha) senha.focus();
    };
    function desenhar() {
      lista.innerHTML = '';
      if (!itens.length) return fechar();
      const q = input.value.trim().toLowerCase();
      itens.forEach((it, i) => {
        const li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.className = i === ativo ? 'ativo' : '';
        const n = it.valor.toLowerCase().startsWith(q) ? q.length : 0;
        const forte = document.createElement('b'); forte.textContent = it.valor.slice(0, n);
        const resto = document.createElement('span'); resto.textContent = it.valor.slice(n);
        const tipo = document.createElement('small'); tipo.textContent = it.tipo;
        li.append(forte, resto, tipo);
        li.addEventListener('mousedown', e => { e.preventDefault(); escolher(it.valor); });
        lista.appendChild(li);
      });
      lista.hidden = false;
      input.setAttribute('aria-expanded', 'true');
    }
    input.addEventListener('input', () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { itens = []; return fechar(); }
      timer = setTimeout(async () => {
        const meu = ++pedido;
        try {
          const r = await fetch(`${input.dataset.sugestoes}?q=${encodeURIComponent(q)}`);
          const dados = await r.json();
          if (meu !== pedido) return;
          itens = dados.filter(d => d.valor.toLowerCase() !== q.toLowerCase());
          ativo = -1; desenhar();
        } catch (e) { fechar(); }
      }, 150);
    });
    input.addEventListener('keydown', e => {
      if (lista.hidden) return;
      if (e.key === 'ArrowDown') { ativo = (ativo + 1) % itens.length; desenhar(); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { ativo = (ativo - 1 + itens.length) % itens.length; desenhar(); e.preventDefault(); }
      else if ((e.key === 'Enter' || e.key === 'Tab') && ativo >= 0) { escolher(itens[ativo].valor); e.preventDefault(); }
      else if (e.key === 'Escape') fechar();
    });
    input.addEventListener('blur', () => setTimeout(fechar, 120));
  });

  document.querySelectorAll('[data-dominio]').forEach(box => {
    const i = box.querySelector('input');
    const atualizar = () => {
      const v = i.value.trim();
      box.classList.toggle('sem-sufixo', /^\d/.test(v) || v.includes('@'));
    };
    i.addEventListener('input', atualizar);
    atualizar();
  });
})();