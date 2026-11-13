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