from livro_magia import LivroDeMagia
from bola_de_fogo import BolaDeFogo
from hipnose import Hipnose

livro_megabonk = LivroDeMagia()
livro_megabonk.adicionar(BolaDeFogo(2))
livro_megabonk.adicionar(Hipnose(3, 5))
livro_megabonk.listar()
livro_megabonk.usar_todos()
