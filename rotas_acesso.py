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