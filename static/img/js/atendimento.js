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