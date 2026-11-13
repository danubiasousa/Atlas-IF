(() => {
  const $ = id => document.getElementById(id);
  if (!$('passo-odonto')) return;

  const SUP = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28];
  const INF = [48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38];
  const TODOS = [...SUP, ...INF];
  const BOCA = 0;   
  const procSel = $('od-proc');
  const nomeDente = n => (n === BOCA ? 'Todos os dentes' : `Dente ${n}`);
  const DENTE_SVG = '<svg viewBox="0 0 24 34" width="22" height="32" aria-hidden="true"><path d="M5 4C5 2 8 1.5 10 2.2c1.2.4 2.8.4 4 0C16 1.5 19 2 19 4c0 4-1.5 6.5-2 11-.4 5-1 16-3 16-1.4 0-1.4-7-2-7s-.6 7-2 7c-2 0-2.6-11-3-16C6.5 10.5 5 8 5 4Z"/></svg>';
  const CLASSE_SIT = { 'Concluído': 'verde', 'Planejado': 'amarelo', 'Em andamento': 'azul' };

  let registros = [], sel = null, editando = null, faces = new Set();
  const dataBase = () => $('data').value;
  const fmt = iso => iso.split('-').reverse().join('/');

  function arcada(el, lista, inferior) {
    lista.forEach(n => {
      const b = document.createElement('button');
      b.type = 'button'; b.dataset.dente = n; b.className = 'dente' + (inferior ? ' inf' : '');
      b.innerHTML = inferior ? DENTE_SVG + `<span>${n}</span>` : `<span>${n}</span>` + DENTE_SVG;
      b.onclick = () => { limpar(); ir(n); };
      el.appendChild(b);
    });
  }
  arcada($('fila-sup'), SUP, false);
  arcada($('fila-inf'), INF, true);

  function marcas() {
    document.querySelectorAll('.dente').forEach(b => {
      const n = +b.dataset.dente;
      b.classList.toggle('sel', n === sel || sel === BOCA);
      b.classList.toggle('reg', registros.some(r => r.dente === n));
    });
  }

  function modoBoca(on) {
    const inp = $('od-dente');
    inp.readOnly = on;
    $('bloco-faces').hidden = on;
    $('od-todos').classList.toggle('on', on);
    [...procSel.options].forEach(o => (o.hidden = on && !o.hasAttribute('data-boca-toda')));
    if (on && procSel.selectedOptions[0].hidden) procSel.value = 'Limpeza (profilaxia)';
    if (on) { faces = new Set(); pintarFaces(); }
  }

  function ir(n) {
    sel = n;
    modoBoca(n === BOCA);
    $('od-dente').value = n === BOCA ? 'Todos' : n;
    $('od-sub').innerHTML = n === BOCA ? '<b>Todos os dentes</b>' : `Dente <b>${n}</b>`;
    $('od-hist-sub').textContent = n === BOCA ? 'Procedimentos da boca toda' : `Registros do dente ${n}`;
    marcas(); historico();
  }
  $('od-todos').onclick = () => { limpar(); ir(BOCA); };

   function historico() {
    const lista = $('od-lista');
    lista.innerHTML = '';
    const itens = registros.filter(r => r.dente === sel).sort((a, b) => b.data.localeCompare(a.data));
    $('od-cont').textContent = itens.length;
    if (!itens.length) {
      const p = document.createElement('p'); p.className = 'vazio-int';
      p.textContent = sel === BOCA ? 'Nenhum procedimento da boca toda.' : sel ? 'Nenhum registro para este dente.' : 'Selecione um dente no odontograma.';
      lista.appendChild(p); return;
    }
    itens.forEach(r => {
      const d = document.createElement('div'); d.className = 'od-item';
      d.innerHTML = '<div class="od-item-topo"><strong></strong><span class="badge"></span></div><small class="mono"></small><p></p><button type="button" class="editar">Editar registro</button>';
      d.querySelector('strong').textContent = r.procedimento;
      const bd = d.querySelector('.badge'); bd.textContent = r.situacao; bd.classList.add(CLASSE_SIT[r.situacao] || 'amarelo');
      d.querySelector('small').textContent = fmt(r.data) + (r.faces.length ? ' · ' + r.faces.join(', ') : '');
      d.querySelector('p').textContent = r.observacoes || '';
      d.querySelector('.editar').onclick = () => editar(r);
      lista.appendChild(d);
    });
  }

  function pintarFaces() {
    document.querySelectorAll('.face').forEach(b => b.classList.toggle('on', faces.has(b.dataset.face)));
  }
  document.querySelectorAll('.face').forEach(b => (b.onclick = () => {
    faces.has(b.dataset.face) ? faces.delete(b.dataset.face) : faces.add(b.dataset.face);
    pintarFaces();
  }));

  function limpar() {
    editando = null; faces = new Set(); pintarFaces();
    procSel.selectedIndex = 0; $('od-sit').value = 'Planejado'; $('od-obs').value = '';
    $('od-data').value = dataBase(); $('od-erro').hidden = true;
    $('od-salvar').textContent = 'Salvar procedimento';
  }

  function editar(r) {
    limpar(); editando = r; ir(r.dente);
    procSel.value = r.procedimento; $('od-sit').value = r.situacao; $('od-data').value = r.data;
    $('od-obs').value = r.observacoes || ''; faces = new Set(r.faces); pintarFaces();
    $('od-salvar').textContent = 'Atualizar procedimento';
  }

  function sincronizar() {
    $('odonto-json').value = JSON.stringify(registros.filter(r => r.novo || r.sujo)
      .map(({ id, dente, procedimento, faces, situacao, data, observacoes }) => ({ id, dente, procedimento, faces, situacao, data, observacoes })));
  }

  $('od-dente').addEventListener('input', e => {
    if (e.target.readOnly) return;
    const n = parseInt(e.target.value, 10);
    if (TODOS.includes(n) && n !== sel) { sel = n; $('od-sub').innerHTML = `Dente <b>${n}</b>`; $('od-hist-sub').textContent = `Registros do dente ${n}`; marcas(); historico(); }
  });

  $('od-salvar').onclick = () => {
    const n = sel === BOCA ? BOCA : parseInt($('od-dente').value, 10), erro = $('od-erro');
    if (n === BOCA && !procSel.selectedOptions[0].hasAttribute('data-boca-toda')) {
      erro.textContent = 'Em “Todos os dentes” escolha limpeza, raspagem, flúor, avaliação ou orientação.'; erro.hidden = false; return;
    }
    if (n !== BOCA && !TODOS.includes(n)) { erro.textContent = 'Selecione um dente (11–18, 21–28, 31–38 ou 41–48) ou “Todos os dentes”.'; erro.hidden = false; return; }
    const dado = { dente: n, procedimento: procSel.value, faces: n === BOCA ? [] : [...faces], situacao: $('od-sit').value,
                   data: $('od-data').value || dataBase(), observacoes: $('od-obs').value.trim() };
    if (editando) { Object.assign(editando, dado); editando.sujo = true; }
    else registros.push({ id: null, novo: true, ...dado });
    sincronizar(); limpar(); ir(n);
  };
  $('od-cancelar').onclick = () => { limpar(); if (sel !== null) ir(sel); };

  async function carregar(id) {
    registros = []; sincronizar(); marcas(); historico();
    try {
      const r = await fetch(`/api/alunos/${id}/odonto`);
      registros = (await r.json()).map(x => ({ ...x, faces: x.faces ? x.faces.split(', ') : [] }));
    } catch (_) { registros = []; }
    marcas(); historico();
  }
  document.addEventListener('aluno-selecionado', e => carregar(e.detail.id));
  document.addEventListener('aluno-limpo', () => { registros = registros.filter(r => r.novo); marcas(); historico(); });

  historico();
  if ($('aluno_id').value) carregar($('aluno_id').value);
})();