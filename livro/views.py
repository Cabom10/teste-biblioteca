from django.shortcuts import redirect, render
from django.http import HttpResponse
from usuarios.models import Usuario
from .models import Emprestimos, Livros, Categoria
from .forms import CadastroLivro, CategoriaLivro
from django import forms
from django.db.models import Q
from django.contrib import messages

from django.utils import timezone
from datetime import timedelta
from django.contrib.staticfiles import finders  
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
import os
from django.conf import settings 


def home(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')

    usuario = Usuario.objects.get(id=request.session['usuario'])

    busca = request.GET.get('busca', '').strip()
    autor = request.GET.get('autor', '').strip()
    categoria = request.GET.get('categoria', '')
    status = request.GET.get('status', '')

    livros = Livros.objects.filter(usuario=usuario).order_by('nome')

    if busca:
        livros = livros.filter(nome__icontains=busca)
    if autor:
        livros = livros.filter(autor__icontains=autor)
    if categoria:
        livros = livros.filter(categoria_id=categoria)
    if status == 'disponivel':
        livros = livros.filter(emprestado=False)
    elif status == 'emprestado':
        livros = livros.filter(emprestado=True)

    categorias = Categoria.objects.filter(usuario=usuario).order_by('nome')

    total_livros = livros.count()
    form = CadastroLivro()
    form.fields['usuario'].initial = usuario.id
    form.fields['categoria'].queryset = categorias
    form_categoria = CategoriaLivro()
    usuarios = Usuario.objects.all()
    livros_emprestar = livros.filter(emprestado=False)
    livros_emprestados = livros.filter(emprestado=True)

    return render(request, 'home.html', {
        'livros': livros,
        'busca': busca,
        'autor': autor,
        'categorias': categorias,
        'categoria_selecionada': categoria,
        'status': status,
        'usuario_logado': usuario.id,
        'form': form,
        'form_categoria': form_categoria,
        'usuarios': usuarios,
        'total_livro': total_livros,
        'livros_emprestar': livros_emprestar,
        'livros_emprestados': livros_emprestados,
    })

def ver_livros(request, id):
    if request.session.get('usuario'):
        livro = Livros.objects.get(id=id)
        if request.session.get('usuario') == livro.usuario.id:
            usuario = Usuario.objects.get(id=request.session['usuario'])
            categoria_livro = Categoria.objects.filter(usuario=usuario).order_by('nome')

            emprestimos = Emprestimos.objects.filter(livro=livro).order_by('-data_emprestimo')

            form = CadastroLivro()
            form.fields['usuario'].initial = request.session['usuario']
            form.fields['categoria'].queryset = categoria_livro
            form_categoria = CategoriaLivro()
            usuarios = Usuario.objects.all()
            livros_emprestar = Livros.objects.filter(usuario=usuario, emprestado=False).order_by('nome')
            livros_emprestados = Livros.objects.filter(usuario=usuario, emprestado=True).order_by('nome')

            return render(request, 'ver_livro.html', {
                'livro': livro,
                'categoria_livro': categoria_livro,
                'emprestimos': emprestimos,
                'usuario_logado': request.session.get('usuario'),
                'form': form,
                'id_livro': id,
                'form_categoria': form_categoria,
                'usuarios': usuarios,
                'livros_emprestar': livros_emprestados,
                'livros_emprestados': livros_emprestados
            })
        else:
            return HttpResponse('Esse livro não é seu')
    return redirect('/auth/login/?status=2')

def cadastrar_emprestimo(request):
    if request.method == 'POST':
        nome = request.POST.get('nome_emprestado')
        email = request.POST.get('email_emprestado')
        livro_id = request.POST.get('livro_emprestado')

        # 1) Salvar empréstimo
        emprestimo = Emprestimos(
            nome_emprestado_anonimo=nome,
            email_emprestado=email,
            livro_id=livro_id,
            data_emprestimo=timezone.now(),
            data_prevista=timezone.now() + timedelta(days=30)
        )
        emprestimo.save()

        # 2) Marcar livro como emprestado
        livro = Livros.objects.get(id=livro_id)
        livro.emprestado = True
        livro.save()

        # 3) Preparar e-mail com logo inline
        assunto = f"Confirmação de Empréstimo: {livro.nome}"
        contexto = {
            'nome': nome,
            'titulo': livro.nome,
            'data_prevista': emprestimo.data_prevista,
        }
        html_content = render_to_string('emails/confirmacao_emprestimo.html', contexto)

        msg = EmailMultiAlternatives(
            assunto,
            '',                    # texto simples vazio
            None,                  # DEFAULT_FROM_EMAIL
            [email],
        )
        msg.attach_alternative(html_content, "text/html")

        # 4) Localizar e anexar a logo INLINE
        logo_path = finders.find('images/logo.png')
        if logo_path:
            with open(logo_path, 'rb') as f:
                logo = MIMEImage(f.read())
                logo.add_header('Content-ID', '<logo_cid>')
                logo.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(logo)

        # 5) Enviar
        msg.send(fail_silently=False)

        return redirect('/livro/home')

    return redirect('/livro/home')

def devolver_livro(request):
    id = request.POST.get('id_livro_devolver')
    try:
        livro_devolver = Livros.objects.get(id=id)
    except Livros.DoesNotExist:
        messages.error(request, "Livro não encontrado.")
        return redirect('/livro/home')

    livro_devolver.emprestado = False
    livro_devolver.save()

    pendentes = Emprestimos.objects.filter(livro=livro_devolver, data_devolucao__isnull=True)
    if pendentes.exists():
        emprestimo_devolver = pendentes.first()
        emprestimo_devolver.data_devolucao = timezone.now()
        emprestimo_devolver.save()
    else:
        messages.warning(request, "Nenhum empréstimo pendente encontrado para esse livro.")

    return redirect('/livro/home')

def cadastrar_livro(request):
    if request.method == 'POST':
        form = CadastroLivro(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('/livro/home')
        else:
            return HttpResponse('DADOS INVÁLIDOS')
    else:
        form = CadastroLivro()
    return render(request, 'cadastro_livro.html', {'form': form})

def excluir_livro(request, id):
    livro = Livros.objects.get(id=id).delete()
    return redirect('/livro/home')

def cadastrar_categoria(request):
    if request.method == 'POST':
        form = CategoriaLivro(request.POST)
        if form.is_valid():
            nome = form.cleaned_data['nome']
            descricao = form.cleaned_data['descricao']
            id_usuario = request.POST.get('usuario')
            if id_usuario and int(id_usuario) == int(request.session.get('usuario')):
                user = Usuario.objects.get(id=id_usuario)
                categoria = Categoria(nome=nome, descricao=descricao, usuario=user)
                categoria.save()
                return redirect('/livro/home?cadastro_categoria=1')
            else:
                return HttpResponse('Usuário inválido.')
        else:
            return HttpResponse(f'Formulário inválido: {form.errors}')

def alterar_livro(request):
    livro_id = request.POST.get('livro_id')
    nome_livro = request.POST.get('nome_livro')
    codigo       = request.POST.get('codigo')  
    autor = request.POST.get('autor')
    co_autor = request.POST.get('co_autor')
    descricao = request.POST.get('descricao')
    categoria_id = request.POST.get('categoria_id')

    categoria = Categoria.objects.get(id=categoria_id)
    livro = Livros.objects.get(id=livro_id)

    if livro.usuario.id == request.session['usuario']:
        livro.nome = nome_livro
        livro.codigo    = codigo 
        livro.autor = autor
        livro.co_autor = co_autor
        livro.descricao = descricao
        livro.categoria = categoria
        livro.save()

        return redirect(f'/livro/ver_livro/{livro_id}')
    else:
        return redirect('/auth/sair')

def seus_emprestimos(request):
    usuario = Usuario.objects.get(id=request.session['usuario'])
    emprestimos = Emprestimos.objects.filter(nome_emprestado=usuario)

    return render(request, 'seus_emprestimos.html', {
        'usuario_logado': request.session['usuario'],
        'emprestimos': emprestimos
    })

def processa_avaliacao(request):
    id_emprestimo = request.POST.get('id_emprestimo')
    opcoes = request.POST.get('opcoes')
    id_livro = request.POST.get('id_livro')

    emprestimo = Emprestimos.objects.get(id=id_emprestimo)
    emprestimo.avaliacao = opcoes
    emprestimo.save()
    return redirect(f'/livro/ver_livro/{id_livro}')

def buscar_livro(request):
    query = request.GET.get('q', '').strip()
    if query:
        try:
            livro = Livros.objects.get(nome__iexact=query)
            return redirect('ver_livro', id=livro.id)
        except Livros.DoesNotExist:
            messages.error(request, "Livro não encontrado!")
        except Livros.MultipleObjectsReturned:
            messages.warning(request, "Mais de um livro foi encontrado. Por favor, refine sua busca.")
    return redirect('home')

def catalogo(request):
    busca = request.GET.get('busca', '')
    autor = request.GET.get('autor', '')
    categoria_id = request.GET.get('categoria')
    status = request.GET.get('status')

    livros = Livros.objects.all().order_by('nome')

    if busca:
        livros = livros.filter(nome__icontains=busca)
    if autor:
        livros = livros.filter(autor__icontains=autor)
    if categoria_id:
        livros = livros.filter(categoria_id=categoria_id)
    if status == 'disponivel':
        livros = livros.filter(emprestado=False)
    elif status == 'emprestado':
        livros = livros.filter(emprestado=True)

    categorias = Categoria.objects.all().order_by('nome')

    context = {
        'livros': livros,
        'busca': busca,
        'autor': autor,
        'categorias': categorias,
        'categoria_selecionada': categoria_id,
    }

    return render(request, 'catalogo.html', context)

def atrasos(request):
    if not request.session.get('usuario'):
        return redirect('/auth/login/?status=2')

    hoje = timezone.now().date()
    atrasos = [
        {
            'usuario': emp.nome_emprestado_anonimo or emp.email_emprestado,
            'livro': emp.livro,
            'data_emprestimo': emp.data_emprestimo,
            'data_prevista': emp.data_prevista,
            'dias_atraso': (hoje - emp.data_prevista).days
        }
        for emp in Emprestimos.objects.filter(data_prevista__lt=hoje, data_devolucao__isnull=True)
    ]

    return render(request, 'atrasos.html', {
        'usuario_logado': request.session['usuario'],
        'atrasos': atrasos,
    })

