from datetime import datetime
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
            return (
                data_agendamento.date()
                >= datetime.now().date()
            )
        except ValueError:
            return False
if __name__ == "__main__":
    paciente = Paciente(
        nome="Maria Silva",
        matricula="2026001",
        curso="Informática para Internet",
        telefone="89999999999",
        email="maria@email.com"
    )
    profissional = ProfissionalSaude(
        nome="Sthefany",
        especialidade="Enfermagem",
        turno="Tarde",
        id_profissional=1
    )
    agendamento = Agendamento(
        paciente=paciente,
        profissional=profissional,
        data="2026-10-30",
        horario="14:00"
    )
    print("~ATLAS IF~")
    print("\nPACIENTE:")
    print(paciente.to_dict())
    print("\nPROFISSIONAL DE SAÚDE:")
    print(profissional.to_dict())
    print("\nAGENDAMENTO:")
    print("Paciente:", agendamento.paciente.nome)
    print("Profissional:", agendamento.profissional.nome)
    print("Data:", agendamento.data)
    print("Horário:", agendamento.horario)
    print("Status:", agendamento.status)
    print("Data válida:", agendamento.validar_data())
    agendamento.confirmar()
    print("Após confirmação:", agendamento.status)
    agendamento.cancelar()
    print("Após cancelamento:", agendamento.status)