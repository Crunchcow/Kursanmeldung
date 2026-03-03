from django import forms
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from .models import Registration


class RegistrationForm(forms.ModelForm):
    accept_terms = forms.BooleanField(required=True)
    accept_sepa = forms.BooleanField(
        required=True,
        label=_(
            "Ich erteile hiermit ein SEPA-Lastschriftmandat. Der Verein ist berechtigt, "
            "den fälligen Kursbetrag von meinem oben angegebenen Konto einzuziehen. "
            "Wenn das Konto die erforderliche Deckung nicht aufweist, besteht seitens "
            "des kontoführenden Kreditinstituts keine Verpflichtung zur Einlösung. "
            "Ich kann innerhalb von 8 Wochen ab Buchungsdatum die Erstattung des "
            "belasteten Betrages verlangen."
        ),
    )

    def __init__(self, *args, course=None, **kwargs):
        super().__init__(*args, **kwargs)
        # set label lazily to avoid url reverse at import
        url = reverse_lazy('privacy')
        self.fields['accept_terms'].label = mark_safe(
            _("Ich akzeptiere die Teilnahmebedingungen und <a href='%(url)s' target='_blank'>Datenschutzbestimmungen</a>")
            % {'url': url}
        )
        # Halben Kurs nur anbieten, wenn der Kurs es erlaubt
        if course is not None and not course.allow_half:
            self.fields.pop('half_course', None)

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
            'half_course': _('Halber Kurs (50 %)'),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('accept_terms'):
            raise forms.ValidationError(_("Du musst die Bedingungen akzeptieren."))
        # IBAN: Leerzeichen entfernen, Länge 15–34
        iban = cleaned.get('iban')
        if iban:
            iban_clean = iban.replace(' ', '').upper()
            cleaned['iban'] = iban_clean
            if not (15 <= len(iban_clean) <= 34):
                self.add_error('iban', _('Bitte geben Sie eine gültige IBAN ein.'))
        return cleaned
