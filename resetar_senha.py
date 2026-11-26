import os
import sys

import pymysql
from werkzeug.security import generate_password_hash

SENHA_SERVIDOR = "setorsaude2026"

con = pymysql.connect(host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", 3306)),
                      user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", ""),
                      database=os.getenv("DB_NAME", "atlas_if"), charset="utf8mb4", autocommit=True,
                      cursorclass=pymysql.cursors.DictCursor)
cur = con.cursor()

cur.execute("SELECT u.id, u.usuario, u.perfil, al.matricula, al.data_nascimento FROM usuarios u "
            "LEFT JOIN alunos al ON al.usuario_id = u.id")
usuarios = cur.fetchall()

for u in usuarios:
    if u["perfil"] == "aluno" and u["data_nascimento"]:
        senha = u["data_nascimento"].strftime("%d%m%Y")
    elif u["perfil"] == "aluno" and u["matricula"]:
        senha = u["matricula"]
    else:
        senha = SENHA_SERVIDOR
    cur.execute("UPDATE usuarios SET senha_hash=%s, trocar_senha=1 WHERE id=%s",
                (generate_password_hash(senha), u["id"]))
    print(f"{u['usuario']}: {senha}")

cur.execute("DELETE FROM codigos_recuperacao")
con.close()

print(f"\n{len(usuarios)} senha(s) voltaram para a inicial. No próximo login, cada pessoa cria a própria senha.")