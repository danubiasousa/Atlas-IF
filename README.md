# ATLAS IF

Sistema do Setor de Saúde do IFPI Campus Paulistana.
Projeto Integrador · Engenharia de Software + Programação Avançada para Web.

**Equipe:** Danúbia Coelho de Sousa · Geovane Moura Gomes · Maria Aparecida Coelho de Sousa · Sthefany Kailane Lima de Sousa

## O que o sistema faz

- Login para profissionais e alunos, com recuperação de senha por código enviado ao e-mail ou celular
- Cadastro de alunos e de profissionais do setor, com **editar e excluir**
- Marcação de atendimento pelo aluno: ele escolhe enfermagem ou odontologia, o profissional e o horário. Sábados, domingos, feriados e pontos facultativos do calendário acadêmico ficam bloqueados
- Registro do atendimento em etapas: identificação, anamnese, sinais vitais, procedimentos e orientações. O atendimento pode ser **editado ou excluído** depois, pelo histórico
- Sinais vitais em verde, amarelo ou vermelho de acordo com o valor, e IMC calculado sozinho pela tabela de idade
- Odontograma para registrar o procedimento de cada dente, ou de todos os dentes no caso de limpeza e raspagem
- Histórico de atendimentos com busca por nome, tipo e data
- Declaração de comparecimento preenchida automaticamente, para o aluno que veio no horário de aula
- Controle de materiais e medicamentos (cadastrar, consultar, editar e excluir), com aviso quando o estoque está baixo
- Funciona no computador e no celular

O setor não faz atestado, porque o campus não tem médico. Quando precisa, o aluno é encaminhado para a regional.

## Tecnologias

- Python 3 e Flask
- MySQL (pelo XAMPP), acessado com PyMySQL
- SQLAlchemy (ORM) no controle de materiais
- HTML, CSS e JavaScript

## Como instalar e rodar

### Requisitos

- [Python 3.10 ou mais novo](https://www.python.org/downloads/) (na instalação, marque **Add Python to PATH**)
- [XAMPP](https://www.apachefriends.org/) (só o MySQL é usado)
- Git (ou baixe o projeto pelo botão verde **Code → Download ZIP**)

### Passo a passo

1. Baixe o projeto:
   ```
   git clone https://github.com/danubiasousa/Atlas-IF.git
   cd Atlas-IF
   ```
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
   Se o `pip` não for reconhecido, use `python -m pip install -r requirements.txt`.
3. Abra o **XAMPP** e clique em **Start** no **MySQL**.
4. Rode o sistema:
   ```
   python app.py
   ```
   Na primeira vez, o sistema cria sozinho o banco `atlas_if`, as 10 tabelas (arquivo `schema.sql`), os usuários do setor e alguns dados de exemplo. Não é preciso importar nada no phpMyAdmin.
5. Abra **http://127.0.0.1:5000** no navegador. Para parar, aperte **Ctrl + C** no terminal.

O XAMPP vem com usuário `root` e senha vazia, que é o padrão do sistema. Se o seu MySQL tiver senha, defina antes de rodar (Windows): `set DB_PASSWORD=sua_senha`.

### Usuários para teste

- Enfermeira (supervisora, vê tudo): `mariana.moura` · senha `setorsaude2026`
- Dentista (abre o odontograma): `debora.castro` · senha `setorsaude2026`
- Aluna: `2025120IIPI0009` · senha `19042009` (data de nascimento)

No primeiro login, o sistema pede para criar uma senha nova (mínimo 6 caracteres, com maiúscula, minúscula, número e caractere especial) e cadastrar um e-mail e um telefone de recuperação. O código de recuperação de senha aparece no **terminal** enquanto o envio por e-mail/SMS não estiver configurado (veja `LEIAME.txt`).

## Segurança

- **Código secreto nos formulários (CSRF):** todo formulário POST leva um código aleatório da sessão (`{{ csrf_input() }}`), e o servidor recusa o envio sem ele (`nucleo.py`).
- **Texto escapado:** as telas usam o Jinja, que escapa tudo o que o usuário digita. Um `<script>` digitado aparece como texto e não roda.
- **ORM e consultas parametrizadas:** o controle de materiais usa o ORM SQLAlchemy (`modelos.py`). As outras consultas usam parâmetros (`%s`), nunca juntam o texto digitado ao SQL. Os dois jeitos evitam SQL injection.
- **Conferência no servidor:** além das regras na tela (HTML e JavaScript), o Python confere de novo os dados antes de salvar (matrícula, data, sinais vitais, tamanho dos textos, quantidades).
- **Senhas em hash**, código de recuperação com validade de 1 minuto e limite de 5 tentativas, cookie da sessão protegido (`HttpOnly`, `SameSite`) e chave secreta aleatória guardada fora do GitHub (`.chave_secreta`).
- Só quem fez o atendimento, ou um supervisor, pode editar ou excluir o registro.

## Estrutura do projeto

```
app.py                     arquivo principal (rode este)
nucleo.py                  configuração, conexão com o banco, criação das tabelas e segurança
modelos.py                 ORM (SQLAlchemy) da tabela estoque
rotas_acesso.py            login, senhas, alunos e usuários
rotas_agendamento.py       agendamentos e painel
rotas_atendimento.py       atendimentos, histórico e declaração
rotas_odonto_materiais.py  odontograma e materiais
seguranca.py               regras de senha e envio de códigos
calendario.py              dias sem atendimento
schema.sql                 criação das tabelas
templates/  static/        telas, estilos, imagens e JavaScript
```