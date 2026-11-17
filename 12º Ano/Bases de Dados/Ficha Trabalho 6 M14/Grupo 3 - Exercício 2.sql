SELECT COUNT(*)
FROM escola; -- 2.1

SELECT distrito.cod_distrito, COUNT(*)
FROM escola, distrito
WHERE distrito.cod_distrito = escola.cod_distrito
GROUP BY distrito.cod_distrito
ORDER BY 2 ASC; -- 2.2

SELECT nome, localidade
FROM regiao, escola
WHERE regiao.cod_regiao = escola.cod_regiao AND regiao.nome_regiao = "CENTRO"
ORDER BY localidade, nome; -- 2.3