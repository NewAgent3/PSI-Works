CREATE DATABASE LojaTec;
USE LojaTec;

# PARTE A

CREATE TABLE Fornecedor (
    Cod_Fornecedor INT PRIMARY KEY AUTO_INCREMENT,
    Nome VARCHAR(60) NOT NULL,
    Morada VARCHAR(100) NULL
);

CREATE TABLE Produto (
    Cod_Produto INT PRIMARY KEY AUTO_INCREMENT,
    Designacao VARCHAR(70) NOT NULL,
    Preco DECIMAL(8,2) NOT NULL,
    Stock INT NOT NULL,
    Cod_Fornecedor INT NOT NULL,
    CONSTRAINT fk_CodForn_Produto
    FOREIGN KEY (Cod_Fornecedor)
    REFERENCES Fornecedor(Cod_Fornecedor),
    CONSTRAINT chk_preco CHECK (Preco >= 0)
);

CREATE TABLE Cliente (
    Cod_Cliente INT PRIMARY KEY AUTO_INCREMENT,
    Nome VARCHAR(70) NOT NULL,
    Morada VARCHAR(100) NULL,
    Telefone VARCHAR(15) NULL
);

CREATE TABLE Encomenda (
    Cod_Encomenda INT PRIMARY KEY AUTO_INCREMENT,
    Data_Encomenda DATE NOT NULL,
    Cod_Cliente INT NOT NULL,
    CONSTRAINT fk_CodCli_Encomenda
    FOREIGN KEY (Cod_Cliente)
    REFERENCES Cliente(Cod_Cliente)
);

CREATE TABLE Item_Encomenda (
    Cod_Encomenda INT NOT NULL,
    Cod_Produto INT NOT NULL,
    Quantidade INT NOT NULL,
    Preco_Unitario DECIMAL(8,2) NOT NULL,
    CONSTRAINT fk_CodEnc_ItemEncomenda
    FOREIGN KEY (Cod_Encomenda)
    REFERENCES Encomenda(Cod_Encomenda),
    CONSTRAINT fk_CodProd_ItemEncomenda
    FOREIGN KEY (Cod_Produto)
    REFERENCES Produto(Cod_Produto),
    PRIMARY KEY (Cod_Encomenda, Cod_Produto),
    CONSTRAINT chk_precoUni CHECK (Preco_Unitario >= 0),
    CONSTRAINT chk_quantidade CHECK (Quantidade > 0)
);

# PARTE B

INSERT INTO Fornecedor
VALUES
(NULL, "TecnoDistribuição", "Almada"),
(NULL, "InfoPeças", "Seixal");

INSERT INTO Cliente
VALUES
(NULL, "Ana Costa", "Almada", "912345678"),
(NULL, "Bruno Silva", "Cacilhas", "913456789");

INSERT INTO Produto
VALUES
(NULL, "Rato USB", 12.50, 25, 1),
(NULL, "Teclado", 24.90, 12, 1),
(NULL, "Disco SSD", 59.90, 8, 2);

INSERT INTO Encomenda
VALUES
(NULL, "2026-10-15", 1),
(NULL, "2026-10-16", 2);

INSERT INTO Item_Encomenda
VALUES
(1, 1, 2, 12.50),
(1, 3, 1, 59.90),
(2, 2, 1, 24.90);

# PARTE C

ALTER TABLE Produto
ADD Categoria VARCHAR(30) NULL;

ALTER TABLE Produto
MODIFY Categoria VARCHAR(50) NULL;

ALTER TABLE Produto
CHANGE Categoria Tipo_Produto VARCHAR(50);

ALTER TABLE Produto
DROP COLUMN Tipo_Produto;

CREATE INDEX idx_produto_designacao
ON Produto(Designacao);

CREATE INDEX idx_cliente_nome_morada
ON Cliente(Nome, Morada);

ALTER TABLE Cliente
DROP INDEX idx_cliente_nome_morada;

ALTER TABLE Encomenda
ADD Estado VARCHAR(20) DEFAULT "Pendente";

ALTER TABLE Encomenda
MODIFY Estado VARCHAR(20) DEFAULT "Em processamento";

ALTER TABLE Encomenda
ALTER Estado DROP DEFAULT;

# PARTE D

CREATE TABLE Transportadora (
    Cod_Transportadora INT PRIMARY KEY AUTO_INCREMENT,
    Nome VARCHAR(60) NOT NULL,
    Telefone VARCHAR(15) NULL
);

ALTER TABLE Encomenda
ADD Cod_Transportadora INT NULL,
ADD CONSTRAINT fk_CodTrans_Encomenda
FOREIGN KEY (Cod_Transportadora)
REFERENCES Transportadora(Cod_Transportadora);

INSERT INTO Transportadora
VALUES
(NULL, "Lumière Expeditions", "921333000"),
(NULL, "Nova Arcadia's Exports", "934567123");