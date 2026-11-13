CREATE DATABASE IF NOT EXISTS atlas_if
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE atlas_if;


CREATE TABLE IF NOT EXISTS usuarios (
    id                   INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario              VARCHAR(120) NOT NULL UNIQUE,
    nome                 VARCHAR(120) NOT NULL,
    senha_hash           VARCHAR(255) NOT NULL,
    perfil               ENUM('profissional','aluno','admin') NOT NULL DEFAULT 'profissional',
    cargo                VARCHAR(80)  NULL,
    nivel                VARCHAR(20)  NOT NULL DEFAULT 'Operador',
    ativo                TINYINT(1)   NOT NULL DEFAULT 1,
    criado_em            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    campus               VARCHAR(60)  NULL,
    siape                VARCHAR(20)  NULL,
    trocar_senha         TINYINT(1)   NOT NULL DEFAULT 1,  
    email_recuperacao    VARCHAR(120) NULL,
    telefone_recuperacao VARCHAR(20)  NULL,
    senha_alterada_em    DATETIME     NULL,
    senha_temporaria     TINYINT(1)   NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS codigos_recuperacao (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT UNSIGNED NOT NULL,
    canal       ENUM('email','sms') NOT NULL,
    codigo_hash VARCHAR(255) NOT NULL,
    expira_em   DATETIME     NOT NULL,
    tentativas  TINYINT UNSIGNED NOT NULL DEFAULT 0,
    usado       TINYINT(1)   NOT NULL DEFAULT 0,
    criado_em   DATETIME     NOT NULL,
    INDEX idx_usuario (usuario_id, usado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS log_acessos (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    usuario    VARCHAR(120) NOT NULL,
    sucesso    TINYINT(1)   NOT NULL,
    ip         VARCHAR(45)  NULL,
    data_hora  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS alunos (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(120) NOT NULL,
    matricula       VARCHAR(30)  NOT NULL UNIQUE,
    turma           VARCHAR(40)  NULL,
    ativo           TINYINT(1)   NOT NULL DEFAULT 1,
    data_nascimento DATE         NULL,
    curso           VARCHAR(120) NULL,
    campus          VARCHAR(60)  NULL,
    usuario_id      INT UNSIGNED NULL,
    sexo            CHAR(1)      NULL,
    INDEX idx_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS atendimentos (
    id               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    aluno_nome       VARCHAR(120) NOT NULL,
    queixa           VARCHAR(160) NOT NULL,
    turma            VARCHAR(40)  NULL,
    status           ENUM('Concluído','Retorno','Encaminhado') NOT NULL,
    data_hora        DATETIME     NOT NULL,
    codigo           VARCHAR(20)  NULL,
    aluno_id         INT UNSIGNED NULL,
    profissional_id  INT UNSIGNED NULL,
    matricula        VARCHAR(30)  NULL,
    tipo             VARCHAR(20)  NOT NULL DEFAULT 'Atendimento',
    em_aula          TINYINT(1)   NOT NULL DEFAULT 0,
    historico        TEXT         NULL,
    alergias         VARCHAR(255) NULL,
    medicamentos_uso VARCHAR(255) NULL,
    doencas          VARCHAR(255) NULL,
    encaminhado_por  VARCHAR(120) NULL,
    pressao          VARCHAR(20)  NULL,
    fc               VARCHAR(20)  NULL,
    fr               VARCHAR(20)  NULL,
    temperatura      VARCHAR(20)  NULL,
    saturacao        VARCHAR(20)  NULL,
    peso             VARCHAR(20)  NULL,
    glicemia         VARCHAR(20)  NULL,
    procedimentos    VARCHAR(600) NULL,
    medicamentos_adm TEXT         NULL,
    enc_externo      TINYINT(1)   NOT NULL DEFAULT 0,
    agendar_retorno  TINYINT(1)   NOT NULL DEFAULT 0,
    orientacoes      TEXT         NULL,
    observacoes      TEXT         NULL,
    finalizado_em    DATETIME     NULL,
    altura           VARCHAR(20)  NULL,
    imc              VARCHAR(60)  NULL,
    INDEX idx_data (data_hora)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS retornos (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    aluno_nome  VARCHAR(120) NOT NULL,
    motivo      VARCHAR(160) NOT NULL,
    data_hora   DATETIME     NOT NULL,
    urgente     TINYINT(1)   NOT NULL DEFAULT 0,
    status      ENUM('pendente','concluido') NOT NULL DEFAULT 'pendente'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS estoque (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    item        VARCHAR(80)  NOT NULL,
    quantidade  INT UNSIGNED NOT NULL,
    ideal       INT UNSIGNED NOT NULL,
    unidade     VARCHAR(20)  NOT NULL,
    categoria   VARCHAR(40)  NULL,
    fornecedor  VARCHAR(80)  NULL,
    validade    DATE         NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS solicitacoes (
    id                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    aluno_nome        VARCHAR(120) NOT NULL,
    motivo            VARCHAR(300) NOT NULL,
    profissional_id   INT UNSIGNED NOT NULL,
    status            ENUM('pendente','aceita','recusada') NOT NULL DEFAULT 'pendente',
    criado_em         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    aluno_id          INT UNSIGNED NULL,
    tipo              VARCHAR(20)  NULL,
    data_preferencial DATE         NULL,
    horario           VARCHAR(5)   NULL,
    em_aula           TINYINT(1)   NOT NULL DEFAULT 0,
    justificativa     VARCHAR(300) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS procedimentos_odonto (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    aluno_id        INT UNSIGNED NULL,
    aluno_nome      VARCHAR(120) NOT NULL,
    atendimento_id  INT UNSIGNED NULL,
    dente           TINYINT UNSIGNED NOT NULL,
    procedimento    VARCHAR(80)  NOT NULL,
    faces           VARCHAR(120) NULL,
    situacao        ENUM('Planejado','Em andamento','Concluído') NOT NULL DEFAULT 'Planejado',
    data            DATE         NOT NULL,
    observacoes     TEXT         NULL,
    profissional_id INT UNSIGNED NULL,
    criado_em       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_aluno (aluno_id, dente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS migracoes (
    nome      VARCHAR(60) NOT NULL PRIMARY KEY,
    feita_em  DATETIME    NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;