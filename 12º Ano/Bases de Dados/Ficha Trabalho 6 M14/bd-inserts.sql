CREATE TABLE Distrito (
    Cod_Distrito INT AUTO_INCREMENT PRIMARY KEY,
    Desc_Distrito VARCHAR(100)
);

CREATE TABLE Concelho (
    Cod_Concelho INT AUTO_INCREMENT PRIMARY KEY,
    Desc_Concelho VARCHAR(100),
    Cod_Distrito INT,
    N_Habitantes INT,
    Area INT,
    CONSTRAINT fk_coddistrito_concelho
    FOREIGN KEY (Cod_Distrito)
    REFERENCES Distrito(Cod_Distrito)
);

CREATE TABLE Freguesia (
    Cod_Freguesia INT AUTO_INCREMENT PRIMARY KEY,
    Desc_Freguesia VARCHAR(100),
    Cod_Concelho INT,
    CONSTRAINT fk_codconcelho_freguesia
    FOREIGN KEY (Cod_Concelho)
    REFERENCES Concelho(Cod_Concelho)
)

INSERT INTO distrito
VALUES
(NULL, "Aveiro"),
(NULL, "Beja"),
(NULL, "Braga");

INSERT INTO concelho
VALUES
(NULL, "Agueda", 1, 2200, 120),
(NULL, "Albergaria a Velha", 1, 1000, 20),
(NULL, "Canas", 1, 1000, 5),
(NULL, "Aljustrel", 2, 1200, 19),
(NULL, "Alvito", 2, 2000, 12),
(NULL, "Amares", 3, 2200, 20),
(NULL, "Barcelos", 3, 3000, 20);

INSERT INTO freguesia
VALUES
(NULL, "Valongo", 1),
(NULL, "Moita", 2),
(NULL, "Messejana", 3),
(NULL, "Santa Cruz", 3),
(NULL, "Barrancos", 4);