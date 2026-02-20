from django import forms
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from .models import Registration


class RegistrationForm(forms.ModelForm):
    accept_terms = forms.BooleanField(required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set label lazily to avoid url reverse at import
        url = reverse_lazy('privacy')
        self.fields['accept_terms'].label = mark_safe(
            _("Ich akzeptiere die Teilnahmebedingungen und <a href='%(url)s' target='_blank'>Datenschutzbestimmungen</a>")
            % {'url': url}
        )

    class Meta:
        model = Registration
        fields = ['first_name', 'last_name', 'email', 'iban', 'bic', 'account_holder', 'is_member', 'half_course']
        labels = {
            'first_name': _('Vorname'),
            'last_name': _('Nachname'),
            'email': _('E-Mail'),
            'iban': _('IBAN'),
            'bic': _('BIC'),
            'account_holder': _('Kontoinhaber'),
            'is_member': _('Mitglied'),
            'half_course': _('Halber Kurs'),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('accept_terms'):
            raise forms.ValidationError("Du musst die Bedingungen akzeptieren.")
        return cleaned
