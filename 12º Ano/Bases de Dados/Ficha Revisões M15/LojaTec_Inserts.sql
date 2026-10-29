USE LojaTec;

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