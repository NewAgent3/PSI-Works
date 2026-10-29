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
    Cod_Fornecedor INT
    CONSTRAINT fk_CodForn_Produto
    FOREIGN KEY (Cod_Fornecedor)
    REFERENCES Fornecedor(Cod_Fornecedor)
    CONSTRAINT chk_preco CHECK (Preco >= 0)
);