(() => {
  const form = document.getElementById('form-atend');
  const passos = [...form.querySelectorAll('.passo')];
  const itens = [...document.querySelectorAll('#stepper li')];
  const ant = document.getElementById('btn-ant'), prox = document.getElementById('btn-prox'), fim = document.getElementById('btn-fim');
  let atual = 0;

  function mostrar(n) {
    atual = n;
    passos.forEach((p, i) => (p.hidden = i !== n));
    itens.forEach((li, i) => {
      li.classList.toggle('atual', i === n);
      li.classList.toggle('feito', i < n);
      li.querySelector('.num').textContent = i < n ? '✓' : i + 1;
    });
    ant.disabled = n === 0;
    prox.hidden = n === passos.length - 1;
    fim.hidden = !prox.hidden;
    if (n === passos.length - 1) resumo();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  const valido = () => [...passos[atual].querySelectorAll('input[name], textarea[name], select[name]')].every(el => el.hidden || el.type === 'hidden' || el.reportValidity());
  prox.onclick = () => valido() && mostrar(atual + 1);
  ant.onclick = () => atual > 0 && mostrar(atual - 1);
  itens.forEach((li, i) => (li.onclick = () => i < atual && mostrar(i)));
  form.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.tagName === 'INPUT') e.preventDefault(); });

  const nome = document.getElementById('aluno_nome'), lista = document.getElementById('sugestoes');
  const id = document.getElementById('aluno_id'), mat = document.getElementById('matricula'), turma = document.getElementById('turma');
  const nasc = document.getElementById('data_nascimento'), idade = document.getElementById('idade');
  const fmtData = iso => (iso ? iso.split('-').reverse().join('/') : '—');
  function mostrarIdade() {
    idade.textContent = '';
    if (!nasc.value) return;
    const n = new Date(nasc.value + 'T00:00'), h = new Date();
    let anos = h.getFullYear() - n.getFullYear();
    if (h < new Date(h.getFullYear(), n.getMonth(), n.getDate())) anos--;
    if (anos >= 0 && anos < 120) idade.textContent = `· ${anos} anos`;
  }
  nasc.addEventListener('input', mostrarIdade);
  mostrarIdade();
  let timer;
  nome.addEventListener('input', () => {
    id.value = '';
    if (nasc.readOnly) { nasc.value = ''; nasc.readOnly = false; mostrarIdade(); }
    document.dispatchEvent(new Event('aluno-limpo'));
    clearTimeout(timer);
    const q = nome.value.trim();
    if (q.length < 2) { lista.hidden = true; return; }
    timer = setTimeout(async () => {
      try {
        const r = await fetch('/api/alunos?q=' + encodeURIComponent(q));
        const alunos = await r.json();
        lista.innerHTML = '';
        alunos.forEach(a => {
          const li = document.createElement('li');
          li.innerHTML = '<b></b><small></small>';
          li.firstChild.textContent = a.nome;
          li.lastChild.textContent = `${a.matricula} · ${a.turma || ''}`;
          li.onmousedown = e => {
            e.preventDefault();
            nome.value = a.nome; id.value = a.id; mat.value = a.matricula; turma.value = a.turma || '';
            nasc.value = a.data_nascimento || ''; nasc.readOnly = !!a.data_nascimento; mostrarIdade();
            document.getElementById('sexo').value = a.sexo || '';
            if (!a.data_nascimento) nasc.focus();
            lista.hidden = true;
            document.dispatchEvent(new CustomEvent('aluno-selecionado', { detail: a }));
          };
          lista.appendChild(li);
        });
        lista.hidden = !alunos.length;
      } catch (_) { lista.hidden = true; }
    }, 200);
  });
  nome.addEventListener('blur', () => setTimeout(() => (lista.hidden = true), 120));

  const emAula = document.getElementById('em_aula'), decl = document.getElementById('info-decl');
  const atualizarDecl = () => { if (decl) decl.classList.toggle('ativa', emAula.checked); };
  emAula.onchange = atualizarDecl; atualizarDecl();

  const ret = document.getElementById('agendar_retorno'), blocoRet = document.getElementById('bloco-retorno'), retData = document.getElementById('retorno_data');
  if (ret) {
    ret.onchange = () => { blocoRet.hidden = !ret.checked; retData.hidden = !ret.checked; retData.required = ret.checked; };
    retData.hidden = true;
  }

  const resumo = () => {
    document.getElementById('res-aluno').textContent = nome.value || '—';
    document.getElementById('res-turma').textContent = turma.value || '—';
    document.getElementById('res-nasc').textContent = fmtData(nasc.value) + (idade.textContent ? ' ' + idade.textContent.replace('·', '(') + ')' : '');
    const ro = document.getElementById('res-odonto'), oj = document.getElementById('odonto-json');
    if (ro && oj) { try { ro.textContent = JSON.parse(oj.value || '[]').length; } catch (_) { ro.textContent = 0; } }
  };

  const FILTROS = {
    alfanum: v => v.replace(/[^A-Za-z0-9]/g, '').toUpperCase(),
    texto: v => v.replace(/[0-9]/g, ''),
    int: v => v.replace(/\D/g, ''),
    dec: v => v.replace(/[^\d.,]/g, '').replace(/([.,].*)[.,]/g, '$1'),
    pa: v => v,   
     function formatarPA(v, digitando) {
    let sis, dia;
    if (v.includes('/')) {
      const [a, b = ''] = v.split('/');
      sis = a.replace(/\D/g, '').slice(0, 3); dia = b.replace(/\D/g, '').slice(0, 3);
      return `${sis}/${dia}`;
    }
    const d = v.replace(/\D/g, '');
    const corte = /^[123]/.test(d) ? 3 : 2;
    if (d.length > corte) return `${d.slice(0, corte)}/${d.slice(corte, corte + 3)}`;
    if (d.length === corte && digitando) return `${d}/`;
    return d;
  }
  form.querySelectorAll('[data-filtro], [data-sinal]').forEach(el => {
    const f = FILTROS[el.dataset.filtro || el.dataset.sinal];
    el.addEventListener('input', e => {
      const novo = el.dataset.sinal === 'pa'
        ? formatarPA(el.value, (e.inputType || '').startsWith('insert'))
        : f(el.value);
      if (novo !== el.value) el.value = novo;
      if (el.dataset.sinal) { conferirSinal(el); classificarSinais(); }
    });
  });
  function conferirSinal(el) {
    const v = el.value.trim();
    let msg = '';
    if (v) {
      if (el.dataset.sinal === 'pa') {
        const m = v.match(/^(\d{2,3})\/(\d{2,3})$/);
        if (!m) msg = 'Use o formato sistólica/diastólica, ex.: 120/80.';
        else if (+m[1] < 40 || +m[1] > 300 || +m[2] < 20 || +m[2] > 200) msg = 'Valor fora do possível. Confira a digitação.';
        else if (+m[1] <= +m[2]) msg = 'A sistólica (1º número) precisa ser maior que a diastólica.';
      } else {
        const ok = el.dataset.sinal === 'int' ? /^\d{1,3}$/.test(v) : /^\d{1,3}([.,]\d)?$/.test(v);
        const n = parseFloat(v.replace(',', '.'));
        if (!ok) msg = 'Digite só números' + (el.dataset.sinal === 'dec' ? ' (ex.: ' + el.placeholder + ').' : '.');
        else if (n < +el.dataset.min || n > +el.dataset.max) msg = `Valor fora do possível (${el.dataset.min} a ${el.dataset.max}). Confira a digitação.`;
      }
    }
    el.setCustomValidity(msg);
  }
  form.querySelectorAll('[data-sinal]').forEach(conferirSinal);

  const num = v => parseFloat(String(v).replace(',', '.'));