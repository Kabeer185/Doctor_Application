from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string
from django_rest_passwordreset.signals import reset_password_token_created

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):

    context={
        'current_user': reset_password_token.user,
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'otp': reset_password_token.key,

    }
    email_html = render_to_string('myapp/password_reset.html', context)
    email_text = render_to_string('myapp/password_reset.txt', context)
    msg=EmailMultiAlternatives(
        "Password Reset OTP",
        email_text,
       "kabeerahmad256@gmail.com",
        [reset_password_token.user.email]
    )
    msg.attach_alternative(email_html, "text/html")
    msg.send()

