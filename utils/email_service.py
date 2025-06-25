from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class EmailService:

    @staticmethod
    def send_email(subject, to_email, template_name, context, from_email=None):
        """
        Envía un email HTML con texto alternativo.

        :param subject: Asunto del email
        :param to_email: Destinatario (string o lista)
        :param template_name: Nombre del template HTML (ej: "emails/account_activation.html")
        :param context: Diccionario con datos para el template
        :param from_email: Email del remitente (opcional)
        """

        from_email = from_email or settings.DEFAULT_FROM_EMAIL

        # HTML y texto plano
        html_content = render_to_string(template_name, context)
        text_content = render_to_string(template_name.replace(".html", ".txt"), context)

        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
