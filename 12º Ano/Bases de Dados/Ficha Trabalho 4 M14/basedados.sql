CREATE DATABASE empresa2;
USE empresa2;

CREATE TABLE clientes (
    cid INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    apelido VARCHAR(100),
    telefone VARCHAR(12) NULL
)

CREATE TABLE funcionarios (
    fid INT AUTO_INCREMENT PRIMARY KEY,
    apelido VARCHAR(100),
    telefone VARCHAR(12) NULL
)

CREATE TABLE servicos (
    sid VARCHAR(10) PRIMARY KEY,
    descricao VARCHAR(255),
    custo INT
)

CREATE TABLE administracao (
    cid INT,
    sid VARCHAR(10),
    fid INT,
    CONSTRAINT fk_cid_administracao
    FOREIGN KEY (cid)
    REFERENCES clientes(cid),
    CONSTRAINT fk_sid_administracao
    FOREIGN KEY (sid)
    REFERENCES servicos(sid),
    CONSTRAINT fk_fid_administracao
    FOREIGN KEY (fid)
    REFERENCES funcionarios(fid),
    PRIMARY KEY (cid, sid, fid)
)