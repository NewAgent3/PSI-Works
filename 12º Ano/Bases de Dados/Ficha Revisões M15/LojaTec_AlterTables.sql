USE LojaTec;

ALTER TABLE Produto
ADD Categoria VARCHAR(30) NULL;

ALTER TABLE Produto
MODIFY Categoria VARCHAR(50) NULL;

ALTER TABLE Produto
RENAME COLUMN Categoria TO Tipo_Produto;

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