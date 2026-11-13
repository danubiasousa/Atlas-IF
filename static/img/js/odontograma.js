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