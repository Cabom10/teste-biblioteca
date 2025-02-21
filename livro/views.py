from datetime import date, datetime
from django.shortcuts import redirect, render
from django.http import HttpResponse
from usuarios.models import Usuario
from .models import Emprestimos, Livros, Categoria
from .forms import CadastroLivro, CategoriaLivro
from django import forms
from django.db.models import Q
from django.contrib import messages
# Create your views here.

def home(request):
    if request.session.get('usuario'):  
        usuario = Usuario.objects.get(id=request.session['usuario'])
        
        # Captura o parâmetro de filtro
        filtro_status = request.GET.get('status', '')
        
        # Busca os livros do usuário
        livros = Livros.objects.filter(usuario=usuario)
        
        # Aplica o filtro, se fornecido
        if filtro_status == 'disponivel':
            livros = livros.filter(emprestado=False)
        elif filtro_status == 'emprestado':
            livros = livros.filter(emprestado=True)
        
        total_livros = livros.count()
        form = CadastroLivro()
        form.fields['usuario'].initial = request.session['usuario']
        form.fields['categoria'].queryset = Categoria.objects.filter(usuario=usuario)     
        form_categoria = CategoriaLivro()
        usuarios = Usuario.objects.all()
        
        # Se necessário, você pode manter as query separadas para empréstimos
        livros_emprestar = Livros.objects.filter(usuario=usuario, emprestado=False)
        livros_emprestados = Livros.objects.filter(usuario=usuario, emprestado=True)

        return render(request, 'home.html', {
            'livros': livros,
            'usuario_logado': request.session.get('usuario'),
            'form': form,
            'form_categoria': form_categoria,
            'usuarios': usuarios,
            'livros_emprestar': livros_emprestar,
            'total_livro': total_livros,
            'livros_emprestados': livros_emprestados
        })
    else:
        return redirect('/auth/login/?status=2')

def ver_livros(request, id):
    if request.session.get('usuario'):
        livro = Livros.objects.get(id=id)
        if request.session.get('usuario') == livro.usuario.id:
            usuario = Usuario.objects.get(id=request.session['usuario'])
            categoria_livro = Categoria.objects.filter(usuario=request.session.get('usuario'))
            emprestimos = Emprestimos.objects.filter(livro=livro)
            form = CadastroLivro()
            form.fields['usuario'].initial = request.session['usuario']
            form.fields['categoria'].queryset = Categoria.objects.filter(usuario=usuario)
            form_categoria = CategoriaLivro()
            usuarios = Usuario.objects.all()

            livros_emprestar = Livros.objects.filter(usuario=usuario, emprestado=False)
            livros_emprestados = Livros.objects.filter(usuario=usuario, emprestado=True)

            return render(request, 'ver_livro.html', {'livro': livro,
                                                      'categoria_livro': categoria_livro,
                                                      'emprestimos': emprestimos,
                                                      'usuario_logado': request.session.get('usuario'),
                                                      'form': form,
                                                      'id_livro': id,
                                                      'form_categoria': form_categoria,
                                                      'usuarios': usuarios,
                                                      'livros_emprestar': livros_emprestar,
                                                      'livros_emprestados': livros_emprestados})
        else:
            return HttpResponse('Esse livro não é seu')
    return redirect('/auth/login/?status=2')

def cadastrar_emprestimo(request):
    if request.method == 'POST':
        nome_emprestado = request.POST.get('nome_emprestado')
        email_emprestado = request.POST.get('email_emprestado')
        livro_emprestado = request.POST.get('livro_emprestado')
        
        emprestimo = Emprestimos(nome_emprestado_anonimo=nome_emprestado,
                                 email_emprestado=email_emprestado,
                                 livro_id=livro_emprestado)
        emprestimo.save()

        livro = Livros.objects.get(id=livro_emprestado)
        livro.emprestado = True
        livro.save()
        
        return redirect('/livro/home')

def devolver_livro(request):
    id = request.POST.get('id_livro_devolver')
    try:
        livro_devolver = Livros.objects.get(id=id)
    except Livros.DoesNotExist:
        messages.error(request, "Livro não encontrado.")
        return redirect('/livro/home')
    
    # Marque o livro como não emprestado
    livro_devolver.emprestado = False
    livro_devolver.save()
    
    # Busque empréstimos pendentes (sem data_devolucao)
    pendentes = Emprestimos.objects.filter(livro=livro_devolver, data_devolucao__isnull=True)
    if pendentes.exists():
        # Atualize o primeiro empréstimo pendente (ou use .latest('data_emprestimo') se preferir o mais recente)
        emprestimo_devolver = pendentes.first()
        emprestimo_devolver.data_devolucao = datetime.now()
        emprestimo_devolver.save()
    else:
        messages.warning(request, "Nenhum empréstimo pendente encontrado para esse livro.")
    
    return redirect('/livro/home')

def cadastrar_livro(request):
    if request.method == 'POST':
        form = CadastroLivro(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('/livro/home')
        else:
            return HttpResponse('DADOS INVÁLIDOS')
        
def excluir_livro(request, id):
    livro = Livros.objects.get(id = id).delete()
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
    autor = request.POST.get('autor')
    co_autor = request.POST.get('co_autor')
    categoria_id = request.POST.get('categoria_id')

    categoria = Categoria.objects.get(id = categoria_id)
    livro = Livros.objects.get(id = livro_id)
    if livro.usuario.id == request.session['usuario']:
        livro.nome = nome_livro
        livro.autor = autor
        livro.co_autor = co_autor
        livro.categoria = categoria
        livro.save()
        return redirect(f'/livro/ver_livro/{livro_id}')
    else:
        return redirect('/auth/sair')

def seus_emprestimos(request):
    usuario = Usuario.objects.get(id = request.session['usuario'])
    emprestimos = Emprestimos.objects.filter(nome_emprestado = usuario)
    


    return render(request, 'seus_emprestimos.html', {'usuario_logado': request.session['usuario'],
                                                    'emprestimos': emprestimos})

def processa_avaliacao(request):
    id_emprestimo = request.POST.get('id_emprestimo')
    opcoes = request.POST.get('opcoes')
    id_livro = request.POST.get('id_livro')
    #TODO: Verificar segurança
    #TODO: Não permitir avaliação de livro nao devolvido
    #TODO: Colocar as estrelas
    emprestimo = Emprestimos.objects.get(id = id_emprestimo)
    emprestimo.avaliacao = opcoes
    emprestimo.save()
    return redirect(f'/livro/ver_livro/{id_livro}')

def buscar_livro(request):
    query = request.GET.get('q', '').strip()
    if query:
        try:
            # Busca exata ignorando maiúsculas/minúsculas
            livro = Livros.objects.get(nome__iexact=query)
            return redirect('ver_livro', id=livro.id)
        except Livros.DoesNotExist:
            messages.error(request, "Livro não encontrado!")
        except Livros.MultipleObjectsReturned:
            messages.warning(request, "Mais de um livro foi encontrado. Por favor, refine sua busca.")
    return redirect('home')