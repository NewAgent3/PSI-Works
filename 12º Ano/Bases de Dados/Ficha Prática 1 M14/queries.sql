SELECT * FROM pessoa;

SELECT * FROM pessoa
WHERE idade = 35;

SELECT id_pessoa, nome, salario FROM pessoa
WHERE idade > 17;

SELECT mensagem FROM mensagem
WHERE id_Msg != 20;

SELECT nome, salario FROM pessoa
WHERE idade > 30;

SELECT id_pessoa, nome, idade, salario FROM pessoa
WHERE idade >= 30 AND idade <= 40;

SELECT id_pessoa, nome, idade, salario FROM pessoa
WHERE idade NOT BETWEEN 30 AND 40;

SELECT mensagem FROM mensagem
WHERE id_Msg BETWEEN 5 AND 20;

SELECT nome, salario FROM pessoa
WHERE idade > 30 AND salario BETWEEN 90000 AND 150000;

SELECT nome, telefone FROM pessoa
WHERE (salario <= 90000 or salario >= 150000) AND idade BETWEEN 20 AND 30;

