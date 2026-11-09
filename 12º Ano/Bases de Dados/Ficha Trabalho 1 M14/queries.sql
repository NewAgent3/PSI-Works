SELECT * FROM fornecedor; -- A

SELECT * FROM fornecedor WHERE categ <= 20; -- B

SELECT nc, nome, sede FROM fornecedor WHERE categ = 10; -- C

SELECT nomep FROM projeto WHERE cidade != "Lisboa"; -- D

SELECT nc, nr, quant FROM fcp WHERE serie = 1; -- E

SELECT nc, nr, quant FROM fcp WHERE serie BETWEEN 3 AND 6; -- F

SELECT nc, nr, quant FROM fcp WHERE serie NOT BETWEEN 3 AND 6; -- G

SELECT nomep, cidade FROM projeto WHERE nr BETWEEN 9204 AND 9303; -- H

SELECT * FROM componente WHERE design = "Biela" AND cor = "Verde"; -- I

SELECT * FROM componente WHERE cor = "Rosa"; -- J

SELECT nc FROM fcp WHERE (nr <= 9204 OR nr >= 9303) AND (serie BETWEEN 3 AND 5); -- K

SELECT * FROM componente WHERE peso BETWEEN 500 AND 1050; -- L

SELECT * FROM componente WHERE peso NOT BETWEEN 600 AND 800; -- M

SELECT * FROM projeto WHERE cidade = "Paris" OR "Roma"; -- N

SELECT * FROM fornecedor WHERE sede = "Madrid" OR sede = "Roma"; -- O

SELECT * FROM projeto WHERE cidade != "Londres"; -- P

SELECT nome FROM fornecedor WHERE (nc BETWEEN 15000 AND 22000) AND (categ BETWEEN 10 AND 25); -- Q

SELECT * FROM componente WHERE origem = "Londres"; -- R