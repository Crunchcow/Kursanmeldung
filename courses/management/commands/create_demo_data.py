"""
Management-Command: Demo-Datensätze für Präsentation erzeugen.

Aufruf:
    python manage.py create_demo_data          # legt Daten an (falls noch nicht vorhanden)
    python manage.py create_demo_data --reset  # löscht alles und legt neu an
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Location, Course, Registration
from datetime import date, time
import random

User = get_user_model()

# ─── Orte ────────────────────────────────────────────────────────────────────
LOCATIONS = [
    'Turnhalle Grundschule',
    'Zweifachturnhalle',
    'Schwimmhalle',
    'Sportpark',
]

# ─── Kursleiter (werden als Benutzer angelegt) ────────────────────────────────
INSTRUCTORS = [
    {'username': 'monique.kramer', 'first_name': 'Monique', 'last_name': 'Kramer',
     'email': 'monique.kramer@westfalia-osterwick.de', 'password': 'Demo1234!'},
    {'username': 'thomas.mueller', 'first_name': 'Thomas', 'last_name': 'Müller',
     'email': 't.mueller@westfalia-osterwick.de', 'password': 'Demo1234!'},
]

# ─── Kurse ────────────────────────────────────────────────────────────────────
COURSES = [
    {
        'name': 'Zumba',
        'description': 'Tanzen und Fitness – für alle Level geeignet.',
        'start_date': date(2026, 4, 1),
        'end_date':   date(2026, 7, 2),
        'start_time': time(19, 0),
        'end_time':   time(20, 0),
        'days': ['Di', 'Do'],
        'location': 'Turnhalle Grundschule',
        'max_participants': 15,
        'price_member': 45.00,
        'price_non_member': 65.00,
        'allow_half': False,
        'instructor': 'monique.kramer',
    },
    {
        'name': 'Yoga',
        'description': 'Entspannung und Körperbewusstsein für Einsteiger und Fortgeschrittene.',
        'start_date': date(2026, 4, 1),
        'end_date':   date(2026, 7, 1),
        'start_time': time(17, 30),
        'end_time':   time(19, 0),
        'days': ['Mi'],
        'location': 'Turnhalle Grundschule',
        'max_participants': 12,
        'price_member': 40.00,
        'price_non_member': 58.00,
        'allow_half': True,
        'instructor': 'monique.kramer',
    },
    {
        'name': 'Pilates',
        'description': 'Kräftigung der Tiefenmuskulatur und Verbesserung der Körperhaltung.',
        'start_date': date(2026, 4, 1),
        'end_date':   date(2026, 7, 1),
        'start_time': time(18, 0),
        'end_time':   time(19, 0),
        'days': ['Mi'],
        'location': 'Turnhalle Grundschule',
        'max_participants': 10,
        'price_member': 42.00,
        'price_non_member': 60.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
    },
    {
        'name': 'Aqua-Zumba',
        'description': 'Zumba im Wasser – gelenkschonend und effektiv.',
        'start_date': date(2026, 4, 1),
        'end_date':   date(2026, 7, 1),
        'start_time': time(19, 0),
        'end_time':   time(19, 45),
        'days': ['Mi'],
        'location': 'Schwimmhalle',
        'max_participants': 20,
        'price_member': 50.00,
        'price_non_member': 70.00,
        'allow_half': False,
        'instructor': 'monique.kramer',
    },
    {
        'name': 'HIIT',
        'description': 'Hochintensives Intervalltraining für maximalen Kalorienverbrauch.',
        'start_date': date(2026, 4, 6),
        'end_date':   date(2026, 7, 6),
        'start_time': time(18, 30),
        'end_time':   time(19, 30),
        'days': ['Mo'],
        'location': 'Zweifachturnhalle',
        'max_participants': 18,
        'price_member': 48.00,
        'price_non_member': 68.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
    },
    {
        'name': 'Rückenfit',
        'description': 'Gezieltes Rückentraining zur Vorbeugung von Beschwerden.',
        'start_date': date(2026, 4, 2),
        'end_date':   date(2026, 7, 2),
        'start_time': time(19, 15),
        'end_time':   time(20, 15),
        'days': ['Do'],
        'location': 'Turnhalle Grundschule',
        'max_participants': 14,
        'price_member': 44.00,
        'price_non_member': 62.00,
        'allow_half': True,
        'instructor': 'thomas.mueller',
    },
    {
        'name': 'Tanzen für Kids',
        'description': 'Tanzkurs für Kinder von 6–12 Jahren.',
        'start_date': date(2026, 4, 7),
        'end_date':   date(2026, 7, 7),
        'start_time': time(16, 0),
        'end_time':   time(16, 45),
        'days': ['Di'],
        'location': 'Turnhalle Grundschule',
        'max_participants': 12,
        'price_member': 35.00,
        'price_non_member': 50.00,
        'allow_half': False,
        'instructor': 'monique.kramer',
    },
    {
        'name': 'Reha-Sport',
        'description': 'Sanfter Rehabilitationssport – anerkannt als Funktionstraining.',
        'start_date': date(2026, 4, 3),
        'end_date':   date(2026, 7, 3),
        'start_time': time(17, 30),
        'end_time':   time(18, 15),
        'days': ['Fr'],
        'location': 'Turnhalle Grundschule',
        'max_participants': 10,
        'price_member': 0.00,
        'price_non_member': 30.00,
        'allow_half': False,
        'instructor': 'thomas.mueller',
    },
]

# ─── Zufällige Teilnehmernamen ────────────────────────────────────────────────
FIRST_NAMES = [
    'Anna', 'Maria', 'Laura', 'Julia', 'Sandra', 'Petra', 'Sabine', 'Monika',
    'Klaus', 'Stefan', 'Thomas', 'Michael', 'Andreas', 'Christian', 'Martin',
    'Lena', 'Hannah', 'Sophie', 'Emma', 'Lisa', 'Felix', 'Lukas', 'Jonas',
    'Tobias', 'David', 'Ralf', 'Bernd', 'Heinz', 'Gabi', 'Ursula',
]
LAST_NAMES = [
    'Müller', 'Schmidt', 'Schneider', 'Fischer', 'Weber', 'Meyer', 'Wagner',
    'Becker', 'Schulz', 'Hoffmann', 'Schäfer', 'Koch', 'Richter', 'Klein',
    'Wolf', 'Schröder', 'Neumann', 'Braun', 'Zimmermann', 'Krause',
    'Hartmann', 'Lange', 'Lehmann', 'Schmitt', 'Werner', 'Meier', 'Kramer',
]

random.seed(42)  # reproduzierbare Ergebnisse


def random_iban():
    return f'DE{random.randint(10,99)}{random.randint(10000000,99999999)}{random.randint(1000000000,9999999999)}'


def make_registrations(course, count_confirmed, count_waitlist=0):
    names = random.sample(
        [(f, l) for f in FIRST_NAMES for l in LAST_NAMES],
        count_confirmed + count_waitlist
    )
    for i, (first, last) in enumerate(names):
        status = 'CONFIRMED' if i < count_confirmed else 'WAITLIST'
        Registration.objects.get_or_create(
            course=course,
            first_name=first,
            last_name=last,
            defaults={
                'email': f'{first.lower()}.{last.lower()}@example.de',
                'iban': random_iban(),
                'bic': 'WELADED1MST',
                'account_holder': f'{first} {last}',
                'terms_accepted': True,
                'is_member': random.choice([True, True, False]),
                'half_course': False,
                'status': status,
            }
        )


class Command(BaseCommand):
    help = 'Demo-Datensätze für Präsentation anlegen'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Alle vorhandenen Kurse und Anmeldungen vorher löschen',
        )

    def handle(self, *args, **options):
        if options['reset']:
            Registration.objects.all().delete()
            Course.objects.all().delete()
            Location.objects.all().delete()
            self.stdout.write(self.style.WARNING('Alte Daten gelöscht.'))

        # Orte
        locs = {}
        for name in LOCATIONS:
            loc, _ = Location.objects.get_or_create(name=name)
            locs[name] = loc
        self.stdout.write(f'  Orte: {len(locs)} vorhanden')

        # Kursleiter
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

        # Kurse & Anmeldungen
        for cd in COURSES:
            course, created = Course.objects.get_or_create(
                name=cd['name'],
                start_date=cd['start_date'],
                defaults={
                    'description':       cd['description'],
                    'end_date':          cd['end_date'],
                    'start_time':        cd['start_time'],
                    'end_time':          cd['end_time'],
                    'days':              cd['days'],
                    'max_participants':  cd['max_participants'],
                    'price_member':      cd['price_member'],
                    'price_non_member':  cd['price_non_member'],
                    'allow_half':        cd['allow_half'],
                    'instructor_user':   instructors[cd['instructor']],
                    'instructor':        instructors[cd['instructor']].get_full_name(),
                }
            )
            course.locations.set([locs[cd['location']]])

            if created:
                # Auslastung variieren: voll, halb belegt, mit Warteliste
                max_p = cd['max_participants']
                scenario = random.choice(['fast_voll', 'halb', 'warteliste'])
                if scenario == 'warteliste':
                    make_registrations(course, max_p, count_waitlist=3)
                elif scenario == 'fast_voll':
                    make_registrations(course, max_p - random.randint(1, 2))
                else:
                    make_registrations(course, max_p // 2)

                confirmed = course.registration_set.filter(status='CONFIRMED').count()
                waitlist  = course.registration_set.filter(status='WAITLIST').count()
                self.stdout.write(
                    f'  ✓ {course.name}: {confirmed} bestätigt'
                    + (f', {waitlist} Warteliste' if waitlist else '')
                )
            else:
                self.stdout.write(f'  – {course.name}: bereits vorhanden, übersprungen')

        self.stdout.write(self.style.SUCCESS('\nDemo-Daten erfolgreich angelegt!'))
        self.stdout.write('Tipp: Login für Kursleitung – monique.kramer / Demo1234!')
