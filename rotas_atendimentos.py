"""Registro de atendimentos (anamnese, sinais vitais), histórico e declaração de comparecimento (Maria Aparecida)."""
from nucleo import *  
from rotas_odonto_materiais import (ODONTO_CARGOS, DENTES, FACES, SITUACOES, PROC_ODONTO, BOCA_TODA,  
                                    TODOS_DENTES, nome_dente, usa_odonto, ler_odonto)


PROCEDIMENTOS = ["Verificação de sinais vitais", "Curativo simples", "Administração de medicamento oral",
                 "Aplicação de compressa", "Aferição de glicemia", "Nebulização", "Oximetria de pulso",
                 "Inalação", "Aferição de pressão arterial"]
SINAIS = [("pressao", "Pressão arterial", "120/80", "mmHg"), ("fc", "Freq. cardíaca", "78", "bpm"),
          ("fr", "Freq. respiratória", "16", "irpm"), ("temperatura", "Temperatura", "36.5", "°C"),
          ("saturacao", "Saturação O₂", "98", "%"), ("peso", "Peso", "65", "kg"), ("altura", "Altura", "165", "cm"),
          ("glicemia", "Glicemia", "95", "mg/dL")]
REGRAS_SINAIS = {"pressao": ("pa", None, None, True), "fc": ("int", 20, 250, True), "fr": ("int", 4, 80, True),
                 "temperatura": ("dec", 30, 45, True), "saturacao": ("int", 40, 100, True),
                 "peso": ("dec", 2, 350, True), "altura": ("int", 50, 230, True), "glicemia": ("int", 10, 999, False)}
ANAMNESE = ["historico", "alergias", "medicamentos_uso", "doencas", "encaminhado_por"]


def erro_sinal(campo, valor):
    """Confere o formato e a faixa de um sinal vital. Devolve a mensagem de erro ou None."""
    tipo, mn, mx, obrig = REGRAS_SINAIS[campo]
    rotulo = next(r for n, r, *_ in SINAIS if n == campo)
    if not valor:
        return f"Preencha {rotulo}." if obrig else None
    if tipo == "pa":
        m = re.fullmatch(r"(\d{2,3})/(\d{2,3})", valor)
        if not m or not (40 <= int(m[1]) <= 300 and 20 <= int(m[2]) <= 200 and int(m[1]) > int(m[2])):
            return "Pressão arterial no formato 120/80 (sistólica/diastólica)."
        return None
    if not re.fullmatch(r"\d{1,3}" if tipo == "int" else r"\d{1,3}([.,]\d)?", valor):
        return f"{rotulo}: digite só números" + (" (ex.: 36.5)." if tipo == "dec" else ".")
    if not (mn <= float(valor.replace(",", ".")) <= mx):
        return f"{rotulo} deve ficar entre {mn} e {mx}."
    return None



@app.route("/api/alunos")
@profissional_required
def api_alunos():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    with get_db().cursor() as cur:
        cur.execute("SELECT id, nome, matricula, turma, data_nascimento, sexo FROM alunos WHERE nome LIKE %s ORDER BY nome LIMIT 8",
                    (f"%{q}%",))
        alunos = cur.fetchall()
    for a in alunos:
        a["data_nascimento"] = a["data_nascimento"].isoformat() if a["data_nascimento"] else ""
        a["sexo"] = a["sexo"] or ""
    return jsonify(alunos)


@app.route("/atendimento/novo", methods=["GET", "POST"])
@profissional_required
def novo_atendimento():
    if request.method == "POST":
        f = request.form
        nome, queixa = f.get("aluno_nome", "").strip(), f.get("queixa", "").strip()
        if not nome or not queixa:
            flash("Informe o nome do aluno e a queixa principal.", "erro")
            return redirect(url_for("novo_atendimento"))
        try:
            dh = datetime.strptime(f"{f.get('data')} {f.get('hora')}", "%Y-%m-%d %H:%M")
        except ValueError:
            dh = agora()
        enc, ret = int(bool(f.get("enc_externo"))), int(bool(f.get("agendar_retorno")))
        tipo, status = (("Encaminhamento", "Encaminhado") if enc else
                        ("Retorno", "Retorno") if ret else ("Atendimento", "Concluído"))
        dados = {
            "aluno_nome": nome, "aluno_id": f.get("aluno_id") or None, "matricula": f.get("matricula", "").strip(),
            "turma": f.get("turma", "").strip(), "queixa": queixa, "em_aula": int(bool(f.get("em_aula"))),
            "data_hora": dh, "tipo": tipo, "status": status, "profissional_id": session["user_id"],
            "enc_externo": enc, "agendar_retorno": ret,
            "procedimentos": "; ".join(f.getlist("proc")),
        }
        for c in ["historico", "alergias", "medicamentos_uso", "doencas", "encaminhado_por", "pressao", "fc", "fr",
                  "temperatura", "saturacao", "peso", "altura", "glicemia", "imc", "medicamentos_adm", "orientacoes",
                  "observacoes"]:
            dados[c] = f.get(c, "").strip() or None
        try:
            nasc = datetime.strptime(f.get("data_nascimento", ""), "%Y-%m-%d").date()
        except ValueError:
            nasc = None
        if not nasc or not (date(1950, 1, 1) <= nasc <= agora().date()):
            flash("Informe a data de nascimento do aluno.", "erro")
            return redirect(url_for("novo_atendimento"))
        sexo = f.get("sexo") if f.get("sexo") in ("F", "M") else None
        if not sexo:
            flash("Informe o sexo do aluno (usado no cálculo do IMC por idade).", "erro")
            return redirect(url_for("novo_atendimento"))

            if not usa_odonto():
            faltando = [c for c in ANAMNESE if not dados[c]]
            erro = ("Preencha todos os campos da anamnese (use “Nenhuma” quando não houver)." if faltando else
                    next((e for c in REGRAS_SINAIS if (e := erro_sinal(c, dados[c] or ""))), None))
            if erro:
                flash(erro, "erro")
                return redirect(url_for("novo_atendimento"))
            for c in ("temperatura", "peso"):
                if dados[c]:
                    dados[c] = dados[c].replace(",", ".")
        dados["finalizado_em"] = agora()
        registros = ler_odonto(f.get("odonto"), dh.date()) if usa_odonto() else []
        if registros and not dados["procedimentos"]:
            dados["procedimentos"] = "; ".join(f"{nome_dente(r['dente'])} – {r['procedimento']}" for r in registros)[:600]
        with get_db().cursor() as cur:
            cur.execute(f"INSERT INTO atendimentos ({', '.join(dados)}) VALUES ({', '.join(['%s'] * len(dados))})",
                        list(dados.values()))
            novo_id = cur.lastrowid
            if dados["aluno_id"]:   
                cur.execute("UPDATE alunos SET data_nascimento=%s WHERE id=%s AND data_nascimento IS NULL",
                            (nasc, dados["aluno_id"]))
                cur.execute("UPDATE alunos SET sexo=%s WHERE id=%s AND sexo IS NULL", (sexo, dados["aluno_id"]))
            codigo = f"ATD-{dh.year}-{1000 + novo_id}"
            cur.execute("UPDATE atendimentos SET codigo=%s WHERE id=%s", (codigo, novo_id))
            for r in registros:
                if r["id"]:   
                    cur.execute("UPDATE procedimentos_odonto SET dente=%s, procedimento=%s, faces=%s, situacao=%s, "
                                "data=%s, observacoes=%s WHERE id=%s AND aluno_id <=> %s",
                                (r["dente"], r["procedimento"], r["faces"], r["situacao"], r["data"],
                                 r["observacoes"], r["id"], dados["aluno_id"]))
                else:
                    cur.execute("INSERT INTO procedimentos_odonto (aluno_id, aluno_nome, atendimento_id, dente, "
                                "procedimento, faces, situacao, data, observacoes, profissional_id) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                (dados["aluno_id"], nome, novo_id, r["dente"], r["procedimento"], r["faces"],
                                 r["situacao"], r["data"], r["observacoes"], session["user_id"]))
            if ret:
                try:
                    quando_ret = datetime.strptime(f.get("retorno_data", ""), "%Y-%m-%dT%H:%M")
                except ValueError:
                    quando_ret = datetime.combine(dh.date() + timedelta(days=1), time(8, 0))
                dia_ret = proximo_dia_util(quando_ret.date())
                if dia_ret and dia_ret != quando_ret.date():
                    flash(f"{quando_ret:%d/%m/%Y}: {motivo_bloqueio(quando_ret.date())}. "
                          f"O retorno foi remarcado para {dia_ret:%d/%m/%Y}.", "erro")
                    quando_ret = datetime.combine(dia_ret, quando_ret.time())
                cur.execute("INSERT INTO retornos (aluno_nome, motivo, data_hora) VALUES (%s,%s,%s)",
                            (nome, f"Retorno – {queixa}"[:160], quando_ret))
        flash(f"Atendimento {codigo} finalizado com sucesso.")
        if dados["em_aula"]:
            return redirect(url_for("declaracao", atendimento_id=novo_id, novo=1))
        return redirect(url_for("historico"))

    d = agora()
    with get_db().cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM atendimentos")
        proximo = cur.fetchone()["n"]
        aluno_pre = None
        if request.args.get("aluno", "").isdigit():
            cur.execute("SELECT id, nome, matricula, turma, data_nascimento, sexo FROM alunos WHERE id = %s",
                        (request.args["aluno"],))
            aluno_pre = cur.fetchone()
    return render_template(
        "atendimento_novo.html", aluno_pre=aluno_pre, procedimentos=PROCEDIMENTOS, sinais=SINAIS, usa_odonto=usa_odonto(),
        regras_sinais=REGRAS_SINAIS, proc_odonto=PROC_ODONTO, boca_toda=BOCA_TODA,
        etapas=(["Identificação", "Odontograma", "Orientações"] if usa_odonto() else
                ["Identificação", "Anamnese", "Sinais Vitais", "Procedimentos", "Orientações"]),
        codigo=f"ATD-{d.year}-{1000 + proximo}", data_iso=d.strftime("%Y-%m-%d"), hora=d.strftime("%H:%M"),
        data_extenso=f"{d.day} de {MESES[d.month - 1]} de {d.year} {d:%H:%M}",
    )

    @app.route("/atendimentos/<int:atendimento_id>/declaracao")
@profissional_required
def declaracao(atendimento_id):
    """Declaração de comparecimento no modelo do IFPI, preenchida com o aluno e o profissional do atendimento."""
    with get_db().cursor() as cur:
        cur.execute("SELECT a.*, u.nome AS prof_nome, u.cargo AS prof_cargo, u.campus AS prof_campus "
                    "FROM atendimentos a LEFT JOIN usuarios u ON u.id = a.profissional_id WHERE a.id = %s",
                    (atendimento_id,))
        a = cur.fetchone()
    if not a:
        flash("Atendimento não encontrado.", "erro")
        return redirect(url_for("historico"))
    fim = a.get("finalizado_em") or a["data_hora"]
    if fim.date() != a["data_hora"].date() or fim < a["data_hora"]:
        fim = a["data_hora"]
    return render_template("declaracao.html", a=a, inicio=a["data_hora"].strftime("%H:%M"), fim=fim.strftime("%H:%M"),
                           campus=a.get("prof_campus") or "Paulistana", novo=request.args.get("novo"))

                           @app.route("/historico")
@profissional_required
def historico():
    q, tipo, data = (request.args.get(k, "").strip() for k in ("q", "tipo", "data"))
    where, args = [], []
    if q:
        where.append("a.aluno_nome LIKE %s"); args.append(f"%{q}%")
    if tipo in ("Atendimento", "Retorno", "Encaminhamento"):
        where.append("a.tipo = %s"); args.append(tipo)
    if data:
        where.append("DATE(a.data_hora) = %s"); args.append(data)
    sql = ("SELECT a.*, u.nome AS prof_nome, u.cargo AS prof_cargo FROM atendimentos a "
           "LEFT JOIN usuarios u ON u.id = a.profissional_id "
           + ("WHERE " + " AND ".join(where) + " " if where else "") + "ORDER BY a.data_hora DESC LIMIT 200")
    with get_db().cursor() as cur:
        cur.execute(sql, args)
        registros = cur.fetchall()
    return render_template("historico.html", registros=registros, q=q, tipo=tipo, data=data)