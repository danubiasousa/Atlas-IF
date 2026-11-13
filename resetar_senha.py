"""Gera uma nova senha temporária para um usuário do ATLAS IF.

Uso (na pasta do projeto, com o MySQL do XAMPP ligado):
    python resetar_senha.py mariana.moura
    python resetar_senha.py 2025120IIPI0009      (aluno: matrícula)
"""
import os
import sys

import pymysql
from werkzeug.security import generate_password_hash

from seguranca import DOMINIO, senha_temporaria

if len(sys.argv) != 2:
    sys.exit("Uso: python resetar_senha.py nome.sobrenome   (ou a matrícula do aluno)")

usuario = sys.argv[1].strip().lower()
if "@" not in usuario and not usuario[0].isdigit():
    usuario += DOMINIO

senha = senha_temporaria()
con = pymysql.connect(host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", 3306)),
                      user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", ""),
                      database=os.getenv("DB_NAME", "atlas_if"), charset="utf8mb4", autocommit=True)
with con.cursor() as cur:
    alterados = cur.execute("UPDATE usuarios SET senha_hash=%s, trocar_senha=1 WHERE usuario=%s",
                            (generate_password_hash(senha), usuario))
con.close()

if alterados:
    print(f"Usuário: {usuario}\nSenha temporária: {senha}\n"
          "No próximo login, a pessoa vai criar a própria senha.")
else:
    print(f"Usuário {usuario} não encontrado.")
