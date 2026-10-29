-- CLINICA MEDICA | MySQL 8 / MariaDB (XAMPP)
-- Execute numa base de dados nova. Dados ficticios.
-- Chaves primarias simples em linha; compostas em restricao separada.

-- 0. Base de dados
CREATE DATABASE IF NOT EXISTS Clinica
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE Clinica;

-- 1. Paciente
CREATE TABLE Paciente (
    Cod_Paciente INT AUTO_INCREMENT PRIMARY KEY,
    Nome VARCHAR(100) NOT NULL,
    Endereco VARCHAR(150),
    Telefone VARCHAR(15)
);

-- 2. Medico
CREATE TABLE Medico (
    Cod_Med INT AUTO_INCREMENT PRIMARY KEY,
    Nome VARCHAR(100) NOT NULL,
    Especialidade VARCHAR(100),
    Endereco VARCHAR(150)
);

-- 3. Seguros
CREATE TABLE Seguros (
    Cod_Seg INT AUTO_INCREMENT PRIMARY KEY,
    Nome VARCHAR(100) NOT NULL
);

-- 4. Consulta
CREATE TABLE Consulta (
    Cod_Consulta INT AUTO_INCREMENT PRIMARY KEY,
    Data DATE NOT NULL,
    Horario TIME NOT NULL,
    Cod_Paciente INT NOT NULL,
    Cod_Med INT NOT NULL,
    FOREIGN KEY (Cod_Paciente) REFERENCES Paciente(Cod_Paciente),
    FOREIGN KEY (Cod_Med) REFERENCES Medico(Cod_Med)
);

-- 5. Consulta_Seguro (N:N)
CREATE TABLE Consulta_Seguro (
    Cod_Consulta INT NOT NULL,
    Cod_Seg INT NOT NULL,
    Percentagem DECIMAL(5,2),
    PRIMARY KEY (Cod_Consulta, Cod_Seg),
    FOREIGN KEY (Cod_Consulta) REFERENCES Consulta(Cod_Consulta),
    FOREIGN KEY (Cod_Seg) REFERENCES Seguros(Cod_Seg)
);

-- 6. Seguro_Medico (N:N)
CREATE TABLE Seguro_Medico (
    Cod_Med INT NOT NULL,
    Cod_Seg INT NOT NULL,
    PRIMARY KEY (Cod_Med, Cod_Seg),
    FOREIGN KEY (Cod_Med) REFERENCES Medico(Cod_Med),
    FOREIGN KEY (Cod_Seg) REFERENCES Seguros(Cod_Seg)
);

-- 7. Paciente_Seguros (N:N)
CREATE TABLE Paciente_Seguros (
    Cod_Seg INT NOT NULL,
    Cod_Paciente INT NOT NULL,
    Tipo VARCHAR(50),
    PRIMARY KEY (Cod_Seg, Cod_Paciente),
    FOREIGN KEY (Cod_Seg) REFERENCES Seguros(Cod_Seg),
    FOREIGN KEY (Cod_Paciente) REFERENCES Paciente(Cod_Paciente)
);

-- DADOS DE EXEMPLO

-- Paciente (5 registos)

INSERT INTO Paciente (Cod_Paciente, Nome, Endereco, Telefone) VALUES
    (1, 'Ana Martins', 'Rua das Flores, 12, Almada', '912345678'),
    (2, 'Bruno Silva', 'Av. da Liberdade, 30, Lisboa', '913456789'),
    (3, 'Carla Ferreira', 'Rua do Sol, 8, Seixal', '914567890'),
    (4, 'Diogo Costa', 'Rua da Escola, 21, Almada', '915678901'),
    (5, 'Eva Rodrigues', 'Praceta Central, 5, Barreiro', '916789012');

-- Medico (3 registos)

INSERT INTO Medico (Cod_Med, Nome, Especialidade, Endereco) VALUES
    (1, 'Sofia Almeida', 'Cardiologia', 'Av. Central, 10, Lisboa'),
    (2, 'Miguel Pereira', 'Dermatologia', 'Rua do Hospital, 4, Almada'),
    (3, 'Ines Carvalho', 'Clinica Geral', 'Rua da Saude, 7, Seixal');

-- Seguros (3 registos)

INSERT INTO Seguros (Cod_Seg, Nome) VALUES
    (1, 'Saude Mais'),
    (2, 'Protecao Total'),
    (3, 'Vida Segura');

-- Consulta (6 registos)

INSERT INTO Consulta (Cod_Consulta, Data, Horario, Cod_Paciente, Cod_Med) VALUES
    (1, '2026-11-03', '09:00:00', 1, 1),
    (2, '2026-11-03', '10:30:00', 2, 2),
    (3, '2026-11-04', '11:00:00', 3, 3),
    (4, '2026-11-05', '14:00:00', 4, 1),
    (5, '2026-11-06', '15:30:00', 5, 2),
    (6, '2026-11-09', '09:30:00', 1, 3);

-- Consulta_Seguro (7 registos)

INSERT INTO Consulta_Seguro (Cod_Consulta, Cod_Seg, Percentagem) VALUES
    (1, 1, 80.0),
    (2, 2, 70.0),
    (3, 3, 60.0),
    (4, 1, 80.0),
    (5, 2, 70.0),
    (6, 1, 50.0),
    (6, 3, 30.0);

-- Seguro_Medico (6 registos)

INSERT INTO Seguro_Medico (Cod_Med, Cod_Seg) VALUES
    (1, 1),
    (1, 2),
    (2, 2),
    (2, 3),
    (3, 1),
    (3, 3);

-- Paciente_Seguros (6 registos)

INSERT INTO Paciente_Seguros (Cod_Seg, Cod_Paciente, Tipo) VALUES
    (1, 1, 'Titular'),
    (3, 1, 'Complementar'),
    (2, 2, 'Titular'),
    (3, 3, 'Titular'),
    (1, 4, 'Titular'),
    (2, 5, 'Titular');
