
class Paciente:
    def __init__(
        self,
        nome,
        matricula,
        curso,
        telefone=None,
        email=None
    ):
        self.nome = nome
        self.matricula = matricula
        self.curso = curso
        self.telefone = telefone
        self.email = email
    def to_dict(self):
        return {
            "nome": self.nome,
            "matricula": self.matricula,
            "curso": self.curso,
            "telefone": self.telefone,
            "email": self.email
        }
class ProfissionalSaude:
    def __init__(
        self,
        nome,
        especialidade,
        turno,
        id_profissional=None
    ):
        self.id_profissional = id_profissional
        self.nome = nome
        self.especialidade = especialidade
        self.turno = turno
    def to_dict(self):
        return {
            "id_profissional": self.id_profissional,
            "nome": self.nome,
            "especialidade": self.especialidade,
            "turno": self.turno
        }
    def atende_no_turno(self, turno):
        return self.turno.lower() == turno.lower()
from datetime import datetime
class Agendamento:
    def __init__(
        self,
        paciente,
        profissional,
        data,
        horario,
        status="Agendado",
        id_agendamento=None
    ):
        self.id_agendamento = id_agendamento
        self.paciente = paciente
        self.profissional = profissional
        self.data = data
        self.horario = horario
        self.status = status
    def cancelar(self):
        self.status = "Cancelado"
    def confirmar(self):
        self.status = "Confirmado"
    def validar_data(self):
        try:
            data_agendamento = datetime.strptime(
                self.data, "%Y-%m-%d"
            )
            return data_agendamento.date() >= datetime.now().date()
        except ValueError:
            return False     