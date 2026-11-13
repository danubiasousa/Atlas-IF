# ATLAS IF

**Acompanhamento Tecnológico de Logística e Atendimentos à Saúde do Instituto Federal do Piauí**
Sistema do Setor de Saúde do IFPI – Campus Paulistana.

Projeto Integrador – Engenharia de Software + Programação Avançada para Web
Curso Técnico em Informática para Internet – 2º ano – Prof. Sebastião Sales Rodrigues Macedo

## Equipe e partes do sistema

| Integrante | Parte | Arquivos principais |
|---|---|---|
| Danúbia Coelho de Sousa | Login, senhas, cadastro de alunos e profissionais, núcleo e banco | `app.py`, `nucleo.py`, `rotas_acesso.py`, `seguranca.py`, `schema.sql` |
| Geovane Moura Gomes | Agendamentos, horários, calendário acadêmico, painel | `rotas_agendamento.py`, `calendario.py` |
| Maria Aparecida Coelho de Sousa | Atendimentos, anamnese, sinais vitais, histórico, declaração | `rotas_atendimento.py`, `static/js/atendimento.js` |
| Sthefany Kailane Lima de Sousa | Odontograma, materiais e medicamentos, visual das telas | `rotas_odonto_materiais.py`, `static/js/odontograma.js`, `static/css/app.css` |

## Tecnologias
Python 3 · Flask · MySQL (XAMPP) · PyMySQL · HTML · CSS · JavaScript

## Como instalar e rodar
1. Instale o [XAMPP](https://www.apachefriends.org/) e inicie o **MySQL** no painel do XAMPP.
2. Na pasta do projeto, instale as bibliotecas:
   ```
   pip install -r requirements.txt
   ```
3. Rode o sistema:
   ```
   python app.py
   ```
4. Abra `http://127.0.0.1:5000` no navegador.
   O banco `atlas_if` e as tabelas são criados automaticamente (ou importe o `schema.sql` no phpMyAdmin).

Se o MySQL tiver senha ou outra porta (PowerShell):
```
$env:DB_PASSWORD="sua_senha"
$env:DB_PORT=3307
python app.py
```

### Acessar pelo celular
Com o celular no mesmo Wi-Fi, use o endereço "No celular" que aparece no terminal (ex.: `http://192.168.0.15:5000`).

## Primeiro acesso
| Perfil | Usuário | Senha inicial |
|---|---|---|
| Servidores | `nome.sobrenome` (o @ifpi.edu.br é completado) | `setorsaude2026` |
| Alunos | matrícula (ou o e-mail cadastrado) | data de nascimento, ex.: `19042009` |

No primeiro login o sistema pede uma nova senha (mínimo 6 caracteres, com maiúscula, minúscula, número e caractere especial) e o e-mail e telefone de recuperação.

## Funcionalidades
- Login com recuperação de senha por código (e-mail ou SMS), válido por 1 minuto
- Cadastro de alunos e profissionais
- Agendamento pelo aluno seguindo o calendário acadêmico (sem sábados, domingos e feriados)
- Registro de atendimento: anamnese, sinais vitais com alertas por cor, IMC por idade (OMS)
- Odontograma interativo, inclusive procedimentos em todos os dentes
- Histórico de atendimentos e declaração de comparecimento
- Controle de materiais e medicamentos
- Layout para computador e celular

## Estrutura
```
app.py                      arquivo principal (python app.py)
nucleo.py                   configuração, banco, controle de acesso
rotas_acesso.py             login, senhas, alunos, usuários
rotas_agendamento.py        agendamentos e painel
rotas_atendimento.py        atendimentos, histórico, declaração
rotas_odonto_materiais.py   odontograma e materiais
seguranca.py                regras de senha e envio de códigos
calendario.py               feriados e dias sem atendimento
schema.sql                  estrutura do banco
templates/                  telas (HTML)
static/                     CSS, JavaScript e imagens
```