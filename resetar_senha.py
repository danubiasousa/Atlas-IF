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