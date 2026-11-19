SELECT numero, nome
FROM aluno
WHERE idade = 17 AND cod_turma = 5; -- 1

SELECT numero, nome, morada
FROM aluno
WHERE idade = 15 OR idade = 18; -- 2

SELECT numero, nome, morada
FROM aluno
WHERE idade IN (15, 16, 18); -- 3

SELECT nome, morada
FROM aluno
WHERE telefone IS NULL; -- 4

SELECT cod_professor, nome, idade
FROM professor
WHERE nome LIKE "a%a"; -- 5

SELECT cod_professor, nome, tmp_servico
FROM professor
ORDER BY idade DESC; -- 6

SELECT cod_professor, nome, tmp_servico
FROM professor
ORDER BY tmp_servico DESC, idade ASC; -- 7

SELECT professor.*, ensina.disciplina
FROM professor, ensina, turma
WHERE professor.cod_professor = ensina.cod_professor AND ensina.cod_turma = turma.cod_turma
ORDER BY disciplina, nome; -- 8

SELECT disciplina, nome, ano, designacao
FROM professor, ensina, turma
WHERE professor.cod_professor = ensina.cod_professor AND ensina.cod_turma = turma.cod_turma
ORDER BY disciplina ASC; -- 9

SELECT COUNT(*)
FROM professor
WHERE idade > 30; -- 10

SELECT COUNT(*)
FROM aluno
WHERE telefone IS NOT NULL; -- 11

SELECT idade
FROM aluno; -- 12