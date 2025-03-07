import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError(
                _("Sua senha deve ter pelo menos 8 caracteres."),
                code='password_too_short',
            )

        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("Sua senha deve conter pelo menos uma letra maiúscula."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _(
            "Sua senha deve ter pelo menos 8 caracteres e conter pelo menos uma letra maiúscula."
        )