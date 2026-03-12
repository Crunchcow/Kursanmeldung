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
            _("Ich habe die <a href='%(url)s' target='_blank'>Datenschutzbestimmungen</a> gelesen und akzeptiere diese.")
            % {'url': url}
        )
        # Halben Kurs nur anbieten, wenn der Kurs es erlaubt
        if course is not None and not course.allow_half:
            self.fields.pop('half_course', None)

    class Meta:
        model = Registration
        fields = ['first_name', 'last_name', 'email', 'phone', 'iban', 'bic', 'account_holder', 'is_member', 'half_course']
        labels = {
            'first_name':      _('Vorname'),
            'last_name':       _('Nachname'),
            'email':           _('E-Mail'),
            'phone':           _('Handy / Telefon'),
            'iban':            _('IBAN'),
            'bic':             _('BIC'),
            'account_holder':  _('Kontoinhaber'),
            'is_member':       _('Ich bin Vereinsmitglied'),
            'half_course':     _('Halber Kurs (50 %)'),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('accept_terms'):
            raise forms.ValidationError(_("Bitte akzeptiere die Datenschutzbestimmungen."))
        # IBAN-Validierung
        iban = cleaned.get('iban')
        if iban:
            iban_clean = iban.replace(' ', '').upper()
            cleaned['iban'] = iban_clean
            error = self._validate_iban(iban_clean)
            if error:
                self.add_error('iban', error)
        return cleaned

    @staticmethod
    def _validate_iban(iban):
        """Gibt eine Fehlermeldung zurueck oder None wenn die IBAN gueltig ist."""
        import re
        # Grundformat: 2 Buchstaben (Laendercode) + 2 Ziffern (Pruefziffer) + bis 30 alphanumerisch
        if not re.fullmatch(r'[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}', iban):
            return _('Ungültige IBAN – Format: Ländercode (z. B. DE) + 2 Prüfziffern + Kontonummer.')
        country = iban[:2]
        # Bekannte Längenregeln
        country_lengths = {
            'DE': 22, 'AT': 20, 'CH': 21, 'NL': 18, 'BE': 16,
            'FR': 27, 'ES': 24, 'IT': 27, 'PL': 28, 'GB': 22,
        }
        expected_len = country_lengths.get(country)
        if expected_len and len(iban) != expected_len:
            return _(
                'IBAN für %(country)s muss genau %(n)d Zeichen lang sein (eingegeben: %(given)d).'
            ) % {'country': country, 'n': expected_len, 'given': len(iban)}
        # Mod-97-Prüfsumme (ISO 13616)
        rearranged = iban[4:] + iban[:4]
        numeric = ''.join(str(int(c, 36)) for c in rearranged)
        if int(numeric) % 97 != 1:
            return _('Die IBAN-Prüfziffer ist ungültig. Bitte Eingabe prüfen.')
        return None
