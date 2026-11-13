"""Agendamentos: portal do aluno, horários disponíveis, painel do profissional e resposta às solicitações (Geovane)."""
from nucleo import *  

@app.route("/painel")
@profissional_required
def painel():
    def um(cur, sql, args=()):
        cur.execute(sql, args)
        return cur.fetchone()["n"]

    with get_db().cursor() as cur:
        hoje_n = um(cur, "SELECT COUNT(*) n FROM atendimentos WHERE DATE(data_hora)=CURDATE()")
        ontem_n = um(cur, "SELECT COUNT(*) n FROM atendimentos WHERE DATE(data_hora)=CURDATE()-INTERVAL 1 DAY")
        stats = {
            "hoje": hoje_n,
            "diff": hoje_n - ontem_n,
            "retornos": um(cur, "SELECT COUNT(*) n FROM retornos WHERE status='pendente'"),
            "urgentes": um(cur, "SELECT COUNT(*) n FROM retornos WHERE status='pendente' AND urgente=1"),
            "encaminhamentos": um(cur, "SELECT COUNT(*) n FROM atendimentos WHERE status='Encaminhado' "
                                       "AND YEAR(data_hora)=YEAR(CURDATE()) AND MONTH(data_hora)=MONTH(CURDATE())"),
            "em_falta": um(cur, "SELECT COUNT(*) n FROM estoque WHERE ideal > 0 AND quantidade < ideal*%s", (LIMITE_CRITICO,)),
        }
        cur.execute("SELECT * FROM solicitacoes WHERE status='pendente' AND profissional_id=%s ORDER BY criado_em DESC",
                    (session["user_id"],))
        solicitacoes = cur.fetchall()
        cur.execute("SELECT * FROM atendimentos ORDER BY data_hora DESC LIMIT 5")
        recentes = cur.fetchall()
        cur.execute("SELECT * FROM retornos WHERE status='pendente' ORDER BY data_hora LIMIT 5")
        retornos = cur.fetchall()
        cur.execute("SELECT *, quantidade/ideal AS pct FROM estoque WHERE ideal > 0 AND quantidade < ideal*%s ORDER BY pct LIMIT 5",
                    (LIMITE_CRITICO,))
        estoque = cur.fetchall()

    hoje = date.today()
    return render_template(
        "painel.html", stats=stats, solicitacoes=solicitacoes, recentes=recentes,
        retornos=retornos, estoque=estoque,
        data_longa=f"{DIAS[hoje.weekday()]}, {hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}",
        data_curta=f"{hoje.day:02d} de {MESES[hoje.month - 1][:3]}. de {hoje.year}",
    )

JANELAS = {"Manhã": (time(8, 0), time(12, 30), "8h00 às 12h30"), "Tarde": (time(14, 0), time(18, 0), "14h00 às 18h00")}
DIA_TODO = ("Manhã", "Tarde")