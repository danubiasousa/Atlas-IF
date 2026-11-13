"""Agendamentos: portal do aluno, horários disponíveis, painel do profissional e resposta às solicitações (Geovane)."""
from nucleo import *  

@app.route("/painel")
@profissional_required
def painel():
    def um(cur, sql, args=()):
        cur.execute(sql, args)
        return cur.fetchone()["n"]

    with get_db().cursor() as cur:
        hoje_n = um(cur, "SELECT COUNT(*) n FROM atendimentos WHERE DATE(data_hora)=CURDATE()")
        ontem_n = um(cur, "SELECT COUNT(*) n FROM atendimentos WHERE DATE(data_hora)=CURDATE()-INTERVAL 1 DAY")
        stats = {
            "hoje": hoje_n,
            "diff": hoje_n - ontem_n,
            "retornos": um(cur, "SELECT COUNT(*) n FROM retornos WHERE status='pendente'"),
            "urgentes": um(cur, "SELECT COUNT(*) n FROM retornos WHERE status='pendente' AND urgente=1"),
            "encaminhamentos": um(cur, "SELECT COUNT(*) n FROM atendimentos WHERE status='Encaminhado' "
                                       "AND YEAR(data_hora)=YEAR(CURDATE()) AND MONTH(data_hora)=MONTH(CURDATE())"),
            "em_falta": um(cur, "SELECT COUNT(*) n FROM estoque WHERE ideal > 0 AND quantidade < ideal*%s", (LIMITE_CRITICO,)),
        }
        cur.execute("SELECT * FROM solicitacoes WHERE status='pendente' AND profissional_id=%s ORDER BY criado_em DESC",
                    (session["user_id"],))
        solicitacoes = cur.fetchall()
        cur.execute("SELECT * FROM atendimentos ORDER BY data_hora DESC LIMIT 5")
        recentes = cur.fetchall()
        cur.execute("SELECT * FROM retornos WHERE status='pendente' ORDER BY data_hora LIMIT 5")
        retornos = cur.fetchall()
        cur.execute("SELECT *, quantidade/ideal AS pct FROM estoque WHERE ideal > 0 AND quantidade < ideal*%s ORDER BY pct LIMIT 5",
                    (LIMITE_CRITICO,))
        estoque = cur.fetchall()

    hoje = date.today()
    return render_template(
        "painel.html", stats=stats, solicitacoes=solicitacoes, recentes=recentes,
        retornos=retornos, estoque=estoque,
        data_longa=f"{DIAS[hoje.weekday()]}, {hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}",
        data_curta=f"{hoje.day:02d} de {MESES[hoje.month - 1][:3]}. de {hoje.year}",
    )

JANELAS = {"Manhã": (time(8, 0), time(12, 30), "8h00 às 12h30"), "Tarde": (time(14, 0), time(18, 0), "14h00 às 18h00")}
DIA_TODO = ("Manhã", "Tarde")
PORTAL = {
    "Enfermagem": {"descricao": "Mariana pela manhã e Stéfany à tarde", "compartilhado": True,
                   "nota": "A enfermagem aceita vários alunos no mesmo horário, conforme a necessidade.",
                   "profissionais": [("mariana.moura@ifpi.edu.br", ("Manhã",)), ("stefany.moreira@ifpi.edu.br", ("Tarde",))]},
    "Odontológico": {"descricao": "Dentista ou técnico em saúde bucal, manhã e tarde", "compartilhado": False,
                     "nota": "O atendimento odontológico é individual: cada horário atende um aluno.",
                     "profissionais": [("debora.castro@ifpi.edu.br", DIA_TODO), ("leonardo.rocha@ifpi.edu.br", DIA_TODO)]},
}
STATUS_SOLIC = {"pendente": ("Aguardando confirmação", "amarelo"), "aceita": ("Confirmado", "verde"),
                "recusada": ("Recusado", "vermelho")}

def horarios(turnos):
    """Horários de 30 em 30 minutos dentro das janelas dos turnos do profissional."""
    saida = []
    for turno in turnos:
        ini, fim, _ = JANELAS[turno]
        t = datetime.combine(date.today(), ini)
        while t.time() < fim:
            saida.append({"v": t.strftime("%H:%M"), "l": f"{t.hour}h{t.minute:02d}"})
            t += timedelta(minutes=30)
    return saida

def descricao_turnos(turnos):
    if tuple(turnos) == DIA_TODO:
        return "Dia todo", "8h00 às 12h30 e 14h00 às 18h00"
    return " e ".join(turnos), " e ".join(JANELAS[t][2] for t in turnos)

def montar_grupos(cur):
    emails = [e for g in PORTAL.values() for e, _ in g["profissionais"]]
    cur.execute("SELECT id, usuario, nome, cargo FROM usuarios WHERE ativo = 1 AND usuario IN (%s)"
                % ",".join(["%s"] * len(emails)), emails)
    por_email = {r["usuario"]: r for r in cur.fetchall()}
    grupos = {}
    for tipo, g in PORTAL.items():
        lista = []
        for e, turnos in g["profissionais"]:
            if e in por_email:
                rot, janela = descricao_turnos(turnos)
                lista.append({"id": por_email[e]["id"], "nome": por_email[e]["nome"], "cargo": por_email[e]["cargo"],
                              "turno": rot, "janela": janela, "slots": horarios(turnos)})
        grupos[tipo] = {**g, "lista": lista}
    return grupos

def achar_profissional(grupos, prof_id):
    for tipo, g in grupos.items():
        for p in g["lista"]:
            if str(p["id"]) == str(prof_id):
                return tipo, g, p
    return None, None, None

def horarios_do_dia(cur, g, prof, dia):
    """Slots do profissional no dia: some os já passados (hoje) e, no odontológico, os já ocupados."""
    ocupados = set()
    if not g["compartilhado"]:
        cur.execute("SELECT horario FROM solicitacoes WHERE profissional_id = %s AND data_preferencial = %s "
                    "AND status <> 'recusada'", (prof["id"], dia))
        ocupados = {r["horario"] for r in cur.fetchall()}
    agora_ = agora()
    saida = []
    for s in prof["slots"]:
        passou = dia == agora_.date() and s["v"] <= agora_.strftime("%H:%M")
        saida.append({**s, "livre": not passou and s["v"] not in ocupados,
                      "motivo": "já passou" if passou else ("ocupado" if s["v"] in ocupados else "")})
    return saida

@app.route("/aluno")
@aluno_required
def aluno_painel():
    with get_db().cursor() as cur:
        solicitacoes = minhas_solicitacoes(cur, 5)
    return render_template("aluno_painel.html", solicitacoes=solicitacoes, status_solic=STATUS_SOLIC)

def minhas_solicitacoes(cur, limite=20):
    cur.execute("SELECT s.*, u.nome AS prof_nome FROM solicitacoes s LEFT JOIN usuarios u ON u.id = s.profissional_id "
                "WHERE s.aluno_id = %s ORDER BY s.criado_em DESC, s.id DESC LIMIT %s", (session["aluno_id"], limite))
    return cur.fetchall()

@app.route("/aluno/api/horarios")
@aluno_required
def api_horarios():
    """Disponibilidade de um profissional numa data, seguindo o calendário acadêmico."""
    try:
        dia = datetime.strptime(request.args.get("data", ""), "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"bloqueado": "Data inválida.", "slots": []})
    if dia < agora().date():
        return jsonify({"bloqueado": "Escolha uma data a partir de hoje.", "slots": []})
    motivo = motivo_bloqueio(dia)
    if motivo:
        prox = proximo_dia_util(dia)
        return jsonify({"bloqueado": motivo, "proximo": prox.isoformat() if prox else None,
                        "proximo_br": prox.strftime("%d/%m/%Y") if prox else None, "slots": []})
    with get_db().cursor() as cur:
        _, g, prof = achar_profissional(montar_grupos(cur), request.args.get("profissional_id"))
        if not prof:
            return jsonify({"bloqueado": "Escolha o profissional.", "slots": []})
        slots = horarios_do_dia(cur, g, prof, dia)
    if not any(s["livre"] for s in slots):
        return jsonify({"bloqueado": "Não há mais horários livres nesse dia com esse profissional.", "slots": slots})
    return jsonify({"bloqueado": None, "slots": slots})
    @app.route("/aluno/marcar", methods=["GET", "POST"])
@aluno_required
def aluno_marcar():
    with get_db().cursor() as cur:
        grupos = montar_grupos(cur)

        if request.method == "POST":
            f = request.form
            tipo, g, prof = achar_profissional(grupos, f.get("profissional_id"))
            if tipo != f.get("tipo"):
                prof = None
            motivo, horario = f.get("motivo", "").strip(), f.get("horario", "")
            try:
                dia = datetime.strptime(f.get("data", ""), "%Y-%m-%d").date()
            except ValueError:
                dia = None
            erro = None
            if not prof:
                erro = "Escolha o tipo de atendimento e o profissional."
            elif not dia or dia < agora().date():
                erro = "Escolha uma data a partir de hoje."
            elif motivo_bloqueio(dia):
                erro = f"{dia:%d/%m/%Y}: {motivo_bloqueio(dia)}. Escolha um dia útil do calendário acadêmico."
            elif not motivo:
                erro = "Descreva o motivo do atendimento."
            else:
                slot = next((x for x in horarios_do_dia(cur, g, prof, dia) if x["v"] == horario), None)
                if not slot:
                    erro = "Escolha um horário disponível."
                elif not slot["livre"]:
                    erro = ("Esse horário já passou. Escolha outro horário." if slot["motivo"] == "já passou" else
                            "Esse horário já foi solicitado por outro aluno. Escolha outro horário.")
            if erro:
                flash(erro, "erro")
                return redirect(url_for("aluno_marcar"))
            cur.execute("INSERT INTO solicitacoes (aluno_id, aluno_nome, motivo, profissional_id, tipo, data_preferencial, "
                        "horario, em_aula) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (session["aluno_id"], session["nome"], motivo[:300], prof["id"], tipo, dia, horario,
                         int(bool(f.get("em_aula")))))
            return redirect(url_for("aluno_marcar", enviada=cur.lastrowid))

        enviada = None
        if request.args.get("enviada", "").isdigit():
            cur.execute("SELECT s.*, u.nome AS prof_nome FROM solicitacoes s LEFT JOIN usuarios u ON u.id = s.profissional_id "
                        "WHERE s.id = %s AND s.aluno_id = %s", (request.args["enviada"], session["aluno_id"]))
            enviada = cur.fetchone()
    hoje = agora().date()
    sugestao = proximo_dia_util(hoje)
    return render_template("aluno_marcar.html", grupos=grupos, enviada=enviada, hoje=hoje.isoformat(),
                           sugestao=sugestao.isoformat() if sugestao else hoje.isoformat(),
                           limite=ULTIMO_DIA_CALENDARIO.isoformat())