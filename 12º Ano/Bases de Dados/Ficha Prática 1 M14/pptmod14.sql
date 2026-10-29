
--
-- Criar Base de Dados: `pptmod14`
--
CREATE DATABASE pptmod14;
-- --------------------------------------------------------

--
-- Usar Base de Dados: `pptmod14`
--
use pptmod14;

-- --------------------------------------------------------

--
-- Criar tabela `codigopostal`
--

CREATE TABLE `codigopostal` (
  `Cod_Postal` int(11) NOT NULL,
  `localidade` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`Cod_Postal`)
);


--
-- Inserir registos na tabela `codigopostal`
--

INSERT INTO `codigopostal` (`Cod_Postal`, `localidade`) VALUES
(1000, 'LISBOA'),
(1100, 'LISBOA'),
(1200, 'LISBOA'),
(1500, 'LISBOA'),
(2000, 'SANTAREM'),
(2300, 'TOMAR'),
(3000, 'COIMBRA'),
(4000, 'PORTO'),
(9000, 'FUNCHAL');

-- --------------------------------------------------------

--
-- Criar tabela `pessoa`
--

CREATE TABLE `pessoa` (
  `id_pessoa` int(11) NOT NULL,
  `nome` varchar(50) DEFAULT NULL,
  `idade` int(11) DEFAULT NULL,
  `salario` decimal(10,0) DEFAULT NULL,
  `telefone` varchar(12) DEFAULT NULL,
  `Cod_Postal` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_pessoa`),
  FOREIGN KEY (`Cod_Postal`) REFERENCES `codigopostal` (`Cod_Postal`)
);

--
-- Inserir registos na tabela `pessoa`
--

INSERT INTO `pessoa` (`id_pessoa`, `nome`, `idade`, `salario`, `telefone`, `Cod_Postal`) VALUES
(5, 'Célia Morais', 25, '170000', '123456', 1000),
(14, 'Nascimento Augusto', 35, '220000', '456123', 1000),
(25, 'Paulo Vegas', 32, '95000', Null, 2000),
(32, 'Florinda Simões', 35, '147000', Null, 3000),
(37, 'Isabel Espada', 29, '86000', Null, 4000),
(42, 'António Deus', 43, '74000', '789654', 2000),
(49, 'José António', 17, '210000', Null, 3000);

-- --------------------------------------------------------

--
-- Criar tabela `mensagem`
--

CREATE TABLE `mensagem` (
  `id_Msg` int(11) NOT NULL,
  `mensagem` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id_Msg`)
);

--
-- Inserir registos na tabela `mensagem`
--

INSERT INTO `mensagem` (`id_Msg`, `mensagem`) VALUES
(10, 'Comissão Vendas'),
(20, 'Fretes Individuais'),
(30, 'Fretes Empresas'),
(40, 'Vendas Extra'),
(50, 'Deslocações'),
(60, 'Refeições'),
(70, 'Combustíveis'),
(100, 'Ofertas');

-- --------------------------------------------------------
--
-- Criar tabela `comissao`
--

CREATE TABLE `comissao` (
  `id_pessoa` int(11) NOT NULL,
  `id_Msg` int(11) NOT NULL,
  `valor` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_pessoa`,`id_Msg`),
  FOREIGN KEY (`id_pessoa`) REFERENCES `pessoa` (`id_pessoa`),
  FOREIGN KEY (`id_Msg`) REFERENCES `mensagem` (`id_Msg`)
);

--
-- Inserir registos na tabela `comissao`
--

INSERT INTO `comissao` (`id_pessoa`, `id_Msg`, `valor`) VALUES
(14, 10, 10500),
(14, 60, 2600),
(14, 70, 400),
(14, 100, 3750),
(25, 10, 2500),
(25, 30, 370),
(37, 10, 5500),
(37, 30, 14230),
(37, 40, 20),
(37, 50, 120),
(42, 20, 20),
(42, 30, 170),
(49, 20, 2300);

-- --------------------------------------------------------

