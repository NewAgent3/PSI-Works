SELECT COUNT(*) AS total_clientes
FROM clientes; -- A

SELECT COUNT(*), COUNT(telefone)
FROM clientes; -- B

SELECT COUNT(*)
FROM clientes
WHERE telefone IS NULL; -- C

SELECT COUNT(*)
FROM servicos
WHERE custo < 200; -- D

SELECT COUNT(DISTINCT cid)
FROM administracao, funcionarios
WHERE administracao.fid = funcionarios.fid AND funcionarios.apelido = "Torres"; -- E

SELECT COUNT(*)
FROM administracao, funcionarios
WHERE administracao.fid = funcionarios.fid AND funcionarios.apelido = "Torres"; -- F

SELECT MIN(custo) AS mínimo, MAX(custo) AS máximo
FROM servicos; -- G

SELECT SUM(custo)
FROM administracao, clientes, servicos
WHERE administracao.cid = clientes.cid AND administracao.sid = servicos.sid AND clientes.nome = "Daniela" AND clientes.apelido = "Santos"; -- H

SELECT SUM(custo)
FROM administracao, clientes, servicos, funcionarios
WHERE administracao.cid = clientes.cid AND administracao.sid = servicos.sid AND administracao.fid = funcionarios.fid AND clientes.nome = "Daniela" AND clientes.apelido = "Santos" AND funcionarios.apelido = "Torres"; -- I

SELECT AVG(custo)
FROM servicos; -- J