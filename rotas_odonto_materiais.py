"""Odontograma e controle de materiais e medicamentos (Sthefany)."""
from nucleo import *  

ODONTO_CARGOS = ("Dentista", "Técnico em Saúde Bucal")
DENTES = [18,17,16,15,14,13,12,11,21,22,23,24,25,26,27,28,48,47,46,45,44,43,42,41,31,32,33,34,35,36,37,38]
FACES = ["Oclusal/Incisal", "Vestibular", "Lingual/Palatina", "Mesial", "Distal"]
SITUACOES = ["Planejado", "Em andamento", "Concluído"]
PROC_ODONTO = ["Avaliação", "Restauração", "Limpeza (profilaxia)", "Raspagem", "Aplicação de flúor", "Selante",
               "Tratamento de cárie", "Endodontia", "Exodontia", "Orientação de higiene bucal", "Outro"]
BOCA_TODA = ["Limpeza (profilaxia)", "Raspagem", "Aplicação de flúor", "Avaliação", "Orientação de higiene bucal"]
TODOS_DENTES = 0


def nome_dente(n):
    return "Todos os dentes" if n == TODOS_DENTES else f"Dente {n}"