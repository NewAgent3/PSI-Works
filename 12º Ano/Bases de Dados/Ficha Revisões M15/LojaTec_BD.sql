CREATE DATABASE LojaTec;
USE LojaTec;

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