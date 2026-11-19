SELECT codigop, designacaop, area, numero
FROM produto; -- A

SELECT produto.codigoP, codigoc, quantidadev, valorv
FROM produto, venda
WHERE produto.codigoP = venda.codigoP AND ((quantidadev > 50 AND quantidadev < 200) OR valorv > 60000); -- B

SELECT produto.codigoP, codigoc, quantidadev, valorv
FROM produto, venda
WHERE produto.codigoP = venda.codigoP AND ((quantidadev < 50 AND quantidadev > 200) OR valorv < 60000); -- C

SELECT nome, especialidade, dataNasc
FROM trabalhador
WHERE especialidade IN ("hortelão", "jardineiro"); -- D

SELECT nome, especialidade, dataNasc
FROM trabalhador
WHERE especialidade IN ("hortelão", "jardineiro") OR dataNasc BETWEEN "1955-01-01" AND "1965-12-31"; -- E

SELECT nome, especialidade, dataNasc
FROM trabalhador
WHERE nome LIKE "J%"; -- F

SELECT nome, especialidade, dataNasc
FROM trabalhador
WHERE nome NOT LIKE "J%"; -- G

SELECT designacaoP, area, produto.numero, nome, especialidade
FROM produto, trabalhador
WHERE produto.numero = trabalhador.numero; -- H

SELECT DISTINCT trabalhador.numero, nome, especialidade
FROM trabalhador, produto
WHERE produto.numero = trabalhador.numero; -- I

SELECT DISTINCT nome, especialidade, designacaoP
FROM trabalhador, produto, venda
WHERE venda.codigoP = produto.codigoP AND trabalhador.numero = produto.numero; -- J

SELECT designacaoP, area, produto.numero, nome, especialidade
FROM produto, trabalhador
WHERE produto.numero = trabalhador.numero
ORDER BY numero DESC, area ASC; -- K

SELECT designacaoP, area, produto.numero, nome, especialidade
FROM produto, trabalhador
WHERE produto.numero = trabalhador.numero AND especialidade = "eng_agronómo"
ORDER BY area DESC; -- L

SELECT designacaoP, area, nome, especialidade
FROM produto, trabalhador
WHERE produto.numero = trabalhador.numero; -- M

SELECT SUM(area) AS Área_total, AVG(area) AS Área_média, COUNT(*) AS Nº_de_produtos
FROM produto; -- N

SELECT produto.codigop, COUNT(*) AS Nº_de_vendas, SUM(quantidadeV) AS Quantidade
FROM produto, venda
WHERE produto.codigop = venda.codigop
GROUP BY codigop; -- O

SELECT produto.codigop, COUNT(*) AS Nº_de_vendas, SUM(quantidadeV) AS Quantidade
FROM produto, venda
WHERE produto.codigop = venda.codigop AND dataRecebim > dataV
GROUP BY codigop; -- P

SELECT produto.codigop, COUNT(*) AS Nº_de_vendas, SUM(quantidadeV) AS Quantidade
FROM produto, venda
WHERE produto.codigop = venda.codigop AND dataRecebim > dataV
GROUP BY codigop
HAVING SUM(quantidadeV) >= 250; -- Q

SELECT designacaoP, area
FROM produto
WHERE area = (SELECT MAX(area) FROM produto); -- S