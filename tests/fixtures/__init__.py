"""Fixtures que montam cada funcionalidade com a infraestrutura real (SQLite, disco).

Ficam fora de api/ de propósito: o teste ao lado de um use case só importa a própria camada e o
domínio, e o import-linter continua valendo para ele; quem liga a infraestrutura real é a fixture.
"""
