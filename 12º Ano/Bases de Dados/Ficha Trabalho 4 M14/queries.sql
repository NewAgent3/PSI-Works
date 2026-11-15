SELECT * FROM servicos; -- A

SELECT DISTINCT funcionarios.*
FROM funcionarios, administracao
WHERE (funcionarios.fid = administracao.fid); -- B

SELECT *
FROM servicos
WHERE custo < 200; -- C

SELECT servicos.descricao
FROM administracao, servicos
WHERE (administracao.sid = servicos.sid) AND administracao.cid = 7 AND administracao.fid = 1; -- D

SELECT DISTINCT clientes.nome, clientes.telefone
FROM clientes, administracao
WHERE clientes.cid = administracao.cid AND (administracao.fid = 1 OR administracao.fid = 3); -- E

SELECT administracao.sid, administracao.cid, clientes.nome, clientes.apelido, administracao.fid
FROM administracao, clientes
WHERE administracao.cid = clientes.cid; -- F

SELECT servicos.descricao, administracao.cid, clientes.nome, clientes.apelido, funcionarios.apelido
FROM administracao, clientes, servicos, funcionarios
WHERE administracao.cid = clientes.cid AND administracao.sid = servicos.sid AND administracao.fid = funcionarios.fid; -- G

SELECT clientes.*
FROM administracao, clientes
WHERE administracao.cid = clientes.cid AND administracao.fid = 3; -- H

SELECT clientes.nome, clientes.apelido
FROM administracao, clientes
WHERE administracao.cid = clientes.cid AND administracao.sid = "It"; -- I

SELECT DISTINCT clientes.nome, clientes.apelido
FROM administracao, clientes
WHERE administracao.cid = clientes.cid
ORDER BY clientes.apelido; -- J

SELECT DISTINCT clientes.nome, clientes.telefone
FROM administracao, clientes
WHERE administracao.cid = clientes.cid
ORDER BY clientes.telefone DESC; -- K