from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('home/', views.home, name = 'home'),
    path('ver_livro/<int:id>', views.ver_livros, name = 'ver_livros' ),
    path('cadastrar_livro', views.cadastrar_livro, name='cadastrar_livro'),
    path('excluir_livro/<int:id>', views.excluir_livro, name='excluir_livro'),
    path('cadastrar_categoria/', views.cadastrar_categoria, name='cadastrar_categoria'),
    path('cadastrar_emprestimo', views.cadastrar_emprestimo, name='cadastrar_emprestimo'),
    path('devolver_livro', views.devolver_livro, name="devolver_livro"),
    path('alterar_livro', views.alterar_livro, name="alterar_livro"),
    path('seus_empretismos', views.seus_emprestimos, name="seus_emprestimos"),
    path('processa_avaliacao', views.processa_avaliacao, name="processa_avaliacao"),
    path('buscar_livro/', views.buscar_livro, name='buscar_livro'),
    path('ver_livro/<int:id>/', views.ver_livros, name='ver_livro'),
    path('catalogo/', views.catalogo, name='catalogo'), 
    path('atrasos/', views.atrasos, name='atrasos'),
  


]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

