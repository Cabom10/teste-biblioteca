from django.db import models    
from datetime import date
import datetime
from django.db.models.base import Model
from usuarios.models import Usuario

class Categoria(models.Model):
    nome = models.CharField(max_length=30)
    descricao = models.TextField()
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return self.nome


class Livros(models.Model):
    nome = models.CharField(max_length=100)
    autor = models.CharField(max_length=30)
    co_autor = models.CharField(max_length=30, blank=True)
    emprestado = models.BooleanField(default=False)
    categoria = models.ForeignKey(Categoria, on_delete=models.DO_NOTHING)
    usuario = models.ForeignKey(Usuario, on_delete=models.DO_NOTHING)
    codigo = models.CharField(max_length=50, null=True, blank=True)
    descricao = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='livros/', blank=True, null=True)

    class Meta:
        verbose_name = 'Livro'

    def __str__(self):
        return self.nome

class Emprestimos(models.Model):
    livro = models.ForeignKey(Livros, on_delete=models.CASCADE)
    nome_emprestado_anonimo = models.CharField(max_length=255)
    email_emprestado = models.EmailField()
    data_emprestimo = models.DateTimeField(auto_now_add=True)
    data_devolucao = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.livro.nome} emprestado para {self.nome_emprestado_anonimo}"



