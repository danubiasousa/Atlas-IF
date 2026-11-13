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
  const CLASSIFICAR = {
    pressao(v) {
      const m = v.match(/^(\d{2,3})\/(\d{2,3})$/); if (!m) return null;
      const s = +m[1], d = +m[2];
      if (s >= 180 || d >= 110) return ['alerta', `Pressão muito alta (${v}): possível crise hipertensiva. Reavalie e considere encaminhar.`];
      if (s < 80 || d < 50) return ['alerta', `Pressão muito baixa (${v}): hipotensão importante. Deite o aluno e reavalie.`];
      if (s >= 140 || d >= 90) return ['alerta', `Pressão alta (${v}): acima de 140/90.`];
      if (s < 90 || d < 60) return ['atencao', `Pressão baixa (${v}): abaixo de 90/60. Observe tontura e mal-estar.`];
      if (s >= 130 || d >= 85) return ['atencao', `Pressão limítrofe (${v}): entre 130/85 e 139/89.`];
      return ['ok', 'Pressão normal'];
    },
    fc(v) {
      const n = num(v);
      if (n < 50) return ['alerta', `Frequência cardíaca muito baixa (${n} bpm): bradicardia.`];
      if (n > 120) return ['alerta', `Frequência cardíaca muito alta (${n} bpm): taquicardia.`];
      if (n < 60) return ['atencao', `Frequência cardíaca baixa (${n} bpm).`];
      if (n > 100) return ['atencao', `Frequência cardíaca alta (${n} bpm).`];
      return ['ok', 'Frequência cardíaca normal'];
    },
    fr(v) {
      const n = num(v);
      if (n < 10) return ['alerta', `Frequência respiratória muito baixa (${n} irpm).`];
      if (n > 24) return ['alerta', `Frequência respiratória muito alta (${n} irpm): taquipneia.`];
      if (n < 12) return ['atencao', `Frequência respiratória baixa (${n} irpm).`];
      if (n > 20) return ['atencao', `Frequência respiratória alta (${n} irpm).`];
      return ['ok', 'Frequência respiratória normal'];
    },
    temperatura(v) {
      const n = num(v);
      if (n < 35) return ['alerta', `Temperatura muito baixa (${v} °C): hipotermia.`];
      if (n >= 39) return ['alerta', `Febre alta (${v} °C).`];
      if (n >= 37.8) return ['alerta', `Febre (${v} °C).`];
      if (n < 36) return ['atencao', `Temperatura baixa (${v} °C).`];
      if (n >= 37.3) return ['atencao', `Febrícula (${v} °C).`];
      return ['ok', 'Temperatura normal'];
    },
    saturacao(v) {
      const n = num(v);
      if (n < 92) return ['alerta', `Saturação baixa (${n}%): possível falta de oxigenação. Avalie com urgência.`];
      if (n < 95) return ['atencao', `Saturação no limite (${n}%).`];
      return ['ok', 'Saturação normal'];
    },
    glicemia(v) {
      const n = num(v);
      if (n < 54) return ['alerta', `Glicemia muito baixa (${n} mg/dL): hipoglicemia grave.`];
      if (n < 70) return ['alerta', `Glicemia baixa (${n} mg/dL): hipoglicemia. Ofereça açúcar se o aluno estiver consciente e reavalie.`];
      if (n >= 200) return ['alerta', `Glicemia muito alta (${n} mg/dL): hiperglicemia.`];
      if (n > 140) return ['atencao', `Glicemia elevada (${n} mg/dL).`];
      return ['ok', 'Glicemia normal'];
    },
  };
  const IMC_OMS = {
    M: { 10: [12.8, 13.7, 18.5, 21.4, 26.1], 11: [13.1, 14.1, 19.2, 22.5, 27.9], 12: [13.4, 14.5, 19.9, 23.6, 29.6],
         13: [13.8, 14.9, 20.8, 24.8, 31.2], 14: [14.3, 15.5, 21.8, 25.9, 32.6], 15: [14.7, 16.0, 22.7, 27.0, 33.8],
         16: [15.1, 16.5, 23.5, 27.9, 34.8], 17: [15.4, 16.9, 24.3, 28.6, 35.5], 18: [15.7, 17.3, 24.9, 29.2, 35.9],
         19: [15.9, 17.6, 25.4, 29.7, 36.2] },
    F: { 10: [12.4, 13.5, 19.0, 22.6, 28.4], 11: [12.7, 13.9, 19.9, 23.7, 30.2], 12: [13.2, 14.4, 20.8, 25.0, 31.9],
         13: [13.6, 14.9, 21.8, 26.2, 33.4], 14: [14.0, 15.4, 22.7, 27.3, 34.7], 15: [14.4, 15.9, 23.5, 28.2, 35.5],
         16: [14.6, 16.2, 24.1, 28.9, 36.1], 17: [14.7, 16.4, 24.5, 29.3, 36.3], 18: [14.7, 16.4, 24.8, 29.5, 36.3],
         19: [14.7, 16.5, 25.0, 29.7, 36.2] },
  };
  function idadeEmMeses() {
    const n = document.getElementById('data_nascimento').value;
    if (!n) return null;
    const d = new Date(n + 'T00:00'), h = new Date(document.getElementById('data').value + 'T00:00');
    let m = (h.getFullYear() - d.getFullYear()) * 12 + h.getMonth() - d.getMonth();
    if (h.getDate() < d.getDate()) m--;
    return m >= 0 ? m : null;
  }
  function classificarIMC() {
    const peso = num(document.getElementById('peso').value), alt = num(document.getElementById('altura').value) / 100;
    const ver = document.getElementById('imc-ver'), oculto = document.getElementById('imc');
    ver.value = ''; oculto.value = '';
    if (!(peso > 0) || !(alt > 0.4) || !document.getElementById('peso').checkValidity()
        || !document.getElementById('altura').checkValidity()) return null;
    const imc = peso / (alt * alt), txt = imc.toFixed(1).replace('.', ',');
    ver.value = txt;
    const meses = idadeEmMeses(), sexo = document.getElementById('sexo').value;
    let r;
    if (meses === null || !sexo) {
      r = ['atencao', `IMC ${txt}: informe o nascimento e o sexo na etapa 1 para classificar pela tabela de idade.`];
    } else if (meses >= 240) {         
      r = imc < 16 ? ['alerta', `IMC ${txt}: magreza grave.`]
        : imc < 18.5 ? ['atencao', `IMC ${txt}: baixo peso (abaixo de 18,5).`]
        : imc < 25 ? ['ok', `Peso adequado (IMC ${txt})`]
        : imc < 30 ? ['atencao', `IMC ${txt}: sobrepeso (25 a 29,9).`]
        : ['alerta', `IMC ${txt}: obesidade (30 ou mais).`];
    } else if (meses < 120) {
      r = ['atencao', `IMC ${txt}: a tabela do sistema começa aos 10 anos; avalie pela curva de crescimento.`];
    } else {
      const tab = IMC_OMS[sexo], a = Math.floor(meses / 12), f = (meses % 12) / 12;
      const lo = tab[a], hi = tab[Math.min(a + 1, 19)];
      const [m3, m2, p1, p2, p3] = lo.map((v, i) => v + (hi[i] - v) * (a >= 19 ? 0 : f));
      const fx = v => v.toFixed(1).replace('.', ',');
      r = imc < m3 ? ['alerta', `IMC ${txt}: magreza acentuada para a idade (abaixo de ${fx(m3)}).`]
        : imc < m2 ? ['atencao', `IMC ${txt}: magreza para a idade (abaixo de ${fx(m2)}).`]
        : imc <= p1 ? ['ok', `Peso adequado para a idade (IMC ${txt}; faixa ${fx(m2)} a ${fx(p1)})`]
        : imc <= p2 ? ['atencao', `IMC ${txt}: sobrepeso para a idade (acima de ${fx(p1)}).`]
        : imc <= p3 ? ['alerta', `IMC ${txt}: obesidade para a idade (acima de ${fx(p2)}).`]
        : ['alerta', `IMC ${txt}: obesidade grave para a idade (acima de ${fx(p3)}).`];
    }
    const nomes = { ok: 'Adequado', atencao: 'Atenção', alerta: 'Alerta' };
    oculto.value = `${txt} – ${r[0] === 'ok' ? 'adequado' : r[1].split(': ')[1] || nomes[r[0]]}`.slice(0, 60);
    return r;
  }

   const ROTULO = { ok: '✓ Normal', atencao: '⚠ Atenção', alerta: '⛔ Alerta' };
  function pintar(el, msg, r) {
    const caixa = el.closest('.com-unidade');
    caixa.classList.add('s-' + r[0]);
    msg.classList.add(r[0]);
    const curto = r[1].split(':').slice(-1)[0].replace(/ \(.*\)/, '').replace(/\.$/, '').trim();
    const titulo = r[1].split(':')[0].replace(/ \(.*\)/, '').replace(/\.$/, '');
    msg.innerHTML = '';
    const tag = document.createElement('span'); tag.className = 'tag-nivel ' + r[0]; tag.textContent = ROTULO[r[0]];
    const t = document.createElement('span');
    t.textContent = r[0] === 'ok' ? '' : ' ' + (titulo.startsWith('IMC') ? curto : titulo);
    msg.append(tag, t);
  }

  function classificarSinais() {
    const avisos = [];
    form.querySelectorAll('[data-sinal]').forEach(el => {
      const caixa = el.closest('.com-unidade'), msg = document.getElementById('msg-' + el.id);
      caixa.classList.remove('s-ok', 's-atencao', 's-alerta');
      msg.className = 'msg-sinal'; msg.textContent = '';
      const fn = CLASSIFICAR[el.id];
      if (!fn || !el.value || !el.checkValidity()) return;
      const r = fn(el.value.trim());
      if (!r) return;
      pintar(el, msg, r);
      if (r[0] !== 'ok') avisos.push(r);
    });
    const ver = document.getElementById('imc-ver');
    if (ver) {
      const msgImc = document.getElementById('msg-imc-ver');
      ver.closest('.com-unidade').classList.remove('s-ok', 's-atencao', 's-alerta');
      msgImc.className = 'msg-sinal'; msgImc.textContent = '';
      const ri = classificarIMC();
      if (ri) {
        pintar(ver, msgImc, ri);
        document.getElementById('peso').closest('.com-unidade').classList.add('s-' + ri[0]);
        document.getElementById('altura').closest('.com-unidade').classList.add('s-' + ri[0]);
        if (ri[0] !== 'ok') avisos.push(ri);
      }
    }
    const painel = document.getElementById('alertas-sinais');
    if (!painel) return;
    const ul = painel.querySelector('ul');
    ul.innerHTML = '';
    avisos.sort((a, b) => (a[0] === 'alerta' ? -1 : 1) - (b[0] === 'alerta' ? -1 : 1)).forEach(([nivel, texto]) => {
      const li = document.createElement('li'); li.className = nivel;
      const tag = document.createElement('span'); tag.className = 'tag-nivel ' + nivel; tag.textContent = ROTULO[nivel];
      li.append(tag, ' ' + texto); ul.appendChild(li);
    });
    painel.hidden = !avisos.length;
    painel.classList.toggle('grave', avisos.some(a => a[0] === 'alerta'));
  }
  form.querySelectorAll('[data-sinal]').forEach(el => el.addEventListener('blur', () => {
    if (el.dataset.sinal === 'pa') el.value = el.value.replace(/\/$/, '');
    conferirSinal(el); classificarSinais();
  }));
  classificarSinais();
  ['sexo', 'data_nascimento', 'data'].forEach(i => document.getElementById(i).addEventListener('change', classificarSinais));
  document.addEventListener('aluno-selecionado', () => setTimeout(classificarSinais, 0));

  form.querySelectorAll('[data-nenhum]').forEach(b => (b.onclick = () => {
    const el = document.getElementById(b.dataset.nenhum);
    el.value = b.dataset.valor || b.textContent.trim();
    el.setCustomValidity('');
  }));

  mostrar(0);
})();