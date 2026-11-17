SELECT COUNT(*)
FROM turma
WHERE ano = 11; -- 2.1

SELECT AVG(idade)
FROM professor; -- 2.2

SELECT Ano, Turma
FROM professor/turma
GROUP BY num; -- 2.3