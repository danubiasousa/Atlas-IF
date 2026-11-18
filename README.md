# ATLAS IF

Sistema do Setor de Saúde do IFPI Campus Paulistana.

## O que o sistema faz

- Login para profissionais e alunos, com recuperação de senha por código enviado ao e-mail ou celular
- Cadastro de alunos e de profissionais do setor
- Marcação de atendimento pelo aluno: ele escolhe enfermagem ou odontologia, o profissional e o horário. Sábados, domingos, feriados e pontos facultativos do calendário acadêmico ficam bloqueados
- Registro do atendimento em etapas: identificação, anamnese, sinais vitais, procedimentos e orientações
- Sinais vitais em verde, amarelo ou vermelho de acordo com o valor, e IMC calculado sozinho pela tabela de idade
- Odontograma para registrar o procedimento de cada dente, ou de todos os dentes no caso de limpeza e raspagem
- Histórico de atendimentos com busca por nome, tipo e data
- Declaração de comparecimento preenchida automaticamente, para o aluno que veio no horário de aula
- Controle de materiais e medicamentos, com aviso quando o estoque está baixo
- Funciona no computador e no celular

O setor não faz atestado, porque o campus não tem médico. Quando precisa, o aluno é encaminhado para a regional.

## Tecnologias

- Python
- Flask
- MySQL (pelo XAMPP)
- PyMySQL
- HTML, CSS e JavaScript