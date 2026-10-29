CREATE DATABASE Hospital;

USE Hospital;

CREATE TABLE Paciente (
    Cod_Paciente int AUTO_INCREMENT PRIMARY KEY,
    Nome VARCHAR(50),
    Endereco VARCHAR(100),
    Telefone VARCHAR(9)
);

CREATE TABLE Medico (
    Cod_Med int AUTO_INCREMENT PRIMARY KEY,
    Nome VARCHAR(50),
    Especialidade VARCHAR(50),
    Endereco VARCHAR(100)
);

CREATE TABLE Seguro (
    Cod_Seg int AUTO_INCREMENT PRIMARY KEY,
    Nome VARCHAR(50)
);

CREATE TABLE Consulta (
    Cod_Consulta int AUTO_INCREMENT PRIMARY KEY,
    Data_Consulta DATE,
    Horario TIME,
    Cod_Paciente int,
    Cod_Med int,
    FOREIGN KEY (Cod_Paciente)
    REFERENCES Paciente(Cod_Paciente),
    FOREIGN KEY (Cod_Med)
    REFERENCES Medico(Cod_Med)
);

CREATE TABLE Consulta_Seguro (
    Cod_Consulta int,
    Cod_Seg int,
    Percentagem int,
    FOREIGN KEY (Cod_Consulta)
    REFERENCES Consulta(Cod_Consulta),
    FOREIGN KEY (Cod_Seg)
    REFERENCES Seguro(Cod_Seg),
    PRIMARY KEY (Cod_Consulta, Cod_Seg)
);

CREATE TABLE Seguro_Médico (
    Cod_Med int,
    Cod_Seg int,
    FOREIGN KEY (Cod_Med)
    REFERENCES Medico(Cod_Med),
    FOREIGN KEY (Cod_Seg)
    REFERENCES Seguro(Cod_Seg),
    PRIMARY KEY (Cod_Med, Cod_Seg)
);

CREATE TABLE Paciente_Seguro (
    Cod_Seg int,
    Cod_Paciente int,
    Tipo VARCHAR(50),
    FOREIGN KEY (Cod_Seg)
    REFERENCES Seguro(Cod_Seg),
    FOREIGN KEY (Cod_Paciente)
    REFERENCES Paciente(Cod_Paciente),
    PRIMARY KEY (Cod_Seg, Cod_Paciente)
);