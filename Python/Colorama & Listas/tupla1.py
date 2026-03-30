coordenadas = (10, 20)
print(f"Coordenada X: {coordenadas[0]}\nCoordenada Y: {coordenadas[1]}")
coordenadas[0] = 15
# Não se pode alterar dados numa tupla!
# Pois uma tupla é feita para ser fixa
# Mas a mesma pode ser convertida para uma lista com x = list(y)
# Com x sendo a lista que vai herdar os dados da tupla, e y é a tupla.
# Tracktrace: (TypeError: 'tuple' object does not support item assignment)
