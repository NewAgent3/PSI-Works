USE Hospital;

INSERT INTO Paciente
VALUES
(NULL, "Joana Mendonça", "Rua da Alegria 15", "923864472"),
(NULL, "Sonia Cardoso Dias", "Rua de Pitágoras 3.14", "932835605"),
(NULL, "Diogo Malheiro", "Estrada do Miratejo 3", "935843752"),
(NULL, "Jamel Lopes", "Estreiro dos Obristas 5", "912638228"),
(NULL, "Joel Duque", "Rua da Ciência 8", "956324964"),
(NULL, "Alice Reis", "Rua do Alto Da Barca", "941732475");

INSERT INTO Medico
VALUES
(NULL, "João Silva", "Cardiologia", "Rua das Flores, Lisboa"),
(NULL, "Maria Santos", "Pediatria", "Avenida Central, Porto"),
(NULL, "Pedro Costa", "Dermatologia", "Rua do Sol, Coimbra"),
(NULL, "Ana Ferreira", "Neurologia", "Rua Nova, Braga"),
(NULL, "Benûr", "Cardiologia", "Bairro do Benûr, Laranjeiro"),
(NULL, "Carlos Oliveira", "Ortopedia", "Avenida da Liberdade, Lisboa");

INSERT INTO Seguro
VALUES
(NULL, "Fidelidade"),
(NULL, "Ageas Seguros"),
(NULL, "Tranquilidade"),
(NULL, "Allianz"),
(NULL, "AdvanceCare"),
(NULL, "Zurich");

INSERT INTO Consulta
VALUES
(NULL, "2026-12-3", "12:30:00", 2, 5),
(NULL, "2026-11-9", "09:00:00", 5, 1),
(NULL, "2027-01-15", "17:45:00", 4, 3),
(NULL, "2026-12-3", "16:15:00", 1, 5),
(NULL, "2027-03-15", "10:30:00", 6, 6),
(NULL, "2026-12-3", "12:30:00", 3, 4);

INSERT INTO Consulta_Seguro
VALUES
(1, 1, 10),
(4, 3, 5),
(2, 2, 25),
(5, 6, 99),
(3, 4, 15),
(6, 2, 20);

INSERT INTO Seguro_Médico
VALUES
(2, 3),
(5, 2),
(6, 1),
(3, 3),
(1, 5),
(4, 2);

INSERT INTO Paciente_Seguro
VALUES
(1, 3, "Seguro de Saúde"),
(3, 5, "Plano de Saúde"),
(2, 6, "Plano de Saúde"),
(5, 4, "Seguro de Saúde"),
(4, 2, "Plano de Saúde"),
(6, 1, "Seguro de Saúde");