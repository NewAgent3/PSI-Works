/* Para contexto, a stora decidiu fazer tudo da pior maneira possivél, para ver se ninguém entendia,
e depois fica fudida de não terem feito pela maneira complicada */

SELECT * FROM servicos; -- A

SELECT DISTINCT funcionarios.*
FROM funcionarios, administracao
WHERE (funcionarios.fid = administracao.fid); -- B
-- Versão "correta" da B. NUNCA PEDIRAM ESTES CAMPOS BTW!
SELECT DISTINCT funcionarios.apelido, servicos.descricao
FROM funcionarios, administracao, servicos
WHERE funcionarios.fid = administracao.fid AND servicos.sid = administracao.sid;

SELECT *
FROM servicos
WHERE custo < 200; -- C

SELECT servicos.descricao
FROM administracao, servicos
WHERE (administracao.sid = servicos.sid) AND administracao.cid = 7 AND administracao.fid = 1; -- D
-- A "stora" queria pelos nomes, ou seja, pedi-se no exercício, não especificou, não faço assim

SELECT DISTINCT clientes.nome, clientes.telefone
FROM clientes, administracao
WHERE clientes.cid = administracao.cid AND (administracao.fid = 1 OR administracao.fid = 3); -- E
-- A "stora" queria pelos nomes, ou seja, pedi-se no exercício, não especificou, não faço assim

SELECT administracao.sid, administracao.cid, clientes.nome, clientes.apelido, administracao.fid
FROM administracao, clientes
WHERE administracao.cid = clientes.cid; -- F
-- Correção que deu igual
SELECT DISTINCT servicos.sid, clientes.cid, clientes.nome, administracao.fid
FROM administracao, clientes, servicos
WHERE clientes.cid = administracao.cid AND servicos.sid = administracao.sid

SELECT servicos.descricao, administracao.cid, clientes.nome, clientes.apelido, funcionarios.apelido
FROM administracao, clientes, servicos, funcionarios
WHERE administracao.cid = clientes.cid AND administracao.sid = servicos.sid AND administracao.fid = funcionarios.fid; -- G

SELECT clientes.*
FROM administracao, clientes
WHERE administracao.cid = clientes.cid AND administracao.fid = 3; -- H
-- A "stora" queria pelos nomes, ou seja, pedi-se no exercício, não especificou, não faço assim

SELECT clientes.nome, clientes.apelido
FROM administracao, clientes
WHERE administracao.cid = clientes.cid AND clientes.nome LIKE "%a%" AND administracao.sid = "It"; -- I

SELECT DISTINCT clientes.nome, clientes.apelido
FROM administracao, clientes
WHERE administracao.cid = clientes.cid
ORDER BY clientes.apelido; -- J

SELECT DISTINCT clientes.nome, clientes.telefone
FROM administracao, clientes
WHERE administracao.cid = clientes.cid
ORDER BY clientes.telefone DESC; -- K