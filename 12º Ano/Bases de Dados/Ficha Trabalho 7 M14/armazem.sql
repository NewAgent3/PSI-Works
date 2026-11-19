CREATE DATABASE Armazem;
USE Armazem;

CREATE TABLE Trabalhador (
numero int AUTO_INCREMENT, 
nome varchar(255), 
dataNasc date, 
especialidade varchar(255),
PRIMARY KEY(numero)
);

CREATE TABLE Produto (
codigoP int, 
designacaoP varchar(255),
area float,
numero int,
PRIMARY KEY(codigoP),
FOREIGN KEY(numero) REFERENCES Trabalhador(numero)
);

CREATE TABLE Comprador (
codigoC int AUTO_INCREMENT, 
identificacaoC varchar(255), 
moradaC varchar(255),
telefoneC int(9),
PRIMARY KEY(codigoC)
);

CREATE TABLE Venda (
codigoP int, 
codigoC int, 
dataV date, 
quantidadeV float, 
valorV int, 
dataRecebim date,
PRIMARY KEY(codigoP, codigoC),
FOREIGN KEY(codigoP) REFERENCES Produto(codigoP),
FOREIGN KEY(codigoC) REFERENCES Comprador(codigoC)
);

CREATE TABLE MateriaPrima (
codigoMp int AUTO_INCREMENT, 
designacaoMp varchar(255), 
quantArmaz int,
PRIMARY KEY(codigoMp)
);

CREATE TABLE Utiliza (
codigoP int, 
codigoMp int, 
dataU date, 
quantidadeU int,
PRIMARY KEY(codigoP, codigoMp),
FOREIGN KEY(codigoP) REFERENCES Produto(codigoP),
FOREIGN KEY(codigoMp) REFERENCES MateriaPrima(codigoMp)
);

CREATE TABLE Fornecedor (
codigoF int AUTO_INCREMENT, 
identificacaoF varchar(255), 
moradaF varchar(255), 
TelefoneF int(9),
PRIMARY KEY(codigoF)
);

CREATE TABLE Compra (
codigoMp int, 
codigoF int, 
dataC date, 
quantidadeC int, 
valorC int, 
dataPagam date,
PRIMARY KEY(codigoMp, codigoF),
FOREIGN KEY(codigoMp) REFERENCES MateriaPrima(codigoMp),
FOREIGN KEY(codigoF) REFERENCES Fornecedor(codigoF)
);


INSERT INTO Trabalhador (nome, dataNasc, especialidade)
VALUES ('Joao Dias', '1955-05-05', 'hortelao'),
('Luisa Ferreira', '1945-11-25', 'jardineiro'),
('Mario Horta', '1960-05-12', 'motorista'),
('Joana Garcia', '', 'eng_agronómo');

INSERT INTO Produto (codigoP, designacaoP, area, numero)
VALUES (5, 'cenoura', '4,5', 4),
(6, 'feijao verde', '6,5', 1),
(7, 'batata', '2,6', 4),
(8, 'rosa', '1,0', 2);

INSERT INTO Comprador (identificacaoC, moradaC, telefoneC)
VALUES ('Manel Maria', 'Almada', 987654323),
('Luisa Fraga', 'Cacilhas', 964562120),
('Duarte Silva', 'Cova da Piedade', 939745470);

INSERT INTO Venda (codigoP, codigoC, dataV, quantidadeV, valorV, dataRecebim)
VALUES (5, 1, '1999-04-07', '50,00', 45000, ''),
(5, 2, '1999-03-29', '5,90', 1000, '1999-03-30'),
(6, 1, '1999-03-29', '450,00', 90000, '1999-03-30'),
(6, 2, '1999-04-05', '100,00', 60000, '1999-04-10');

INSERT INTO MateriaPrima (designacaoMp, quantArmaz)
VALUES ('Rede', 3),
('Caixa', 6),
('Embalagem', 4),
('Vaso', 4);

INSERT INTO Utiliza (codigoP, codigoMp, dataU, quantidadeU)
VALUES (7, 1, '1999-02-05', 3),
(5, 2, '1999-02-05', 4),
(6, 3, '1999-02-11', 3),
(8, 4, '1999-02-12', 2);

INSERT INTO Fornecedor (identificacaoF, moradaF, TelefoneF)
VALUES ('Ana Sousa', 'Cacilhas', 923537730);

INSERT INTO Compra (codigoMp, codigoF, dataC, quantidadeC, valorC, dataPagam)
VALUES (1, 1, '1999-03-02', 4, 30, '1999-03-03'),
(3, 1, '1999-03-04', 3, 40, '1999-03-05'),
(4, 1, '1999-03-05', 2, 60, '1999-03-06');