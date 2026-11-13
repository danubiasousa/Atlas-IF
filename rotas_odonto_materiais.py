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

    def ler_material(f):
    item = f.get("item", "").strip()
    if not item:
        return None, "Informe o nome do item."
    try:
        qtd, minimo = int(f.get("quantidade", "")), int(f.get("ideal", ""))
    except ValueError:
        return None, "Informe a quantidade atual e o estoque mínimo (números inteiros)."
    if qtd < 0 or minimo < 0:
        return None, "Quantidade e estoque mínimo não podem ser negativos."
    try:
        validade = datetime.strptime(f.get("validade", ""), "%Y-%m").date()
    except ValueError:
        validade = None
    return {
        "item": item[:80], "categoria": f.get("categoria", "").strip()[:40] or None,
        "unidade": f.get("unidade", "").strip()[:20] or "un.", "fornecedor": f.get("fornecedor", "").strip()[:80] or None,
        "quantidade": qtd, "ideal": minimo, "validade": validade,
    }, None


@app.route("/materiais")
@profissional_required
def materiais():
    q, cat, status = (request.args.get(k, "").strip() for k in ("q", "categoria", "status"))
    with get_db().cursor() as cur:
        cur.execute("SELECT * FROM estoque ORDER BY id")
        itens = cur.fetchall()
    contagem = {"Crítico": 0, "Baixo": 0, "Normal": 0}
    for it in itens:
        it["status"], it["pct"] = classificar_estoque(it["quantidade"], it["ideal"])
        contagem[it["status"]] += 1
    categorias = sorted({i["categoria"] for i in itens if i["categoria"]} | set(CATEGORIAS))
    mostrados = [i for i in itens
                 if (not q or q.lower() in f"{i['item']} {i['fornecedor'] or ''}".lower())
                 and (not cat or i["categoria"] == cat) and (not status or i["status"] == status)]
    return render_template("materiais.html", itens=mostrados, total=len(itens), contagem=contagem,
                           categorias=categorias, q=q, cat=cat, status=status,
                           filtrado=bool(q or cat or status), hoje_mes=date.today().strftime("%Y-%m"))