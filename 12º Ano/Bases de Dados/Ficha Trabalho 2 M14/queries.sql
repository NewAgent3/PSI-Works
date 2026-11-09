SELECT * FROM projeto WHERE nomep LIKE "%UMM%"; -- A

SELECT * FROM fornecedor WHERE nome LIKE "J%"; -- B

SELECT design, cor FROM componente WHERE cor LIKE "%a"; -- C

SELECT * FROM fornecedor WHERE sede LIKE "%Ma%"; -- D

SELECT * FROM componente WHERE design LIKE "%la%"; -- E

SELECT * FROM componente WHERE cor NOT LIKE "%ran%"; -- F

SELECT * FROM componente WHERE design LIKE "_i%"; -- G

SELECT nome FROM fornecedor WHERE nome LIKE "%ee%"; -- H

SELECT * FROM projeto ORDER BY nomep; -- I

SELECT serie, design, cor FROM componente ORDER BY peso DESC; -- J

SELECT * FROM fcp ORDER BY nc, nr; -- K

SELECT * FROM fcp WHERE quant < 350 ORDER BY nr DESC; -- L

SELECT nc FROM fcp WHERE nr = 9301 ORDER BY nc DESC; -- M