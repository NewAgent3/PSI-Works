USE LojaTec;

CREATE TABLE Transportadora (
    Cod_Transportadora INT PRIMARY KEY AUTO_INCREMENT,
    Nome VARCHAR(60) NOT NULL,
    Telefone VARCHAR(15) NULL
);

ALTER TABLE Encomenda
ADD Cod_Transportadora INT NULL,
CONSTRAINT fk_CodTrans_Encomenda
FOREIGN KEY (Cod_Transportadora)
REFERENCES Transportadora(Cod_Transportadora);

INSERT INTO Transportadora
VALUES
(NULL, "Lumière Expeditions", "921333000"),
(NULL, "Nova Arcadia's Exports", "934567123");