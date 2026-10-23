
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