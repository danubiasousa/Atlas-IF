"""Senhas iniciais, política de senha e envio de códigos de recuperação."""
import json
import os
import re
import secrets
import smtplib
import urllib.request
from email.message import EmailMessage

DOMINIO = "@ifpi.edu.br"

ESPECIAIS = "!@#$%&*()-_=+[]{};:,.?/\\|~^"
REGRAS_SENHA = [
    ("min", "No mínimo 6 caracteres"),
    ("mai", "Uma letra maiúscula"),
    ("min_l", "Uma letra minúscula"),
    ("num", "Um número"),
    ("esp", "Um caractere especial (! @ # $ % & * ...)"),
]



SENHA_PADRAO_SERVIDOR = "setorsaude2026"


def senha_aluno(data_nascimento, matricula):
    """Senha inicial do aluno: data de nascimento tudo junto (19042009).
    Sem data de nascimento cadastrada, usa a matrícula."""
    return data_nascimento.strftime("%d%m%Y") if data_nascimento else matricula


def erros_senha(senha, usuario=""):
    """Lista os requisitos que a senha não cumpre (lista vazia = senha válida)."""
    erros = []
    if len(senha) < 6:
        erros.append("ter no mínimo 6 caracteres")
    if not re.search(r"[A-ZÀ-Ý]", senha):
        erros.append("ter uma letra maiúscula")
    if not re.search(r"[a-zß-ÿ]", senha):
        erros.append("ter uma letra minúscula")
    if not re.search(r"\d", senha):
        erros.append("ter um número")
    if not any(c in ESPECIAIS for c in senha):
        erros.append("ter um caractere especial")
    if " " in senha:
        erros.append("não ter espaços")
    partes = re.split(r"[.\-_]", usuario.split("@")[0].lower())
    if any(len(p) >= 4 and p in senha.lower() for p in partes):
        erros.append("não conter o seu nome de usuário")
    return erros


def mensagem_erros(erros):
    return "A senha precisa " + ", ".join(erros) + "." if erros else ""



def normalizar_email(texto):
    e = (texto or "").strip().lower()
    return e if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", e) and len(e) <= 120 else None


def normalizar_telefone(texto):
    """Aceita (89)99999-9999, 89999999999, +55 89 ... → '(89)99999-9999'."""
    d = re.sub(r"\D", "", texto or "")
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if len(d) not in (10, 11) or d[0] == "0":
        return None
    return f"({d[:2]}){d[2:-4]}-{d[-4:]}"


def mascarar_email(e):
    nome, dom = e.split("@", 1)
    vis = nome[0] + "•" * max(len(nome) - 2, 1) + (nome[-1] if len(nome) > 1 else "")
    return f"{vis}@{dom}"


def mascarar_telefone(t):
    d = re.sub(r"\D", "", t)
    return f"({d[:2]})•••••-{d[-4:]}"



def gerar_codigo():
    return f"{secrets.randbelow(1_000_000):06d}"


def enviar_email(destino, assunto, texto):
    """Envia por SMTP se configurado (variáveis SMTP_*); senão mostra no terminal.

    Devolve "enviado", "simulado" (só no terminal) ou None (falhou)."""
    host = os.getenv("SMTP_HOST")
    if not host:
        print(f"\n[ATLAS IF · e-mail simulado] Para: {destino}\n{assunto}\n{texto}\n", flush=True)
        return "simulado"
    msg = EmailMessage()
    msg["From"] = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "nao-responda@ifpi.edu.br"))
    msg["To"], msg["Subject"] = destino, assunto
    msg.set_content(texto)
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", 587)), timeout=15) as s:
            s.starttls()
            if os.getenv("SMTP_USER"):
                s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD", ""))
            s.send_message(msg)
        return "enviado"
    except Exception as exc:  
        print(f"[ATLAS IF] Falha ao enviar e-mail: {exc}", flush=True)
        return None


def enviar_sms(telefone, texto):
    """Envia via webhook do provedor de SMS (SMS_WEBHOOK_URL); senão mostra no terminal.

    O webhook recebe um POST JSON {"telefone": "+5589999999999", "mensagem": "..."}.
    Use o serviço que o campus contratar (Twilio, Zenvia, etc.).
    """
    url = os.getenv("SMS_WEBHOOK_URL")
    numero = "+55" + re.sub(r"\D", "", telefone)
    if not url:
        print(f"\n[ATLAS IF · SMS simulado] Para: {numero}\n{texto}\n", flush=True)
        return "simulado"
    corpo = json.dumps({"telefone": numero, "mensagem": texto}).encode()
    req = urllib.request.Request(url, data=corpo, headers={"Content-Type": "application/json"})
    if os.getenv("SMS_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.getenv('SMS_TOKEN')}")
    try:
        urllib.request.urlopen(req, timeout=15)
        return "enviado"
    except Exception as exc:  
        print(f"[ATLAS IF] Falha ao enviar SMS: {exc}", flush=True)
        return None


def enviar_codigo(canal, destino, codigo, nome):
    texto = (f"Olá, {nome.split()[0]}!\n\nSeu código para redefinir a senha do ATLAS IF é: {codigo}\n"
             "Ele vale por 1 minuto. Se não foi você quem pediu, ignore esta mensagem.")
    if canal == "email":
        return enviar_email(destino, "ATLAS IF – código de recuperação de senha", texto)
    return enviar_sms(destino, f"ATLAS IF: seu codigo de recuperacao de senha e {codigo}. Vale por 1 min.")
