"""Login, primeiro acesso, recuperação de senha, minha conta, cadastro de alunos e usuários (Danúbia)."""
from nucleo import *  

def buscar_usuario(texto):
    """Aceita 'nome.sobrenome' (completa com @ifpi.edu.br), o e-mail completo, a matrícula do aluno
    ou o e-mail que o aluno cadastrou no primeiro acesso."""
    texto = (texto or "").strip().lower().replace(" ", "")
    if not texto:
        return None
    candidatos = [texto] if "@" in texto else [texto + DOMINIO, texto]
    marcas = ",".join(["%s"] * len(candidatos))
    with get_db().cursor() as cur:
        cur.execute(f"SELECT * FROM usuarios WHERE usuario IN ({marcas}) AND ativo = 1 "
                    "ORDER BY LOCATE('@', usuario) DESC LIMIT 1", candidatos)
        user = cur.fetchone()
        if user or "@" not in texto:
            return user

        cur.execute("SELECT * FROM usuarios WHERE perfil = 'aluno' AND ativo = 1 AND LOWER(email_recuperacao) = %s LIMIT 2",
                    (texto,))
        achados = cur.fetchall()
        return achados[0] if len(achados) == 1 else None


def senha_confere(user, senha):
    """A senha pessoal diferencia maiúsculas de minúsculas. Exceção: a senha INICIAL padronizada
    (setorsaude2026, a matrícula do aluno) aceita qualquer combinação: SetorSaude2026, 2025120iipi0009..."""
    if check_password_hash(user["senha_hash"], senha):
        return True
    if not user.get("trocar_senha"):
        return False
    return any(v != senha and check_password_hash(user["senha_hash"], v) for v in {senha.upper(), senha.lower()})


def email_em_uso(email, uid):
    """O e-mail do aluno também serve de login, então não pode repetir o de outra pessoa."""
    with get_db().cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE id <> %s AND (usuario = %s OR "
                    "(perfil = 'aluno' AND LOWER(email_recuperacao) = %s)) LIMIT 1", (uid, email, email))
        return cur.fetchone() is not None


def dados_aluno(user):
    with get_db().cursor() as cur:
        cur.execute("SELECT id, matricula, turma FROM alunos WHERE usuario_id = %s AND ativo = 1", (user["id"],))
        return cur.fetchone()


def iniciar_sessao(user):
    """Abre a sessão de fato (depois da senha e, se preciso, do primeiro acesso)."""
    session.clear()
    if user["perfil"] == "aluno":
        al = dados_aluno(user)
        if not al:
            flash("Cadastro de aluno não encontrado ou inativo.")
            return redirect(url_for("login"))
        session.update(user_id=user["id"], nome=user["nome"], cargo="Aluno(a)", perfil="aluno",
                       aluno_id=al["id"], matricula=al["matricula"], turma=al["turma"] or "")
        return redirect(url_for("aluno_painel"))
    session.update(user_id=user["id"], nome=user["nome"], cargo=user["cargo"] or "Profissional", perfil="profissional",
                   nivel=user.get("nivel") or "Operador")
    return redirect(url_for("painel"))


def precisa_primeiro_acesso(user):
    return bool(user.get("trocar_senha")) or not (user.get("email_recuperacao") and user.get("telefone_recuperacao"))


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session and request.method == "GET":
        return redirect(url_for("aluno_painel" if session.get("perfil") == "aluno" else "painel"))

    if request.method == "POST":
        digitado = request.form.get("usuario", "").strip().lower()
        senha = request.form.get("senha", "")

        if not digitado or not senha:
            flash("Informe o usuário e a senha.")
            return render_template("login.html", versao=VERSAO, usuario=digitado)

        user = buscar_usuario(digitado)
        if user and senha_confere(user, senha):
            if user["perfil"] == "aluno" and not dados_aluno(user):
                registrar_acesso(user["usuario"], False)
                flash("Cadastro de aluno não encontrado ou inativo.")
                return render_template("login.html", versao=VERSAO, usuario=digitado)
            registrar_acesso(user["usuario"], True)
            if precisa_primeiro_acesso(user):
                session.clear()
                session["pendente_uid"] = user["id"]
                return redirect(url_for("primeiro_acesso"))
            return iniciar_sessao(user)

        registrar_acesso(user["usuario"] if user else (digitado if "@" in digitado else digitado + DOMINIO), False)
        flash("Usuário ou senha incorretos.")
        return render_template("login.html", versao=VERSAO, usuario=digitado)
    return render_template("login.html", versao=VERSAO, usuario="")


_SUGESTOES_IP = {}


@app.route("/api/sugestoes-usuario")
def sugestoes_usuario():
    """Sugestões para o campo Usuário enquanto a pessoa digita: logins dos servidores e matrículas dos alunos."""
    q = (request.args.get("q") or "").strip().lower().replace(" ", "")
    if len(q) < 2 or len(q) > 120:
        return jsonify([])

    ip, agora_ = request.remote_addr or "?", agora()
    janela = [t for t in _SUGESTOES_IP.get(ip, []) if (agora_ - t).total_seconds() < 60]
    if len(janela) >= 60:
        return jsonify([])
    _SUGESTOES_IP[ip] = janela + [agora_]

    prefixo = q.replace("\\", "").replace("%", "").replace("_", "\\_") + "%"
    with get_db().cursor() as cur:
        
        cur.execute("SELECT usuario AS valor, perfil FROM usuarios WHERE ativo = 1 AND usuario LIKE %s "
                    "ORDER BY valor LIMIT 6", (prefixo,))
        linhas = cur.fetchall()
    return jsonify([{"valor": r["valor"].upper() if r["perfil"] == "aluno" and "@" not in r["valor"] else r["valor"],
                     "tipo": "Aluno" if r["perfil"] == "aluno" else "Servidor"} for r in linhas if r["valor"]])


def usuario_por_id(uid):
    with get_db().cursor() as cur:
        cur.execute("SELECT * FROM usuarios WHERE id = %s AND ativo = 1", (uid,))
        return cur.fetchone()


def validar_nova_senha(user, nova, confirma, senha_antiga_hash=None):
    if nova != confirma:
        return "A confirmação não confere com a nova senha."
    erros = erros_senha(nova, user["usuario"])
    if erros:
        return mensagem_erros(erros)
    if senha_antiga_hash and check_password_hash(senha_antiga_hash, nova):
        return "A nova senha precisa ser diferente da senha atual."
    return None


@app.route("/primeiro-acesso", methods=["GET", "POST"])
def primeiro_acesso():
    """Depois de entrar com a senha temporária: cria a senha definitiva e cadastra e-mail/telefone de recuperação."""
    user = usuario_por_id(session.get("pendente_uid")) if session.get("pendente_uid") else None
    if not user:
        session.pop("pendente_uid", None)
        return redirect(url_for("login"))
    ctx = dict(versao=VERSAO, user=user, regras=REGRAS_SENHA, especiais=ESPECIAIS, troca=bool(user["trocar_senha"]))

    if request.method == "POST":
        f = request.form
        email = normalizar_email(f.get("email_recuperacao"))
        tel = normalizar_telefone(f.get("telefone_recuperacao"))
        erro = None
        if ctx["troca"]:
            erro = validar_nova_senha(user, f.get("nova", ""), f.get("confirma", ""), user["senha_hash"])
        if not erro and not email:
            erro = "Informe um e-mail de recuperação válido."
        elif not erro and email.endswith(DOMINIO) and email == user["usuario"]:
            erro = "Use um e-mail pessoal diferente do seu login institucional, para conseguir recuperar o acesso."
        elif not erro and user["perfil"] == "aluno" and email_em_uso(email, user["id"]):
            erro = "Esse e-mail já está cadastrado para outra pessoa. Use outro e-mail."
        elif not erro and not tel:
            erro = "Informe um telefone com DDD, por exemplo (89) 99999-9999."
        if erro:
            flash(erro)
            return render_template("primeiro_acesso.html", **ctx, email=f.get("email_recuperacao", ""),
                                   telefone=f.get("telefone_recuperacao", ""))
        with get_db().cursor() as cur:
            if ctx["troca"]:
                cur.execute("UPDATE usuarios SET senha_hash=%s, trocar_senha=0, senha_alterada_em=%s WHERE id=%s",
                            (generate_password_hash(f["nova"]), agora(), user["id"]))
            cur.execute("UPDATE usuarios SET email_recuperacao=%s, telefone_recuperacao=%s WHERE id=%s",
                        (email, tel, user["id"]))
        resp = iniciar_sessao(usuario_por_id(user["id"]))
        flash("Tudo certo! Sua senha e seus contatos de recuperação foram salvos.", "ok")
        return resp

    return render_template("primeiro_acesso.html", **ctx, email=user.get("email_recuperacao") or "",
                           telefone=user.get("telefone_recuperacao") or "")



VALIDADE_CODIGO = timedelta(minutes=1)   
PRAZO_NOVA_SENHA = timedelta(minutes=10)  
MAX_TENTATIVAS = 5


@app.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "POST":
        user = buscar_usuario(request.form.get("usuario"))
        if not user:
            flash("Usuário não encontrado ou inativo.")
            return render_template("recuperar.html", etapa="usuario", versao=VERSAO, usuario=request.form.get("usuario", ""))
        if not (user.get("email_recuperacao") or user.get("telefone_recuperacao")):
            flash("Esse usuário ainda não cadastrou e-mail nem telefone de recuperação. "
                  "Procure o Setor de Saúde para voltar à senha inicial.")
            return render_template("recuperar.html", etapa="usuario", versao=VERSAO, usuario=request.form.get("usuario", ""))
        session.clear()
        session["rec_uid"] = user["id"]
        return redirect(url_for("enviar_codigo_rec"))
    return render_template("recuperar.html", etapa="usuario", versao=VERSAO, usuario="")


ESPERA_REENVIO = 60   


def canais_do_usuario(user):
    canais = []
    if user.get("email_recuperacao"):
        canais.append(("email", "E-mail", mascarar_email(user["email_recuperacao"])))
    if user.get("telefone_recuperacao"):
        canais.append(("sms", "SMS", mascarar_telefone(user["telefone_recuperacao"])))
    return canais


def ultimo_codigo(cur, uid):
    cur.execute("SELECT * FROM codigos_recuperacao WHERE usuario_id=%s ORDER BY id DESC LIMIT 1", (uid,))
    return cur.fetchone()


@app.route("/esqueci-senha/enviar", methods=["GET", "POST"])
def enviar_codigo_rec():
    user = usuario_por_id(session.get("rec_uid")) if session.get("rec_uid") else None
    if not user:
        return redirect(url_for("esqueci_senha"))
    canais = canais_do_usuario(user)

    if request.method == "POST":
        canal = request.form.get("canal") or session.get("rec_canal")
        if canal not in [c[0] for c in canais]:
            flash("Escolha para onde enviar o código.")
            return redirect(url_for("enviar_codigo_rec"))
        with get_db().cursor() as cur:
            ult = ultimo_codigo(cur, user["id"])
            if ult and (agora() - ult["criado_em"]).total_seconds() < ESPERA_REENVIO:
                faltam = ESPERA_REENVIO - int((agora() - ult["criado_em"]).total_seconds())
                flash(f"Aguarde {faltam} segundo(s) para pedir outro código.")
                return redirect(url_for("codigo_rec") if session.get("rec_canal") else url_for("enviar_codigo_rec"))
            cur.execute("SELECT COUNT(*) n FROM codigos_recuperacao WHERE usuario_id=%s AND criado_em > %s",
                        (user["id"], agora() - timedelta(hours=1)))
            if cur.fetchone()["n"] >= 5:
                flash("Muitos pedidos de código na última hora. Tente novamente mais tarde.")
                return redirect(url_for("enviar_codigo_rec"))
            codigo = gerar_codigo()
            destino = user["email_recuperacao"] if canal == "email" else user["telefone_recuperacao"]
            status = enviar_codigo(canal, destino, codigo, user["nome"])
            if not status:
                flash("Não foi possível enviar o código agora. Tente o outro canal ou procure o Setor de Saúde.")
                return redirect(url_for("enviar_codigo_rec"))
            cur.execute("UPDATE codigos_recuperacao SET usado=1 WHERE usuario_id=%s AND usado=0", (user["id"],))
            cur.execute("INSERT INTO codigos_recuperacao (usuario_id, canal, codigo_hash, expira_em, criado_em) "
                        "VALUES (%s,%s,%s,%s,%s)",
                        (user["id"], canal, generate_password_hash(codigo), agora() + VALIDADE_CODIGO, agora()))
        session["rec_canal"] = canal
        session["rec_destino"] = next(c[2] for c in canais if c[0] == canal)
        if status == "simulado":
            flash("Modo de teste: o envio por " + ("e-mail" if canal == "email" else "SMS") + " ainda não foi configurado, "
                  "então o código foi mostrado no terminal onde o sistema está rodando.", "ok")
        else:
            flash(f"Enviamos um novo código de 6 dígitos para {session['rec_destino']}.", "ok")
        return redirect(url_for("codigo_rec"))
    return render_template("recuperar.html", etapa="canal", versao=VERSAO, canais=canais, user=user)


@app.route("/esqueci-senha/codigo", methods=["GET", "POST"])
def codigo_rec():
    """Etapa 3: só verifica o código."""
    user = usuario_por_id(session.get("rec_uid")) if session.get("rec_uid") else None
    if not user or not session.get("rec_canal"):
        return redirect(url_for("esqueci_senha"))
    with get_db().cursor() as cur:
        ult = ultimo_codigo(cur, user["id"])
    agora_ = agora()
    espera = max(0, ESPERA_REENVIO - int((agora_ - ult["criado_em"]).total_seconds())) if ult else 0
    bloqueado = bool(ult and not ult["usado"] and ult["tentativas"] >= MAX_TENTATIVAS)
    expira = (max(0, int((ult["expira_em"] - agora_).total_seconds()))
              if ult and not ult["usado"] and not bloqueado else 0)
    ctx = dict(etapa="codigo", versao=VERSAO, user=user, destino=session.get("rec_destino", ""),
               espera=espera, expira=expira, bloqueado=bloqueado)
    if request.method == "POST":
        digitado = "".join(ch for ch in request.form.get("codigo", "") if ch.isdigit())
        with get_db().cursor() as cur:
            cur.execute("SELECT * FROM codigos_recuperacao WHERE usuario_id=%s AND usado=0 AND expira_em > %s "
                        "ORDER BY id DESC LIMIT 1", (user["id"], agora()))
            cod = cur.fetchone()
            if not cod or cod["tentativas"] >= MAX_TENTATIVAS:
                flash("O código venceu ou foi bloqueado. Clique em “Reenviar código”.")
                return redirect(url_for("codigo_rec"))
            if not check_password_hash(cod["codigo_hash"], digitado):
                cur.execute("UPDATE codigos_recuperacao SET tentativas = tentativas + 1 WHERE id=%s", (cod["id"],))
                restam = MAX_TENTATIVAS - cod["tentativas"] - 1
                flash(f"Código incorreto. {'Restam ' + str(restam) + ' tentativa(s).' if restam else 'Peça um novo código.'}")
                return redirect(url_for("codigo_rec"))
            cur.execute("UPDATE codigos_recuperacao SET usado=1 WHERE usuario_id=%s", (user["id"],))
        session["rec_ok_ate"] = (agora() + PRAZO_NOVA_SENHA).isoformat()
        flash("Código confirmado! Agora crie a sua nova senha.", "ok")
        return redirect(url_for("nova_senha_rec"))
    return render_template("recuperar.html", **ctx)


@app.route("/esqueci-senha/nova-senha", methods=["GET", "POST"])
def nova_senha_rec():
    """Etapa 4: só depois do código confirmado."""
    user = usuario_por_id(session.get("rec_uid")) if session.get("rec_uid") else None
    try:
        ok_ate = datetime.fromisoformat(session.get("rec_ok_ate", ""))
    except ValueError:
        ok_ate = None
    if not user or not ok_ate:
        return redirect(url_for("esqueci_senha"))
    if agora() > ok_ate:
        session.pop("rec_ok_ate", None)
        flash("O tempo para criar a senha acabou. Peça um novo código.")
        return redirect(url_for("enviar_codigo_rec"))
    if request.method == "POST":
        f = request.form
        erro = validar_nova_senha(user, f.get("nova", ""), f.get("confirma", ""))
        if erro:
            flash(erro)
            return redirect(url_for("nova_senha_rec"))
        with get_db().cursor() as cur:
           
            cur.execute("UPDATE usuarios SET senha_hash=%s, trocar_senha=0, senha_alterada_em=%s WHERE id=%s",
                        (generate_password_hash(f["nova"]), agora(), user["id"]))
        session.clear()
        flash("Senha redefinida e salva com sucesso. Entre com a sua nova senha.", "ok")
        return redirect(url_for("login"))
    return render_template("recuperar.html", etapa="senha", versao=VERSAO, user=user, regras=REGRAS_SENHA,
                           especiais=ESPECIAIS)



@app.route("/conta", methods=["GET", "POST"])
@login_required
def minha_conta():
    user = usuario_por_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))
    if request.method == "POST":
        f = request.form
        if not check_password_hash(user["senha_hash"], f.get("atual", "")):
            flash("Senha atual incorreta.", "erro")
            return redirect(url_for("minha_conta"))
        with get_db().cursor() as cur:
            if f.get("acao") == "senha":
                erro = validar_nova_senha(user, f.get("nova", ""), f.get("confirma", ""), user["senha_hash"])
                if erro:
                    flash(erro, "erro")
                    return redirect(url_for("minha_conta"))
                cur.execute("UPDATE usuarios SET senha_hash=%s, trocar_senha=0, senha_alterada_em=%s WHERE id=%s",
                            (generate_password_hash(f["nova"]), agora(), user["id"]))
                flash("Senha alterada com sucesso.", "ok")
            else:
                email = normalizar_email(f.get("email_recuperacao"))
                tel = normalizar_telefone(f.get("telefone_recuperacao"))
                if not email or not tel:
                    flash("Informe um e-mail válido e um telefone com DDD.", "erro")
                    return redirect(url_for("minha_conta"))
                if user["perfil"] == "aluno" and email_em_uso(email, user["id"]):
                    flash("Esse e-mail já está cadastrado para outra pessoa. Use outro e-mail.", "erro")
                    return redirect(url_for("minha_conta"))
                cur.execute("UPDATE usuarios SET email_recuperacao=%s, telefone_recuperacao=%s WHERE id=%s",
                            (email, tel, user["id"]))
                flash("Contatos de recuperação atualizados.", "ok")
        return redirect(url_for("minha_conta"))
    return render_template("minha_conta.html", ativo="conta", user=user, regras=REGRAS_SENHA, especiais=ESPECIAIS)



@app.route("/alunos")
@profissional_required
def alunos():
    q, turma, data = (request.args.get(k, "").strip() for k in ("q", "turma", "data"))
    where, args = [], []
    if q:
        where.append("(al.nome LIKE %s OR al.matricula LIKE %s OR al.turma LIKE %s)"); args += [f"%{q}%"] * 3
    if turma:
        where.append("al.turma = %s"); args.append(turma)
    if data:
        where.append("EXISTS (SELECT 1 FROM atendimentos x WHERE x.aluno_id = al.id AND DATE(x.data_hora) = %s)"); args.append(data)
    sql = ("SELECT al.*, COUNT(a.id) AS total, MAX(a.data_hora) AS ultimo FROM alunos al "
           "LEFT JOIN atendimentos a ON a.aluno_id = al.id " + ("WHERE " + " AND ".join(where) + " " if where else "")
           + "GROUP BY al.id ORDER BY al.nome")
    with get_db().cursor() as cur:
        cur.execute(sql, args)
        lista = cur.fetchall()
        cur.execute("SELECT DISTINCT turma FROM alunos WHERE turma IS NOT NULL AND turma <> '' ORDER BY turma")
        turmas = [r["turma"] for r in cur.fetchall()]
    return render_template("alunos.html", alunos=lista, turmas=turmas, q=q, turma=turma, data=data,
                           filtrado=bool(where))


@app.route("/alunos/novo", methods=["POST"])
@profissional_required
def novo_aluno():
    f = request.form
    nome = f.get("nome", "").strip()
    matricula = f.get("matricula", "").strip().upper().replace(" ", "")
    if not nome or not matricula:
        flash("Informe o nome completo e a matrícula do aluno.", "erro")
        return redirect(url_for("alunos"))
    try:
        nasc = datetime.strptime(f.get("data_nascimento", ""), "%Y-%m-%d").date()
    except ValueError:
        nasc = None
    if not nasc or not (date(1950, 1, 1) <= nasc <= agora().date()):
        flash("Informe a data de nascimento do aluno: ela é a senha inicial dele.", "erro")
        return redirect(url_for("alunos"))
    try:
        with get_db().cursor() as cur:
            cur.execute("INSERT INTO alunos (nome, matricula, turma, curso, campus, data_nascimento, sexo) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (nome, matricula, f.get("turma", "").strip() or None, f.get("curso", "").strip() or None,
                         f.get("campus", "").strip() or "Paulistana", nasc,
                         f.get("sexo") if f.get("sexo") in ("F", "M") else None))
            senha = criar_login_aluno(cur, cur.lastrowid, matricula, nome, nasc)
    except pymysql.err.IntegrityError:
        flash(f"Já existe um aluno com a matrícula {matricula}.", "erro")
        return redirect(url_for("alunos"))
    flash(f"Aluno {nome} cadastrado. Login: {matricula} · senha inicial: {senha} (data de nascimento). "
          "No primeiro acesso o aluno cria a própria senha.", "ok")
    return redirect(url_for("alunos"))


@app.route("/alunos/<int:aluno_id>/nova-senha", methods=["POST"])
@profissional_required
def nova_senha_aluno(aluno_id):
    """Para o aluno que perdeu a senha e não tem contato de recuperação cadastrado."""
    with get_db().cursor() as cur:
        cur.execute("SELECT nome, matricula, usuario_id, data_nascimento FROM alunos WHERE id = %s", (aluno_id,))
        al = cur.fetchone()
        if not al:
            return redirect(url_for("alunos"))
        senha = senha_aluno(al["data_nascimento"], al["matricula"])
        if not al["usuario_id"]:
            senha = criar_login_aluno(cur, aluno_id, al["matricula"], al["nome"], al["data_nascimento"])
        else:
            cur.execute("UPDATE usuarios SET senha_hash=%s, trocar_senha=1 WHERE id=%s AND perfil='aluno'",
                        (generate_password_hash(senha), al["usuario_id"]))
    origem = "data de nascimento" if al["data_nascimento"] else "matrícula — cadastre a data de nascimento do aluno"
    flash(f"Senha de {al['nome']} voltou para a inicial: {senha} ({origem}). Login: {al['matricula']}. "
          "No próximo acesso o aluno cria uma senha nova.", "ok")
    return redirect(url_for("alunos"))




NIVEIS = ["Operador", "Supervisor"]


def ler_usuario(f):
    nome = f.get("nome", "").strip()
    if not nome:
        return None, "Informe o nome completo."
    nivel = f.get("nivel") if f.get("nivel") in NIVEIS else "Operador"
    siape = "".join(ch for ch in f.get("siape", "") if ch.isdigit())[:20] or None
    return {"nome": nome[:120], "cargo": f.get("cargo", "").strip()[:80] or None,
            "campus": f.get("campus", "").strip()[:60] or "Paulistana", "nivel": nivel, "siape": siape}, None


def supervisores_ativos_exceto(cur, uid):
    cur.execute("SELECT COUNT(*) n FROM usuarios WHERE perfil <> 'aluno' AND ativo = 1 AND nivel = 'Supervisor' AND id <> %s", (uid,))
    return cur.fetchone()["n"]


@app.route("/usuarios")
@supervisor_required
def usuarios():
    aba = "atividades" if request.args.get("aba") == "atividades" else "profissionais"
    with get_db().cursor() as cur:
        cur.execute("SELECT u.*, (SELECT MAX(l.data_hora) FROM log_acessos l WHERE l.usuario = u.usuario AND l.sucesso = 1) AS ultimo "
                    "FROM usuarios u WHERE u.perfil <> 'aluno' ORDER BY u.nome")
        lista = cur.fetchall()
        atividades = []
        if aba == "atividades":
            cur.execute("SELECT l.*, u.nome FROM log_acessos l LEFT JOIN usuarios u ON u.usuario = l.usuario "
                        "ORDER BY l.data_hora DESC, l.id DESC LIMIT 100")
            atividades = cur.fetchall()
    return render_template("usuarios.html", aba=aba, lista=lista, atividades=atividades, niveis=NIVEIS,
                           ativos=sum(1 for u in lista if u["ativo"]))


@app.route("/usuarios/novo", methods=["POST"])
@supervisor_required
def novo_usuario():
    f = request.form
    email = f.get("email", "").strip().lower()
    d, erro = ler_usuario(f)
    if email and "@" not in email:
        email += DOMINIO
    if not erro and not normalizar_email(email):
        erro = "Informe um e-mail institucional válido."
    if erro:
        flash(erro, "erro")
        return redirect(url_for("usuarios"))
    senha = SENHA_PADRAO_SERVIDOR
    try:
        with get_db().cursor() as cur:
            cur.execute("INSERT INTO usuarios (usuario, nome, cargo, campus, nivel, siape, senha_hash, perfil) "
                        "VALUES (%s,%s,%s,%s,%s,%s,%s,'profissional')",
                        (email, d["nome"], d["cargo"], d["campus"], d["nivel"], d["siape"], generate_password_hash(senha)))
    except pymysql.err.IntegrityError:
        flash(f"Já existe um usuário com o e-mail {email}.", "erro")
        return redirect(url_for("usuarios"))
    flash(f"Usuário {d['nome']} criado. Senha inicial: {senha} (padrão dos servidores). "
          "No primeiro acesso a pessoa cria a própria senha.", "ok")
    return redirect(url_for("usuarios"))


@app.route("/usuarios/<int:uid>/editar", methods=["POST"])
@supervisor_required
def editar_usuario(uid):
    f = request.form
    d, erro = ler_usuario(f)
    if erro:
        flash(erro, "erro")
        return redirect(url_for("usuarios"))
    msg = f"Usuário {d['nome']} atualizado."
    with get_db().cursor() as cur:
        if d["nivel"] != "Supervisor" and not supervisores_ativos_exceto(cur, uid):
            cur.execute("SELECT nivel FROM usuarios WHERE id = %s", (uid,))
            atual = cur.fetchone()
            if atual and atual["nivel"] == "Supervisor":
                flash("O sistema precisa de pelo menos um supervisor ativo.", "erro")
                return redirect(url_for("usuarios"))
        cur.execute("UPDATE usuarios SET nome=%s, cargo=%s, campus=%s, nivel=%s, siape=%s WHERE id=%s AND perfil <> 'aluno'",
                    (d["nome"], d["cargo"], d["campus"], d["nivel"], d["siape"], uid))
        if f.get("nova_senha"):
            senha = SENHA_PADRAO_SERVIDOR
            cur.execute("UPDATE usuarios SET senha_hash=%s, trocar_senha=1 WHERE id=%s AND perfil <> 'aluno'",
                        (generate_password_hash(senha), uid))
            msg += f" A senha voltou para a inicial: {senha}. No próximo acesso a pessoa cria uma nova."
    if uid == session["user_id"]:
        session["nome"], session["cargo"], session["nivel"] = d["nome"], d["cargo"] or "Profissional", d["nivel"]
    flash(msg)
    return redirect(url_for("usuarios"))


@app.route("/usuarios/<int:uid>/status", methods=["POST"])
@supervisor_required
def status_usuario(uid):
    if uid == session["user_id"]:
        flash("Você não pode desativar o seu próprio usuário.", "erro")
        return redirect(url_for("usuarios"))
    with get_db().cursor() as cur:
        cur.execute("SELECT nome, ativo, nivel FROM usuarios WHERE id = %s AND perfil <> 'aluno'", (uid,))
        u = cur.fetchone()
        if not u:
            return redirect(url_for("usuarios"))
        if u["ativo"] and u["nivel"] == "Supervisor" and not supervisores_ativos_exceto(cur, uid):
            flash("O sistema precisa de pelo menos um supervisor ativo.", "erro")
            return redirect(url_for("usuarios"))
        cur.execute("UPDATE usuarios SET ativo = %s WHERE id = %s", (0 if u["ativo"] else 1, uid))
    flash(f"Usuário {u['nome']} {'desativado' if u['ativo'] else 'reativado'}.")
    return redirect(url_for("usuarios"))


@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("login"))

