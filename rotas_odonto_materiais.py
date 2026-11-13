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

    def usa_odonto():
    return session.get("cargo") in ODONTO_CARGOS


def ler_odonto(texto, data_padrao):
    """Valida o JSON de procedimentos do odontograma enviado pelo formulário."""
    try:
        itens = json.loads(texto or "[]")
    except ValueError:
        return []
    saida = []
    for r in itens if isinstance(itens, list) else []:
        try:
            dente = int(r.get("dente"))
        except (TypeError, ValueError):
            continue
        procedimento = str(r.get("procedimento", "Avaliação"))[:80]
        if dente not in DENTES and not (dente == TODOS_DENTES and procedimento in BOCA_TODA):
            continue
        try:
            data = datetime.strptime(str(r.get("data")), "%Y-%m-%d").date()
        except ValueError:
            data = data_padrao
        situacao = r.get("situacao") if r.get("situacao") in SITUACOES else "Planejado"
        faces = ", ".join(x for x in r.get("faces", []) if x in FACES)
        rid = r.get("id")
        saida.append({"id": int(rid) if str(rid or "").isdigit() else None, "dente": dente,
                      "procedimento": procedimento, "faces": "" if dente == TODOS_DENTES else faces,
                      "situacao": situacao, "data": data, "observacoes": str(r.get("observacoes", "")).strip() or None})
    return saida

    @app.route("/api/alunos/<int:aluno_id>/odonto")
@profissional_required
def api_odonto(aluno_id):
    with get_db().cursor() as cur:
        cur.execute("SELECT id, dente, procedimento, faces, situacao, data, observacoes FROM procedimentos_odonto "
                    "WHERE aluno_id = %s ORDER BY data DESC, id DESC", (aluno_id,))
        linhas = cur.fetchall()
    for r in linhas:
        r["data"] = r["data"].isoformat()
    return jsonify(linhas)

def classificar_estoque(qtd, minimo):
    """Normal: qtd >= mínimo · Crítico: menos de 50% do mínimo · Baixo: o resto."""
    if not minimo or qtd >= minimo:
        return "Normal", 100
    pct = int(qtd / minimo * 100 + 0.5)
    return ("Crítico" if qtd * 2 < minimo else "Baixo"), pct