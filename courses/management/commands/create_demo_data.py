"""
Management-Command: Demo-Datensaetze fuer Praesentation erzeugen.

Aufruf:
    python manage.py create_demo_data          # legt Daten an (falls noch nicht vorhanden)
    python manage.py create_demo_data --reset  # loescht alles und legt neu an

Deckt alle neuen Features ab:
  - session_mode AUTO / COUNT / MANUAL
  - course_type WATER / HALL / OTHER
  - publish_from (kuenftiger Kurs noch nicht sichtbar)
  - NRW-Feiertage werden beim Generieren uebersprungen
  - Abgelaufene Kurse fuer Archiv-Seite
  - Stornierte Anmeldungen (status=CANCELLED)
  - Individualbetrag (custom_price)
  - Handy-Feld (phone)
  - Wartelisten-Positionen
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Location, Course, CourseSession, Registration
from datetime import date, time, timedelta
import random

User = get_user_model()

# ─── Orte ─────────────────────────────────────────────────────────────────────
LOCATIONS = {
    'halle1':    'Turnhalle Grundschule',
    'halle2':    'Zweifachturnhalle',
    'schwimm':   'Schwimmhalle',
    'sportpark': 'Sportpark',
}

# ─── Kursleiter ───────────────────────────────────────────────────────────────
INSTRUCTORS = [
    {
        'username': 'monique.kramer',
        'first_name': 'Monique',
        'last_name': 'Kramer',
        'email': 'monique.kramer@westfalia-osterwick.de',
        'password': 'Demo1234!',
    },
    {
        'username': 'thomas.mueller',
        'first_name': 'Thomas',
        'last_name': 'Mueller',
        'email': 't.mueller@westfalia-osterwick.de',
        'password': 'Demo1234!',
    },
]

# ─── Kurse ────────────────────────────────────────────────────────────────────
# session_mode:
#   AUTO  = start_date + end_date + days, NRW-Feiertage raus
#   COUNT = start_date + days + num_sessions, Enddatum automatisch
#   MANUAL = Termine werden manuell als CourseSession eingetragen
#
# archived=True  => end_date in der Vergangenheit (fuer Archiv-Demo)
# publish_from   => Kurs noch nicht oeffentlich sichtbar

COURSES = [
    # ── LAUFENDE KURSE (sichtbar) ────────────────────────────────────────────
    {
        'name': 'Zumba',
        'description': 'Tanzen und Fitness – fuer alle Level geeignet.',
        'course_type': 'HALL',
        'session_mode': 'AUTO',
        'start_date': date(2026, 4, 7),
        'end_date':   date(2026, 7, 7),
        'start_time': time(19, 0),
        'end_time':   time(20, 0),
        'days': ['Di', 'Do'],
        'location': 'halle1',
        'max_participants': 15,
        'price_member': 45.00,
        'price_non_member': 65.00,
        'allow_half': False,
        'instructor': 'monique.kramer',
        'scenario': 'warteliste',
    },
    {
        'name': 'Yoga',
        'description': 'Entspannung und Koerperbewusstsein fuer Einsteiger und Fortgeschrittene.',
        'course_type': 'HALL',
        'session_mode': 'COUNT',
        'num_sessions': 12,
        'start_date': date(2026, 4, 8),
        'start_time': time(17, 30),
        'end_time':   time(19, 0),
        'days': ['Mi'],
        'location': 'halle1',
        'max_participants': 12,
        'price_member': 40.00,
        'price_non_member': 58.00,
        'allow_half': True,
        'instructor': 'monique.kramer',
        'scenario': 'fast_voll',
    },
    {
        'name': 'Aqua-Fitness',
        'description': 'Wassergymnastik – gelenkschonend und effektiv.',
        'course_type': 'WATER',
        'session_mode': 'AUTO',
        'start_date': date(2026, 4, 6),
        'end_date':   date(2026, 7, 6),
        'start_time': time(7, 30),
        'end_time':   time(8, 15),
        'days': ['Mo', 'Mi', 'Fr'],
        'location': 'schwimm',
        'max_participants': 20,
        'price_member': 55.00,
        'price_non_member': 75.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
        'scenario': 'halb',
    },
    {
        'name': 'Aqua-Zumba',
        'description': 'Zumba im Wasser – macht Spass und schont die Gelenke.',
        'course_type': 'WATER',
        'session_mode': 'COUNT',
        'num_sessions': 10,
        'start_date': date(2026, 4, 8),
        'start_time': time(19, 0),
        'end_time':   time(19, 45),
        'days': ['Mi'],
        'location': 'schwimm',
        'max_participants': 18,
        'price_member': 50.00,
        'price_non_member': 70.00,
        'allow_half': False,
        'instructor': 'monique.kramer',
        'scenario': 'voll',
    },
    {
        'name': 'Pilates',
        'description': 'Kraeftigung der Tiefenmuskulatur und Verbesserung der Koerperhaltung.',
        'course_type': 'HALL',
        'session_mode': 'AUTO',
        'start_date': date(2026, 4, 8),
        'end_date':   date(2026, 7, 1),
        'start_time': time(18, 0),
        'end_time':   time(19, 0),
        'days': ['Mi'],
        'location': 'halle1',
        'max_participants': 10,
        'price_member': 42.00,
        'price_non_member': 60.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
        'scenario': 'fast_voll',
    },
    {
        'name': 'HIIT',
        'description': 'Hochintensives Intervalltraining fuer maximalen Kalorienverbrauch.',
        'course_type': 'HALL',
        'session_mode': 'COUNT',
        'num_sessions': 16,
        'start_date': date(2026, 4, 6),
        'start_time': time(18, 30),
        'end_time':   time(19, 30),
        'days': ['Mo'],
        'location': 'halle2',
        'max_participants': 18,
        'price_member': 48.00,
        'price_non_member': 68.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
        'scenario': 'halb',
    },
    {
        'name': 'Rueckenfit',
        'description': 'Gezieltes Rueckentraining zur Vorbeugung von Beschwerden.',
        'course_type': 'HALL',
        'session_mode': 'AUTO',
        'start_date': date(2026, 4, 9),
        'end_date':   date(2026, 7, 9),
        'start_time': time(19, 15),
        'end_time':   time(20, 15),
        'days': ['Do'],
        'location': 'halle1',
        'max_participants': 14,
        'price_member': 44.00,
        'price_non_member': 62.00,
        'allow_half': True,
        'instructor': 'thomas.mueller',
        'scenario': 'fast_voll',
    },
    {
        'name': 'Tanzen fuer Kids',
        'description': 'Tanzkurs fuer Kinder von 6–12 Jahren.',
        'course_type': 'HALL',
        'session_mode': 'AUTO',
        'start_date': date(2026, 4, 7),
        'end_date':   date(2026, 7, 7),
        'start_time': time(16, 0),
        'end_time':   time(16, 45),
        'days': ['Di'],
        'location': 'halle1',
        'max_participants': 12,
        'price_member': 35.00,
        'price_non_member': 50.00,
        'allow_half': False,
        'instructor': 'monique.kramer',
        'scenario': 'halb',
    },
    {
        'name': 'Reha-Sport',
        'description': 'Sanfter Rehabilitationssport – anerkannt als Funktionstraining.',
        'course_type': 'HALL',
        'session_mode': 'AUTO',
        'start_date': date(2026, 4, 10),
        'end_date':   date(2026, 7, 10),
        'start_time': time(17, 30),
        'end_time':   time(18, 15),
        'days': ['Fr'],
        'location': 'halle1',
        'max_participants': 10,
        'price_member': 0.00,
        'price_non_member': 30.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
        'scenario': 'fast_voll',
    },
    # ── MANUELLER MODUS (Sondertermine, z.B. alle 2 Wochen) ─────────────────
    {
        'name': 'Selbstverteidigung kompakt',
        'description': 'Workshop-Reihe mit individuellen Terminen, keine feste Wochenstruktur.',
        'course_type': 'HALL',
        'session_mode': 'MANUAL',
        'start_date': date(2026, 4, 11),
        'end_date':   date(2026, 6, 20),
        'start_time': time(10, 0),
        'end_time':   time(12, 0),
        'days': ['Sa'],
        'location': 'halle2',
        'max_participants': 16,
        'price_member': 60.00,
        'price_non_member': 85.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
        'scenario': 'halb',
        # Manuelle Termine werden unten separat angelegt
        'manual_dates': [
            date(2026, 4, 11),
            date(2026, 4, 25),
            date(2026, 5, 9),
            date(2026, 5, 23),
            date(2026, 6, 6),
            date(2026, 6, 20),
        ],
    },
    # ── NOCH NICHT SICHTBAR (publish_from in der Zukunft) ────────────────────
    {
        'name': 'Spinning Herbst',
        'description': 'Spinning-Kurs fuer den Herbst – Anmeldung noch nicht freigeschaltet.',
        'course_type': 'HALL',
        'session_mode': 'COUNT',
        'num_sessions': 14,
        'start_date': date(2026, 9, 7),
        'start_time': time(18, 0),
        'end_time':   time(19, 0),
        'days': ['Mo', 'Do'],
        'location': 'halle2',
        'max_participants': 20,
        'price_member': 50.00,
        'price_non_member': 72.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
        'scenario': 'leer',
        'publish_from': date(2026, 7, 1),  # ab 1. Juli sichtbar
    },
    # ── ARCHIV-KURSE (end_date in der Vergangenheit) ─────────────────────────
    {
        'name': 'Zumba (Winter 2025)',
        'description': 'Abgeschlossener Winterkurs.',
        'course_type': 'HALL',
        'session_mode': 'AUTO',
        'start_date': date(2025, 10, 7),
        'end_date':   date(2026, 1, 27),
        'start_time': time(19, 0),
        'end_time':   time(20, 0),
        'days': ['Di', 'Do'],
        'location': 'halle1',
        'max_participants': 15,
        'price_member': 45.00,
        'price_non_member': 65.00,
        'allow_half': False,
        'instructor': 'monique.kramer',
        'scenario': 'voll',
        'archived': True,
    },
    {
        'name': 'Aqua-Fitness (Winter 2025)',
        'description': 'Abgeschlossener Winterkurs.',
        'course_type': 'WATER',
        'session_mode': 'AUTO',
        'start_date': date(2025, 10, 6),
        'end_date':   date(2026, 1, 26),
        'start_time': time(7, 30),
        'end_time':   time(8, 15),
        'days': ['Mo', 'Mi', 'Fr'],
        'location': 'schwimm',
        'max_participants': 20,
        'price_member': 55.00,
        'price_non_member': 75.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
        'scenario': 'fast_voll',
        'archived': True,
    },
    {
        'name': 'Rueckenfit (Winter 2025)',
        'description': 'Abgeschlossener Winterkurs.',
        'course_type': 'HALL',
        'session_mode': 'COUNT',
        'num_sessions': 12,
        'start_date': date(2025, 10, 9),
        'start_time': time(19, 15),
        'end_time':   time(20, 15),
        'days': ['Do'],
        'location': 'halle1',
        'max_participants': 14,
        'price_member': 44.00,
        'price_non_member': 62.00,
        'allow_half': True,
        'instructor': 'thomas.mueller',
        'scenario': 'voll',
        'archived': True,
    },
]

# ─── Teilnehmernamen ──────────────────────────────────────────────────────────
FIRST_NAMES = [
    'Anna', 'Maria', 'Laura', 'Julia', 'Sandra', 'Petra', 'Sabine', 'Monika',
    'Klaus', 'Stefan', 'Thomas', 'Michael', 'Andreas', 'Christian', 'Martin',
    'Lena', 'Hannah', 'Sophie', 'Emma', 'Lisa', 'Felix', 'Lukas', 'Jonas',
    'Tobias', 'David', 'Ralf', 'Bernd', 'Heinz', 'Gabi', 'Ursula', 'Karin',
    'Dieter', 'Werner', 'Ingrid', 'Helga', 'Bettina', 'Susanne', 'Claudia',
]
LAST_NAMES = [
    'Mueller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner',
    'Becker', 'Schulz', 'Hoffmann', 'Schaefer', 'Koch', 'Richter', 'Klein',
    'Wolf', 'Schroeder', 'Neumann', 'Braun', 'Zimmermann', 'Krause',
    'Hartmann', 'Lange', 'Lehmann', 'Schmitt', 'Werner', 'Meier', 'Kramer',
    'Huber', 'Mayer', 'Herrmann', 'Kaiser', 'Fuchs', 'Lang', 'Vogel',
]
PHONE_PREFIXES = ['0151', '0152', '0157', '0160', '0162', '0170', '0172', '0175']

random.seed(42)  # reproduzierbare Ergebnisse


def random_iban():
    return f'DE{random.randint(10, 99)}{random.randint(10000000, 99999999)}{random.randint(1000000000, 9999999999)}'


def random_phone():
    """Gibt immer eine Handynummer zurueck (Pflichtfeld)."""
    return f'{random.choice(PHONE_PREFIXES)} {random.randint(10000000, 99999999)}'


def make_registrations(course, count_confirmed, count_waitlist=0, count_cancelled=0):
    """Legt Anmeldungen in unterschiedlichen Stati an."""
    total = count_confirmed + count_waitlist + count_cancelled
    pool = [(f, l) for f in FIRST_NAMES for l in LAST_NAMES]
    names = random.sample(pool, min(total, len(pool)))

    for i, (first, last) in enumerate(names):
        if i < count_confirmed:
            status = 'CONFIRMED'
        elif i < count_confirmed + count_waitlist:
            status = 'WAITLIST'
        else:
            status = 'CANCELLED'

        # Individualbetrag bei ~10 % der Teilnehmer (Verletztungs-Sonderfall)
        custom_price = None
        if status == 'CONFIRMED' and random.random() < 0.10:
            base = float(course.price_member if random.random() < 0.6 else course.price_non_member)
            custom_price = round(base * random.uniform(0.3, 0.8), 2)

        Registration.objects.get_or_create(
            course=course,
            first_name=first,
            last_name=last,
            defaults={
                'email':          f'{first.lower()}.{last.lower()}@example.de',
                'phone':          random_phone(),
                'iban':           random_iban(),
                'bic':            'WELADED1MST',
                'account_holder': f'{first} {last}',
                'terms_accepted': True,
                'is_member':      random.choice([True, True, False]),
                'half_course':    False,
                'status':         status,
                'custom_price':   custom_price,
            }
        )


class Command(BaseCommand):
    help = 'Demo-Datensaetze fuer Praesentation anlegen (neue Architektur)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Alle vorhandenen Kurse und Anmeldungen vorher loeschen',
        )

    def handle(self, *args, **options):
        if options['reset']:
            Registration.objects.all().delete()
            CourseSession.objects.all().delete()
            Course.objects.all().delete()
            Location.objects.all().delete()
            self.stdout.write(self.style.WARNING('Alte Daten geloescht.'))

        # ── Orte ──────────────────────────────────────────────────────────────
        locs = {}
        for key, name in LOCATIONS.items():
            loc, _ = Location.objects.get_or_create(name=name)
            locs[key] = loc
        self.stdout.write(f'  Orte: {len(locs)} vorhanden')

        # ── Kursleiter ────────────────────────────────────────────────────────
        instructors = {}
        for data in INSTRUCTORS:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'first_name': data['first_name'],
                    'last_name':  data['last_name'],
                    'email':      data['email'],
                    'is_staff':   True,
                }
            )
            if created:
                user.set_password(data['password'])
                user.save()
            instructors[data['username']] = user
        self.stdout.write(f'  Kursleiter: {len(instructors)} vorhanden')

        # ── Kurse & Einheiten & Anmeldungen ───────────────────────────────────
        for cd in COURSES:
            mode       = cd.get('session_mode', 'AUTO')
            archived   = cd.get('archived', False)

            # Pflichtfelder zusammenstellen
            defaults = {
                'description':       cd['description'],
                'start_time':        cd['start_time'],
                'end_time':          cd['end_time'],
                'days':              cd['days'],
                'max_participants':  cd['max_participants'],
                'price_member':      cd['price_member'],
                'price_non_member':  cd['price_non_member'],
                'allow_half':        cd.get('allow_half', False),
                'instructor_user':   instructors[cd['instructor']],
                'instructor':        instructors[cd['instructor']].get_full_name(),
                'session_mode':      mode,
                'course_type':       cd.get('course_type', 'OTHER'),
                'publish_from':      cd.get('publish_from', None),
            }

            # end_date / num_sessions je nach Modus
            if mode in ('AUTO', 'MANUAL'):
                defaults['end_date'] = cd.get('end_date')
            elif mode == 'COUNT':
                defaults['num_sessions'] = cd['num_sessions']
                # end_date wird durch generate_sessions() gesetzt

            course, created = Course.objects.get_or_create(
                name=cd['name'],
                start_date=cd['start_date'],
                defaults=defaults,
            )
            course.locations.set([locs[cd['location']]])

            if not created:
                self.stdout.write(f'  – {course.name}: bereits vorhanden, uebersprungen')
                continue

            # ── Einheiten generieren ──────────────────────────────────────────
            if mode == 'MANUAL':
                # Manuelle Termine direkt anlegen
                for d in cd.get('manual_dates', []):
                    CourseSession.objects.create(course=course, date=d)
                # end_date auf letzten Termin setzen
                if cd.get('manual_dates'):
                    course.end_date = max(cd['manual_dates'])
                    course.save(update_fields=['end_date'])
                session_info = f'{len(cd.get("manual_dates", []))} manuelle Einheiten'
            else:
                course.generate_sessions(skip_holidays=True)
                count = course.session_count()
                session_info = f'{count} Einheiten (NRW-Feiertage herausgerechnet)'

            # ── Anmeldungen anlegen ───────────────────────────────────────────
            max_p    = cd['max_participants']
            scenario = cd.get('scenario', 'halb')

            if scenario == 'warteliste':
                make_registrations(course, max_p, count_waitlist=3, count_cancelled=1)
            elif scenario == 'voll':
                make_registrations(course, max_p, count_cancelled=2)
            elif scenario == 'fast_voll':
                make_registrations(course, max_p - random.randint(1, 2), count_cancelled=1)
            elif scenario == 'halb':
                make_registrations(course, max_p // 2)
            elif scenario == 'leer':
                pass  # keine Anmeldungen (Kurs noch nicht sichtbar)

            confirmed = course.registration_set.filter(status='CONFIRMED').count()
            waitlist  = course.registration_set.filter(status='WAITLIST').count()
            cancelled = course.registration_set.filter(status='CANCELLED').count()
            custom    = course.registration_set.exclude(custom_price=None).count()

            line = (
                f'  {"[ARCHIV]" if archived else "[NEU]    "} '
                f'{course.name} ({course.get_course_type_display()}, '
                f'{course.get_session_mode_display().split("(")[0].strip()}): '
                f'{confirmed} bestätigt'
            )
            if waitlist:
                line += f', {waitlist} Warteliste'
            if cancelled:
                line += f', {cancelled} storniert'
            if custom:
                line += f', {custom} Individualbetrag'
            line += f' | {session_info}'

            self.stdout.write(line)

        self.stdout.write(self.style.SUCCESS('\nDemo-Daten erfolgreich angelegt!'))
        self.stdout.write('')
        self.stdout.write('Logins:')
        self.stdout.write('  Admin:       python manage.py createsuperuser')
        self.stdout.write('  Kursleitung: monique.kramer / Demo1234!')
        self.stdout.write('  Kursleitung: thomas.mueller / Demo1234!')
        self.stdout.write('')
        self.stdout.write('Besonderheiten in den Demo-Daten:')
        self.stdout.write('  - Alle Modi: AUTO, COUNT, MANUAL (Selbstverteidigung kompakt)')
        self.stdout.write('  - "Spinning Herbst" sichtbar erst ab 01.07.2026 (publish_from)')
        self.stdout.write('  - 3 Archiv-Kurse (Winter 2025) auf /archiv/')
        self.stdout.write('  - Wartelisten-Anmeldungen mit sichtbarer Position')
        self.stdout.write('  - ~10% der Teilnehmer haben Individualbetrag (custom_price)')
        self.stdout.write('  - Alle Anmeldungen enthalten eine Handynummer (Pflichtfeld)')
