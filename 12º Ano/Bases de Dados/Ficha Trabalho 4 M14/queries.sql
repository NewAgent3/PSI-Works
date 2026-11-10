SELECT * FROM servicos; -- A

SELECT DISTINCT funcionarios.*
FROM funcionarios, administracao
WHERE (funcionarios.fid = administracao.fid); -- B (NOT DONE YET)
