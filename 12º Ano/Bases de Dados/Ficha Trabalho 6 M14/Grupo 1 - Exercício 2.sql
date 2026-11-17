SELECT cod_concelho, desc_concelho
FROM concelho
ORDER BY n_habitantes; -- 2.1

SELECT distrito.cod_distrito, COUNT(*), SUM(n_habitantes)
FROM distrito, concelho
WHERE distrito.Cod_Distrito = concelho.Cod_Distrito
GROUP BY distrito.Cod_Distrito; -- 2.2

SELECT cod_concelho, n_habitantes/area AS densidade
FROM concelho
GROUP BY cod_concelho; -- 2.3