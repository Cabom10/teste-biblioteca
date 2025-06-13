# livro/management/commands/send_overdue_emails.py

from datetime import date
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from livro.models import Emprestimos

class Command(BaseCommand):
    help = "Envia semanalmente e‑mails de empréstimos atrasados (rodar diariamente, mas só dispara no dia definido)"

    # 0 = segunda, 6 = domingo
    WEEKLY_DAY = 4  # sexta-feira

    def handle(self, *args, **options):
        hoje = date.today()

        # Só executa no dia configurado
        if hoje.weekday() != self.WEEKLY_DAY:
            self.stdout.write(f"Ignorado: hoje é {hoje.strftime('%A')}, nada a fazer.")
            return

        atrasados = Emprestimos.objects.filter(
            data_prevista__lt=hoje,
            data_devolucao__isnull=True
        )
        if not atrasados:
            self.stdout.write("✔ Nenhum atraso encontrado.")
            return

        for emp in atrasados:
            assunto = f"[ATENÇÃO ATRASO] Devolução do livro “{emp.livro.nome}”"
            contexto = {
                'nome': emp.nome_emprestado_anonimo or emp.email_emprestado,
                'titulo': emp.livro.nome,
                'data_prevista': emp.data_prevista,
            }
            html_content = render_to_string('emails/alerta_atraso.html', contexto)

            msg = EmailMultiAlternatives(
                assunto,
                '',  # texto simples vazio
                None,  # DEFAULT_FROM_EMAIL
                [emp.email_emprestado],
            )
            msg.attach_alternative(html_content, "text/html")

            # Anexa logo inline
            logo_path = finders.find('images/logo.png')
            if logo_path:
                from email.mime.image import MIMEImage
                with open(logo_path, 'rb') as f:
                    logo = MIMEImage(f.read())
                    logo.add_header('Content-ID', '<logo_cid>')
                    logo.add_header('Content-Disposition', 'inline', filename='logo.png')
                    msg.attach(logo)

            msg.send(fail_silently=False)
            self.stdout.write(f"✔ Aviso de atraso enviado a {emp.email_emprestado}")
