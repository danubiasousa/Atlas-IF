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