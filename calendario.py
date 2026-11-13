"""Calendário acadêmico 2026 – IFPI Campus Paulistana (cursos técnicos integrados).

Dias em que o Setor de Saúde NÃO aceita agendamento:
  * sábados e domingos;
  * feriados e pontos facultativos do calendário;
  * recesso natalino.

Para o próximo ano, basta acrescentar as datas em DIAS_SEM_ATENDIMENTO
e ajustar ULTIMO_DIA_CALENDARIO.
"""
from datetime import date, timedelta

DIAS_SEM_ATENDIMENTO = {
    date(2026, 1, 1): "Confraternização Universal",
    date(2026, 2, 16): "Carnaval",
    date(2026, 2, 17): "Carnaval",
    date(2026, 4, 2): "Quinta-feira Santa",
    date(2026, 4, 3): "Sexta-feira Santa",
    date(2026, 4, 21): "Tiradentes",
    date(2026, 5, 1): "Dia do Trabalhador",
    date(2026, 6, 4): "Corpus Christi",
    date(2026, 7, 15): "Dia do Evangélico",
    date(2026, 9, 7): "Independência do Brasil",
    date(2026, 10, 12): "Nossa Senhora Aparecida",
    date(2026, 10, 15): "Dia do Professor e do TAE",
    date(2026, 10, 19): "Dia do Piauí",
    date(2026, 10, 28): "Dia do Servidor Público",
    date(2026, 11, 2): "Finados",
    date(2026, 11, 15): "Proclamação da República",
    date(2026, 11, 20): "Dia da Consciência Negra",
    date(2026, 12, 15): "Feriado municipal",
    date(2026, 12, 25): "Natal",
    date(2027, 1, 1): "Confraternização Universal",
}

for _d in range(21, 32):
    DIAS_SEM_ATENDIMENTO.setdefault(date(2026, 12, _d), "Recesso natalino")

ULTIMO_DIA_CALENDARIO = date(2027, 1, 31)


def motivo_bloqueio(d):
    """Devolve o motivo de não haver atendimento no dia, ou None se for dia útil."""
    if d.weekday() == 5:
        return "Sábado – sem atendimento"
    if d.weekday() == 6:
        return "Domingo – sem atendimento"
    if d in DIAS_SEM_ATENDIMENTO:
        return f"{DIAS_SEM_ATENDIMENTO[d]} – sem atendimento"
    if d > ULTIMO_DIA_CALENDARIO:
        return "Data fora do calendário acadêmico vigente"
    return None


def dia_util(d):
    return motivo_bloqueio(d) is None


def proximo_dia_util(d):
    """O próprio dia, se for útil; senão o próximo dia útil (ou None se passar do calendário)."""
    while d <= ULTIMO_DIA_CALENDARIO:
        if dia_util(d):
            return d
        d += timedelta(days=1)
    return None