# ATLAS IF

Sistema que fizemos para o Setor de Saúde do IFPI Campus Paulistana, no Projeto Integrador das disciplinas de Engenharia de Software e Programação Avançada para Web (2º ano do Técnico em Informática para Internet, Prof. Sebastião Sales Rodrigues Macedo).

O nome vem de Acompanhamento Tecnológico de Logística e Atendimentos à Saúde do Instituto Federal.

A ideia surgiu porque o setor anota quase tudo no papel: atendimentos, retornos, estoque de material. Com o sistema, a enfermagem e a odontologia registram os atendimentos e consultam o histórico de cada aluno, e o aluno consegue marcar horário pelo celular sem precisar ir até o setor.

## Equipe

| Integrante | Arquivos que ficaram com cada um |
|---|---|
| Danúbia Coelho de Sousa | style.css, materiais.html, minha_conta.html, painel.html, primeiro_acesso.html, recuperar.html, usuarios.html, app.py, calendario.py, nucleo.py, rotas_atendimento.py |
| Geovane Moura Gomes | README, _icons.html, _mensagens_publico.html, _regras_senha.html, _solicitacoes_lista.html, aluno_atendimentos.html, aluno_marcar.html, historico.html, login.html, rotas_odonto_materiais.py |
| Maria Aparecida Coelho de Sousa | app.css, aluno_painel.html, alunos.html, atendimento_novo.html, base_app.html, base_publico.html, declaracao.html, rotas_agendamento.py, rotas_acesso.py, schema.sql |
| Sthefany Kailane Lima de Sousa | imagens (logos, brasão e rodapé), atendimento.js, odontograma.js, senha.js, .gitignore, requirements.txt, resetar_senha.py, seguranca.py, usuarios_seed.py |

## O que o sistema faz

- Login para profissionais e alunos, com recuperação de senha por código enviado ao e-mail ou celular
- Cadastro de alunos e de profissionais do setor
- O aluno marca atendimento escolhendo enfermagem ou odontologia, o profissional e o horário. Sábados, domingos, feriados e pontos facultativos do calendário acadêmico ficam bloqueados
- Registro do atendimento em etapas: identificação, anamnese, sinais vitais, procedimentos e orientações
- Os sinais vitais ficam verdes, amarelos ou vermelhos conforme o valor, e o IMC é calculado sozinho pela tabela de idade
- Odontograma para registrar os procedimentos de cada dente, ou de todos os dentes no caso de limpeza e raspagem
- Histórico de atendimentos com busca por nome, tipo e data
- Declaração de comparecimento preenchida automaticamente, para o aluno que veio no horário de aula
- Controle de materiais e medicamentos, com aviso quando o estoque está baixo
- Funciona no computador e no celular

O setor não emite atestado, porque no campus não tem médico. Quando precisa, o aluno é encaminhado para a regional.

## Formulários

| Formulário | Campos principais |
|---|---|
| Login | usuário (nome.sobrenome, e-mail ou matrícula), senha |
| Cadastro de aluno | nome, matrícula, data de nascimento, turma, sexo, curso, campus |
| Atendimento: identificação | aluno, matrícula, turma, nascimento, sexo, data, hora, queixa principal |
| Atendimento: anamnese | histórico, alergias, medicamentos em uso, doenças preexistentes, encaminhado por |
| Atendimento: sinais vitais | pressão, frequência cardíaca e respiratória, temperatura, saturação, peso, altura, IMC, glicemia |
| Atendimento: procedimentos | procedimentos feitos, medicamentos administrados, encaminhamento, retorno |
| Atendimento: finalização | orientações, observações, declaração de comparecimento |
| Busca no histórico | nome, tipo, data |
| Busca de materiais | nome, categoria, status |
| Cadastro de material | nome, categoria, unidade, fornecedor, quantidade, estoque mínimo, validade |
| Novo usuário | nome, e-mail institucional, cargo, campus, perfil de acesso, SIAPE |

Os campos são conferidos na tela e também no servidor. Por exemplo: a pressão só aceita o formato 120/80, campos numéricos não aceitam letras e a anamnese não passa com campo vazio.

## Tecnologias

Python, Flask, MySQL (pelo XAMPP), PyMySQL, HTML, CSS e JavaScript.

## Como rodar

Precisa ter o Python 3 e o XAMPP instalados.

1. Abra o XAMPP e dê Start no MySQL.
2. Na pasta do projeto, instale as bibliotecas:
   ```
   python -m pip install -r requirements.txt
   ```
3. Rode:
   ```
   python app.py
   ```
4. Abra `http://127.0.0.1:5000` no navegador.

O banco `atlas_if` e as tabelas são criados quando o sistema inicia. Se preferir, dá para importar o `schema.sql` pelo phpMyAdmin.

Se o MySQL tiver senha, rode antes (no PowerShell):
```
$env:DB_PASSWORD="sua_senha"
```

Para abrir no celular, ele precisa estar no mesmo Wi-Fi do computador. O endereço aparece no terminal quando o sistema inicia, algo como `http://192.168.0.15:5000`.

## Primeiro acesso

| Quem | Usuário | Senha inicial |
|---|---|---|
| Servidores | nome.sobrenome (o @ifpi.edu.br completa sozinho) | setorsaude2026 |
| Alunos | matrícula | data de nascimento sem barras, ex.: 19042009 |

No primeiro login o sistema pede para criar uma senha nova (mínimo de 6 caracteres, com letra maiúscula, minúscula, número e caractere especial) e para cadastrar um e-mail e um telefone de recuperação.

Sem configurar um e-mail de envio, o código de recuperação de senha aparece no terminal. Isso serve para testar.

## Estrutura das pastas

```
app.py                      arquivo que roda o sistema
nucleo.py                   configuração, banco de dados e controle de acesso
rotas_acesso.py             login, senhas, alunos e usuários
rotas_agendamento.py        agendamento e painel do profissional
rotas_atendimento.py        atendimento, histórico e declaração
rotas_odonto_materiais.py   odontograma e materiais
seguranca.py                regras de senha e envio do código
calendario.py               feriados e dias sem atendimento
schema.sql                  tabelas do banco
templates/                  páginas HTML
static/                     CSS, JavaScript e imagens
```

## Situação atual

Formulários e banco de dados funcionando. Ainda falta fazer mais testes, ajustar o que aparecer e hospedar o sistema.
