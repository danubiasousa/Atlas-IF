"""ATLAS IF – núcleo do sistema (Danúbia).

Configuração do Flask, conexão com o MySQL, criação das tabelas (init_db),
controle de acesso (decorators) e filtros usados nas telas.
Os arquivos rotas_*.py importam tudo daqui com:  from nucleo import *
"""
import json
import re
import os
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from functools import wraps
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor
from flask import Flask, render_template, request, redirect, url_for, session, flash, g, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from usuarios_seed import USUARIOS_INICIAIS
from calendario import motivo_bloqueio, proximo_dia_util, ULTIMO_DIA_CALENDARIO
from seguranca import (DOMINIO, REGRAS_SENHA, ESPECIAIS, SENHA_PADRAO_SERVIDOR, senha_aluno, erros_senha, mensagem_erros,
                       normalizar_email, normalizar_telefone, mascarar_email, mascarar_telefone,
                       gerar_codigo, enviar_codigo)

BASE = Path(__file__).parent
VERSAO = "v2.6.0"
LIMITE_CRITICO = 0.5  

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "charset": "utf8mb4",
    "cursorclass": DictCursor,
    "autocommit": True,
}
DB_NAME = os.getenv("DB_NAME", "atlas_if")

CATEGORIAS = ["Antisséptico", "Curativo", "Descartável", "Equipamento", "EPI", "Medicamento"]
MATERIAIS_INICIAIS = [
    ("Álcool 70%", "Antisséptico", "frascos 500ml", "Cirúrgica Piauí", 2, 10, "2025-06"),
    ("Luva Procedimento M", "EPI", "pares", "MedSupply", 5, 20, "2026-03"),
    ("Dipirona 500mg", "Medicamento", "caixas 20cp", "Farmácia Central", 3, 15, "2025-02"),
    ("Seringa 5ml", "Descartável", "un.", "MedSupply", 8, 30, "2027-01"),
    ("Gaze Estéril 7,5×7,5", "Curativo", "embalagens", "Cirúrgica Piauí", 24, 50, "2026-08"),
    ("Esparadrapo 4,5m", "Curativo", "rolos", "Cirúrgica Piauí", 6, 10, "2026-12"),
    ("Termômetro Digital", "Equipamento", "un.", "TechMed", 2, 3, None),
    ("Paracetamol 750mg", "Medicamento", "caixas 20cp", "Farmácia Central", 18, 15, "2025-09"),
    ("Soro Fisiológico 0,9%", "Medicamento", "frascos 250ml", "Farmácia Central", 12, 10, "2025-11"),
    ("Luva Procedimento G", "EPI", "pares", "MedSupply", 40, 20, "2026-03"),
    ("Atadura 10cm", "Curativo", "rolos", "Cirúrgica Piauí", 15, 20, "2027-06"),
    ("Oxímetro de pulso", "Equipamento", "un.", "TechMed", 1, 2, None),
]

try:
    TZ = ZoneInfo("America/Sao_Paulo")      
except Exception:                           
    TZ = timezone(timedelta(hours=-3))


def agora():
    return datetime.now(TZ).replace(tzinfo=None)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "troque-esta-chave-em-producao")

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

def get_db():
    if "db" not in g:
        g.db = pymysql.connect(database=DB_NAME, **DB_CONFIG)
    return g.db

    @app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    """Cria banco, tabelas, usuários autorizados e dados de exemplo."""
    con = pymysql.connect(**DB_CONFIG)
    with con.cursor() as cur:
        sql = (BASE / "schema.sql").read_text(encoding="utf-8")
        for comando in sql.split(";"):
            linhas = [l for l in comando.splitlines() if not l.strip().startswith("--")]
            comando = "\n".join(linhas).strip()
            if comando:
                cur.execute(comando)

        cur.execute("SHOW COLUMNS FROM usuarios LIKE 'cargo'")
        if not cur.fetchone():
            cur.execute("ALTER TABLE usuarios ADD COLUMN cargo VARCHAR(80) NULL AFTER perfil")
        cur.execute("ALTER TABLE usuarios MODIFY usuario VARCHAR(120) NOT NULL")
        cur.execute("UPDATE IGNORE usuarios SET usuario = LOWER(TRIM(usuario)) WHERE usuario <> LOWER(TRIM(usuario))")

        cur.execute("DELETE FROM usuarios WHERE usuario = 'admin'")
        for usuario, nome, cargo, senha_hash in USUARIOS_INICIAIS:
            cur.execute(
                """INSERT INTO usuarios (usuario, nome, cargo, senha_hash, perfil)
                   VALUES (%s,%s,%s,%s,'profissional')
                   ON DUPLICATE KEY UPDATE nome=VALUES(nome), cargo=VALUES(cargo)""",
                (usuario, nome, cargo, senha_hash),
            )

        extras = {
            "codigo": "VARCHAR(20) NULL", "aluno_id": "INT UNSIGNED NULL", "profissional_id": "INT UNSIGNED NULL",
            "matricula": "VARCHAR(30) NULL", "tipo": "VARCHAR(20) NOT NULL DEFAULT 'Atendimento'",
            "em_aula": "TINYINT(1) NOT NULL DEFAULT 0", "historico": "TEXT NULL", "alergias": "VARCHAR(255) NULL",
            "medicamentos_uso": "VARCHAR(255) NULL", "doencas": "VARCHAR(255) NULL", "encaminhado_por": "VARCHAR(120) NULL",
            "pressao": "VARCHAR(20) NULL", "fc": "VARCHAR(20) NULL", "fr": "VARCHAR(20) NULL",
            "temperatura": "VARCHAR(20) NULL", "saturacao": "VARCHAR(20) NULL", "peso": "VARCHAR(20) NULL",
            "glicemia": "VARCHAR(20) NULL", "procedimentos": "VARCHAR(600) NULL", "medicamentos_adm": "TEXT NULL",
            "enc_externo": "TINYINT(1) NOT NULL DEFAULT 0", "agendar_retorno": "TINYINT(1) NOT NULL DEFAULT 0",
            "orientacoes": "TEXT NULL", "observacoes": "TEXT NULL",
            "altura": "VARCHAR(20) NULL", "imc": "VARCHAR(60) NULL",
        }
        for col, ddl in extras.items():
            cur.execute("SHOW COLUMNS FROM atendimentos LIKE %s", (col,))
            if not cur.fetchone():
                cur.execute(f"ALTER TABLE atendimentos ADD COLUMN {col} {ddl}")

        for col, ddl in {"data_nascimento": "DATE NULL", "curso": "VARCHAR(120) NULL", "campus": "VARCHAR(60) NULL",
                         "sexo": "CHAR(1) NULL"}.items():
            cur.execute("SHOW COLUMNS FROM alunos LIKE %s", (col,))
            if not cur.fetchone():
                cur.execute(f"ALTER TABLE alunos ADD COLUMN {col} {ddl}")

        cur.execute("SELECT COUNT(*) n FROM alunos")
        if cur.fetchone()["n"] == 0:
            cur.executemany(
                "INSERT INTO alunos (nome, matricula, turma, data_nascimento) VALUES (%s,%s,%s,%s)",
                [("Danúbia Coelho de Sousa", "2025120IIPI0009", "2° INFO", date(2009, 4, 19)),
                 ("Geovane Moura Gomes", "2025120IIPI0012", "2° INFO", date(2010, 1, 28)),
                 ("Maria Aparecida Coelho de Sousa", "2025120IIPI0032", "2° INFO", date(2009, 10, 21)),
                 ("Sthefany Kailane Lima de Sousa", "2025120IIPI0036", "2° INFO", date(2010, 3, 20))],
            )

        cur.execute("SELECT COUNT(*) n FROM procedimentos_odonto")
        if cur.fetchone()["n"] == 0:
            cur.execute("SELECT id, nome FROM alunos WHERE matricula = '2025120IIPI0009'")
            al = cur.fetchone()
            if al:
                cur.executemany(
                    "INSERT INTO procedimentos_odonto (aluno_id, aluno_nome, dente, procedimento, faces, situacao, data, observacoes) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    [(al["id"], al["nome"], 11, "Restauração", "Vestibular", "Concluído", date(2025, 4, 18), "Restauração em resina composta, sem intercorrências."),
                     (al["id"], al["nome"], 26, "Selante", "Oclusal/Incisal", "Concluído", date(2025, 6, 2), "Selante aplicado, sem intercorrências."),
                     (al["id"], al["nome"], 36, "Avaliação", "Oclusal/Incisal", "Planejado", date(2025, 6, 2), "Acompanhar evolução.")],
                )

        cur.execute("SELECT COUNT(*) n FROM atendimentos")
        if cur.fetchone()["n"] == 0:
            hoje = agora().date()
            dt = lambda d, h, m: datetime.combine(d, time(h, m))
            cur.executemany(
                "INSERT INTO atendimentos (aluno_nome, queixa, turma, status, data_hora) VALUES (%s,%s,%s,%s,%s)",
                [
                    ("Geovane Moura Gomes", "Cefaleia intensa", "2° INFO", "Concluído", dt(hoje, 14, 32)),
                    ("Danúbia Coelho de Sousa", "Dor abdominal leve", "2° INFO", "Retorno", dt(hoje, 13, 15)),
                    ("Sthefany Kailane Lima de Sousa", "Corte na mão direita", "2° INFO", "Concluído", dt(hoje, 11, 48)),
                    ("Maria Aparecida Coelho de Sousa", "Alergia cutânea", "2° INFO", "Encaminhado", dt(hoje, 10, 22)),
                    ("Geovane Moura Gomes", "Dor de garganta", "2° INFO", "Concluído", dt(hoje - timedelta(days=1), 9, 40)),
                ],
            )
            cur.executemany(
                "INSERT INTO retornos (aluno_nome, motivo, data_hora, urgente) VALUES (%s,%s,%s,%s)",
                [
                    ("Danúbia Coelho de Sousa", "Dor abdominal – verificar evolução", dt(hoje, 16, 0), 1),
                    ("Maria Aparecida Coelho de Sousa", "Resultado encaminhamento alergia", dt(hoje + timedelta(days=1), 8, 30), 0),
                ],
            )
            cur.executemany(
                "INSERT INTO estoque (item, quantidade, ideal, unidade) VALUES (%s,%s,%s,%s)",
                [("Álcool 70%", 2, 10, "frascos"), ("Luva M", 5, 20, "pares"),
                 ("Dipirona 500mg", 3, 15, "caixas"), ("Seringa 5ml", 8, 30, "un.")],
            )