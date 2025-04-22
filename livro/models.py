from django.db import models
from datetime import date
import datetime
from django.db.models.base import Model
from usuarios.models import Usuario
from datetime import timedelta
from django.utils import timezone


def get_default_data_prevista():
    return timezone.now().date() + timedelta(days=7)


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


def get_default_data_emprestimo():
    return timezone.now()


class Emprestimos(models.Model):
    nome_emprestado_anonimo = models.CharField(max_length=100, null=True, blank=True)
    email_emprestado = models.EmailField()
    livro = models.ForeignKey(Livros, on_delete=models.CASCADE)
    data_emprestimo = models.DateTimeField(default=get_default_data_emprestimo)
    data_prevista = models.DateField(default=get_default_data_prevista)
    data_devolucao = models.DateField(null=True, blank=True)
    

    def __str__(self):
        return f"{self.nome_emprestado_anonimo or self.email_emprestado} - {self.livro}"
