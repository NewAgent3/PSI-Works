SELECT * FROM projeto ORDER BY nr DESC; -- 1

SELECT * FROM fornecedor WHERE sede LIKE "%o%" ORDER BY nome; -- 2

SELECT * FROM componente WHERE cor LIKE "v%" ORDER BY design ASC; -- 3

SELECT * FROM componente WHERE design LIKE "%a" ORDER BY cor, peso; -- 4

SELECT nome, sede FROM fornecedor WHERE nome LIKE "%ar%" ORDER BY sede DESC; -- 5

SELECT * FROM componente WHERE peso > 300 ORDER BY peso DESC; -- 6

SELECT * FROM projeto WHERE nomep NOT LIKE "%e%" ORDER BY nomep DESC; -- 7

SELECT * FROM fcp ORDER BY quant ASC, nc DESC; -- 8

SELECT * FROM fcp WHERE quant BETWEEN 200 AND 500 ORDER BY nr; -- 9

SELECT nc FROM fcp WHERE nr = 9301 ORDER BY nc DESC; -- 10

SELECT * FROM projeto WHERE nomep LIKE "%a%" AND nomep NOT LIKE "%o%"; -- 11

SELECT * FROM fornecedor WHERE nome LIKE "P%s"; -- 12

SELECT * FROM componente WHERE cor LIKE "%ar%" AND peso > 200; -- 13

SELECT * FROM projeto WHERE nomep LIKE "____"; -- 14

SELECT * FROM fornecedor WHERE sede NOT LIKE "%a%" AND sede NOT LIKE "%e%" AND sede NOT LIKE "%i%" AND sede NOT LIKE "%o%" AND sede NOT LIKE "%u%"; -- 15

SELECT * FROM componente WHERE design LIKE "_e%a"; -- 16

SELECT * FROM fornecedor WHERE (nome LIKE "%an%" OR nome LIKE "%er%") AND sede LIKE "%a%"; -- 17

SELECT * FROM projeto WHERE nomep LIKE "M_____"; -- 18

SELECT * FROM fcp WHERE nr != 9301 AND quant > 300; -- 19

SELECT * FROM componente WHERE cor NOT LIKE "%o%" AND peso <= 250 ORDER BY peso ASC; -- 20