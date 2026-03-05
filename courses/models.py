import uuid
from django.db import models
from django.contrib.auth import get_user_model


from django.utils.translation import gettext_lazy as _


class Location(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Ort'))

    class Meta:
        ordering = ['name']
        verbose_name = _('Ort')
        verbose_name_plural = _('Orte')

    def __str__(self):
        return self.name


from multiselectfield import MultiSelectField

def week_days():
    # Werte (z. B. ‚Mo‘) werden im Datenfeld gespeichert; Label bleibt der volle
    # Name. Wir verwenden deutsche Abkürzungen statt englischer.
    return [
        ('Mo', 'Montag'),
        ('Di', 'Dienstag'),
        ('Mi', 'Mittwoch'),
        ('Do', 'Donnerstag'),
        ('Fr', 'Freitag'),
        ('Sa', 'Samstag'),
        ('So', 'Sonntag'),
    ]


class Course(models.Model):
    name = models.CharField(max_length=200, verbose_name=_('Kursname'))
    description = models.TextField(blank=True, verbose_name=_('Beschreibung'))
    locations = models.ManyToManyField(Location, blank=True, verbose_name=_('Orte'))
    start_date = models.DateField(verbose_name=_('Beginn'), null=True, blank=True)
    end_date = models.DateField(verbose_name=_('Ende'), null=True, blank=True)
    start_time = models.TimeField(verbose_name=_('Startzeit'))
    end_time = models.TimeField(verbose_name=_('Endzeit'))
    days = MultiSelectField(choices=week_days(), verbose_name=_('Wochentage'))
    max_participants = models.PositiveIntegerField(verbose_name=_('Maximale Teilnehmer'))
    price_member = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_('Preis Mitglied'))
    price_non_member = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_('Preis Nicht-Mitglied'))
    allow_half = models.BooleanField(default=False, verbose_name=_('Halber Kurs erlaubt'))
    is_closed = models.BooleanField(
        default=False,
        verbose_name=_('Anmeldung gesperrt'),
        help_text=_('Wenn aktiv, können sich keine neuen Teilnehmer anmelden.'),
    )
    # Text field for backwards compatibility / display. New code should
    # use ``instructor_user`` to relate a course to an actual user account.
    instructor = models.CharField(max_length=200, blank=True, verbose_name=_('Kursleitung'))

    # optional FK to a Django user who is responsible for the course.  Using a
    # real user makes it easy to restrict admin access later on and avoids the
    # fragile name/email comparison that would otherwise be necessary.
    from django.conf import settings
    instructor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Kursleitung (Benutzer)'),
        help_text=_('Wähle den Benutzer, der für diesen Kurs verantwortlich ist.'),
    )

    def __str__(self):
        return f"{self.name} ({self.start_date}–{self.end_date})"

    def current_registrations(self):
        return self.registration_set.filter(status='CONFIRMED').count()

    def is_full(self):
        return self.current_registrations() >= self.max_participants

    def free_spots(self):
        """Gibt die Anzahl freier Plätze zurück (niemals negativ)."""
        return max(0, self.max_participants - self.current_registrations())

    def session_count(self):
        """Count how many class sessions occur between start_date and end_date based on selected weekdays."""
        if not (self.start_date and self.end_date):
            return 0
        # Kürzel müssen den gespeicherten Werten aus week_days() entsprechen (deutsch)
        day_map = {'Mo': 0, 'Di': 1, 'Mi': 2, 'Do': 3, 'Fr': 4, 'Sa': 5, 'So': 6}
        desired = {day_map[d] for d in self.days if d in day_map} if self.days else set()
        if not desired:
            return 0
        count = 0
        current = self.start_date
        from datetime import timedelta
        while current <= self.end_date:
            if current.weekday() in desired:
                count += 1
            current += timedelta(days=1)
        return count

    def clean(self):
        # ensure end_date is not before start_date
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': _('Enddatum darf nicht vor dem Startdatum liegen.')})

    class Meta:
        verbose_name = _('Kurs')
        verbose_name_plural = _('Kurse')


class Registration(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', _('Bestätigt')),
        ('WAITLIST', _('Warteliste')),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name=_('Kurs'))
    first_name = models.CharField(max_length=100, verbose_name=_('Vorname'))
    last_name = models.CharField(max_length=100, verbose_name=_('Nachname'))
    email = models.EmailField(verbose_name=_('E-Mail'))
    iban = models.CharField(max_length=34, verbose_name=_('IBAN'))
    bic = models.CharField(max_length=11, blank=True, verbose_name=_('BIC'))
    account_holder = models.CharField(max_length=200, verbose_name=_('Kontoinhaber'))
    terms_accepted = models.BooleanField(default=False, verbose_name=_('Bedingungen akzeptiert'))
    is_member = models.BooleanField(default=False, verbose_name=_('Mitglied'))
    half_course = models.BooleanField(default=False, verbose_name=_('Halber Kurs'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='CONFIRMED', verbose_name=_('Status'))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    cancel_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_('Storno-Token'))

    class Meta:
        verbose_name = _('Anmeldung')
        verbose_name_plural = _('Anmeldungen')

    def price(self):
        base = self.course.price_member if self.is_member else self.course.price_non_member
        if self.half_course and self.course.allow_half:
            return base / 2
        return base

    def total_price(self):
        # Preis ist als Festbetrag definiert; keine Multiplikation mit Einheiten
        return self.price()

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.course.name}"


from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=Registration)
def promote_from_waitlist(sender, instance, **kwargs):
    """Wenn eine bestätigte Anmeldung gelöscht wird und der Kurs nicht mehr voll
    ist, rückt automatisch die älteste Wartelisten-Anmeldung nach."""
    if instance.status != 'CONFIRMED':
        return
    course = instance.course
    if course.is_full():
        return
    next_waiting = (
        Registration.objects
        .filter(course=course, status='WAITLIST')
        .order_by('created')
        .first()
    )
    if next_waiting:
        next_waiting.status = 'CONFIRMED'
        next_waiting.save(update_fields=['status'])