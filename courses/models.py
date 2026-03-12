import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField


class Location(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Ort'))

    class Meta:
        ordering = ['name']
        verbose_name = _('Ort')
        verbose_name_plural = _('Orte')

    def __str__(self):
        return self.name


def week_days():
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
    # ── Einheitenmodus ─────────────────────────────────────────────────────────
    SESSION_MODE_AUTO   = 'AUTO'
    SESSION_MODE_COUNT  = 'COUNT'
    SESSION_MODE_MANUAL = 'MANUAL'
    SESSION_MODE_CHOICES = [
        (SESSION_MODE_AUTO,   _('Automatisch (Start + Ende + Wochentage, NRW-Feiertage übersprungen)')),
        (SESSION_MODE_COUNT,  _('Einheitenanzahl (Start + Wochentage + Anzahl, Enddatum wird berechnet)')),
        (SESSION_MODE_MANUAL, _('Manuell (Einzeltermine selbst bestimmen)')),
    ]

    # ── Kurstyp ───────────────────────────────────────────────────────────────
    TYPE_WATER = 'WATER'
    TYPE_HALL  = 'HALL'
    TYPE_OTHER = 'OTHER'
    COURSE_TYPE_CHOICES = [
        (TYPE_WATER, _('Wasserkurs')),
        (TYPE_HALL,  _('Hallenkurs')),
        (TYPE_OTHER, _('Sonstiges')),
    ]

    name = models.CharField(max_length=200, verbose_name=_('Kursname'))
    description = models.TextField(blank=True, verbose_name=_('Beschreibung'))
    locations = models.ManyToManyField(Location, blank=True, verbose_name=_('Orte'))
    start_date = models.DateField(verbose_name=_('Beginn'), null=True, blank=True)
    end_date = models.DateField(verbose_name=_('Ende'), null=True, blank=True)
    start_time = models.TimeField(verbose_name=_('Startzeit'))
    end_time = models.TimeField(verbose_name=_('Endzeit'))
    days = MultiSelectField(choices=week_days(), verbose_name=_('Wochentage'), blank=True)
    max_participants = models.PositiveIntegerField(verbose_name=_('Maximale Teilnehmer'))
    price_member = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_('Preis Mitglied'))
    price_non_member = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_('Preis Nicht-Mitglied'))
    allow_half = models.BooleanField(default=False, verbose_name=_('Halber Kurs erlaubt'))
    is_closed = models.BooleanField(
        default=False,
        verbose_name=_('Anmeldung gesperrt'),
        help_text=_('Wenn aktiv, können sich keine neuen Teilnehmer anmelden.'),
    )
    instructor = models.CharField(max_length=200, blank=True, verbose_name=_('Kursleitung'))

    from django.conf import settings
    instructor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_('Kursleitung (Benutzer)'),
        help_text=_('Wähle den Benutzer, der für diesen Kurs verantwortlich ist.'),
    )

    # ── Neue Felder Phase 1 ───────────────────────────────────────────────────
    session_mode = models.CharField(
        max_length=10,
        choices=SESSION_MODE_CHOICES,
        default=SESSION_MODE_AUTO,
        verbose_name=_('Einheitenmodus'),
    )
    num_sessions = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Anzahl Einheiten'),
        help_text=_('Nur für Modus "Einheitenanzahl". Enddatum wird automatisch berechnet.'),
    )
    course_type = models.CharField(
        max_length=10,
        choices=COURSE_TYPE_CHOICES,
        default=TYPE_OTHER,
        verbose_name=_('Kurstyp'),
    )
    publish_from = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Sichtbar ab'),
        help_text=_('Leer = sofort sichtbar. Sonst wird der Kurs erst ab diesem Datum angezeigt.'),
    )

    def __str__(self):
        return f"{self.name} ({self.start_date}\u2013{self.end_date})"

    def current_registrations(self):
        return self.registration_set.filter(status='CONFIRMED').count()

    def is_full(self):
        return self.current_registrations() >= self.max_participants

    def free_spots(self):
        """Gibt die Anzahl freier Plaetze zurueck (niemals negativ)."""
        return max(0, self.max_participants - self.current_registrations())

    def session_dates(self):
        """Gibt die Liste aller aktiven Kurs-Termine zurueck (datetime.date).

        Prioritaet:
        1. CourseSession-Objekte vorhanden -> diese verwenden
           (gilt fuer alle Modi nach generate_sessions() oder manuellem Eintrag)
        2. Fallback fuer AUTO ohne generierte Sessions -> on-the-fly berechnen
        """
        db_sessions = self.sessions.filter(is_cancelled=False).order_by('date')
        if db_sessions.exists():
            return [s.date for s in db_sessions]
        # Fallback: bisheriges Verhalten fuer bestehende Kurse ohne Sessions
        if self.session_mode == self.SESSION_MODE_AUTO:
            return self._calc_auto_dates()
        return []

    def _calc_auto_dates(self):
        """Berechnet Termine aus start_date/end_date/days (ohne Feiertage, nur Fallback)."""
        from datetime import timedelta
        if not (self.start_date and self.end_date):
            return []
        day_map = {'Mo': 0, 'Di': 1, 'Mi': 2, 'Do': 3, 'Fr': 4, 'Sa': 5, 'So': 6}
        desired = {day_map[d] for d in self.days if d in day_map} if self.days else set()
        if not desired:
            return []
        dates = []
        current = self.start_date
        while current <= self.end_date:
            if current.weekday() in desired:
                dates.append(current)
            current += timedelta(days=1)
        return dates

    def session_count(self):
        """Anzahl der Kurs-Einheiten."""
        return len(self.session_dates())

    def generate_sessions(self, skip_holidays=True):
        """Generiert CourseSession-Objekte basierend auf dem Modus.

        - AUTO:   iteriert von start_date bis end_date, ueberspringt NRW-Feiertage
        - COUNT:  generiert num_sessions Einheiten vorwaerts ab start_date, setzt end_date
        - MANUAL: nichts tun - Sessions muessen manuell ueber Admin eingetragen werden
        """
        from datetime import timedelta, date as date_type

        if self.session_mode == self.SESSION_MODE_MANUAL:
            return  # Manuelle Sessions werden nicht ueberschrieben

        nrw_holidays: set = set()
        if skip_holidays:
            try:
                import holidays as hol_lib
                start_year = self.start_date.year if self.start_date else date_type.today().year
                end_year = start_year + 2
                nrw_holidays = set(hol_lib.Germany(state='NW', years=range(start_year, end_year)))
            except Exception:
                pass

        day_map = {'Mo': 0, 'Di': 1, 'Mi': 2, 'Do': 3, 'Fr': 4, 'Sa': 5, 'So': 6}
        desired = {day_map[d] for d in self.days if d in day_map} if self.days else set()

        sessions_to_create = []

        if self.session_mode == self.SESSION_MODE_AUTO:
            if not (self.start_date and self.end_date):
                return
            current = self.start_date
            while current <= self.end_date:
                if current.weekday() in desired and current not in nrw_holidays:
                    sessions_to_create.append(CourseSession(course=self, date=current))
                current += timedelta(days=1)

        elif self.session_mode == self.SESSION_MODE_COUNT:
            if not self.start_date or not self.num_sessions or not desired:
                return
            count = 0
            current = self.start_date
            safety = self.start_date.replace(year=self.start_date.year + 6)
            while count < self.num_sessions and current < safety:
                if current.weekday() in desired and current not in nrw_holidays:
                    sessions_to_create.append(CourseSession(course=self, date=current))
                    count += 1
                current += timedelta(days=1)
            if sessions_to_create:
                Course.objects.filter(pk=self.pk).update(end_date=sessions_to_create[-1].date)
                self.end_date = sessions_to_create[-1].date

        self.sessions.all().delete()
        CourseSession.objects.bulk_create(sessions_to_create)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': _('Enddatum darf nicht vor dem Startdatum liegen.')})
        if self.session_mode == self.SESSION_MODE_COUNT and not self.num_sessions:
            raise ValidationError({'num_sessions': _('Bitte Anzahl Einheiten angeben.')})

    class Meta:
        verbose_name = _('Kurs')
        verbose_name_plural = _('Kurse')


class CourseSession(models.Model):
    """Eine einzelne Kurseinheit an einem bestimmten Datum."""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('Kurs'),
    )
    date = models.DateField(verbose_name=_('Datum'))
    is_cancelled = models.BooleanField(
        default=False,
        verbose_name=_('Ausgefallen'),
        help_text=_('Einheit fällt aus (z.B. nachträglicher Feiertag, Ausnahme.'),
    )
    note = models.CharField(max_length=200, blank=True, verbose_name=_('Hinweis'))

    class Meta:
        ordering = ['date']
        verbose_name = _('Einheit')
        verbose_name_plural = _('Einheiten')

    def __str__(self):
        status = ' [ausgefallen]' if self.is_cancelled else ''
        return f"{self.course.name} \u2013 {self.date.strftime('%d.%m.%Y')}{status}"


class Registration(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', _('Bestätigt')),
        ('WAITLIST',  _('Warteliste')),
        ('CANCELLED', _('Storniert')),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name=_('Kurs'))
    first_name = models.CharField(max_length=100, verbose_name=_('Vorname'))
    last_name = models.CharField(max_length=100, verbose_name=_('Nachname'))
    email = models.EmailField(verbose_name=_('E-Mail'))
    phone = models.CharField(
        max_length=30,
        verbose_name=_('Handy / Telefon'),
        help_text=_('Für Rückfragen bei Kursänderungen.'),
    )
    iban = models.CharField(max_length=34, verbose_name=_('IBAN'))
    bic = models.CharField(max_length=11, blank=True, verbose_name=_('BIC'))
    account_holder = models.CharField(max_length=200, verbose_name=_('Kontoinhaber'))
    terms_accepted = models.BooleanField(default=False, verbose_name=_('Bedingungen akzeptiert'))
    is_member = models.BooleanField(default=False, verbose_name=_('Mitglied'))
    half_course = models.BooleanField(default=False, verbose_name=_('Halber Kurs'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='CONFIRMED', verbose_name=_('Status'))
    custom_price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Individualbetrag'),
        help_text=_('Wenn gesetzt, wird dieser Betrag statt des Standardpreises verwendet (z.B. bei Verletzung).'),
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name=_('Erstellt am'))
    cancel_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name=_('Storno-Token'))

    class Meta:
        verbose_name = _('Anmeldung')
        verbose_name_plural = _('Anmeldungen')

    def price(self):
        """Effektiver Preis. Individualbetrag hat hoechste Prioritaet."""
        if self.custom_price is not None:
            return self.custom_price
        base = self.course.price_member if self.is_member else self.course.price_non_member
        if self.half_course and self.course.allow_half:
            return base / 2
        return base

    def total_price(self):
        return self.price()

    def waitlist_position(self):
        """Position auf der Warteliste (1-basiert), oder None wenn nicht WAITLIST."""
        if self.status != 'WAITLIST':
            return None
        return (
            Registration.objects
            .filter(course=self.course, status='WAITLIST', created__lte=self.created)
            .count()
        )

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.course.name}"


from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


def _promote_next_from_waitlist(course):
    """Rueckt den aeltesten Wartelistenplatz nach wenn Kapazitaet frei ist."""
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
        _send_waitlist_promotion_email(next_waiting)


@receiver(post_delete, sender=Registration)
def promote_from_waitlist_on_delete(sender, instance, **kwargs):
    """Beim Loeschen einer bestaetigten Anmeldung nachrücken lassen."""
    if instance.status != 'CONFIRMED':
        return
    _promote_next_from_waitlist(instance.course)


@receiver(post_save, sender=Registration)
def promote_from_waitlist_on_cancel(sender, instance, created, **kwargs):
    """Wenn eine bestaetigte Anmeldung storniert wird, rueckt der naechste nach."""
    if created:
        return
    if instance.status != 'CANCELLED':
        return
    _promote_next_from_waitlist(instance.course)


def _send_waitlist_promotion_email(registration):
    """Benachrichtigt einen Wartelistenplatz-Nachrücker per E-Mail."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings as django_settings
    from django.urls import reverse

    cancel_url = (
        django_settings.SITE_URL.rstrip('/')
        + reverse('course_cancel', args=[registration.cancel_token])
    )
    days = ', '.join(registration.course.days)
    locations = ', '.join(loc.name for loc in registration.course.locations.all())

    ical_url = (
        django_settings.SITE_URL.rstrip('/')
        + reverse('course_ical', args=[registration.course.id])
    )

    subject = render_to_string(
        'courses/email/waitlist_promotion_subject.txt',
        {'registration': registration},
    ).strip()
    body = render_to_string(
        'courses/email/waitlist_promotion_body.txt',
        {'registration': registration, 'cancel_url': cancel_url,
         'days': days, 'locations': locations, 'ical_url': ical_url},
    )
    send_mail(
        subject,
        body,
        django_settings.DEFAULT_FROM_EMAIL,
        [registration.email],
        fail_silently=True,
    )
