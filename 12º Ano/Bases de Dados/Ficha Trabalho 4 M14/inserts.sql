USE empresa2;

INSERT INTO clientes
VALUES
(NULL, "João", "Antunes", "656561678"),
(NULL, "Daniela", "Santos", NULL),
(NULL, "Carla", "Soares", "876123232"),
(NULL, "Pedro", "Peres", "156746532"),
(NULL, "Filipe", "Rocha", "265987436"),
(NULL, "Rui", "Lima", "236985124"),
(NULL, "Sandra", "Reis", NULL),
(NULL, "Filipe", "Almeida", "366597423");

INSERT INTO funcionarios
VALUES
(NULL, "Torres", "356797144"),
(NULL, "Neves", "487451321"),
(NULL, "Lopes", "484313238");

INSERT INTO servicos
VALUES
("Ic", "Instalação de canalização", 400),
("Ie", "Instalação de electricidade", 500),
("Ig", "Instalação de gás", 500),
("Ir", "Instalação de rede", 150),
("It", "Instalação de telefone", 100);

INSERT INTO administracao
VALUES
(1, "Ic", 2),
(1, "Ie", 2),
(2, "Ir", 1),
(2, "It", 1),
(3, "Ic", 2),
(3, "Ie", 2),
(3, "Ir", 1),
(4, "Ic", 2),
(4, "Ie", 2),
(4, "Ig", 3),
(5, "Ig", 3),
(5, "Ir", 1),
(5, "It", 1),
(6, "Ig", 3),
(6, "Ir", 1),
(7, "Ic", 2),
(7, "Ig", 3),
(7, "It", 1);