import secrets as _secrets
import urllib.parse as _urlparse
import requests as _requests
import hmac
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Course, Registration
from django.utils.translation import gettext_lazy as _
from .forms import RegistrationForm
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings as django_settings
from django.urls import reverse


class NoSignupAdapter(DefaultAccountAdapter):
    """Custom adapter that blocks signup."""
    def is_open_for_signup(self, request):
        return False


def _send_confirmation_email(request, registration):
    """Bestaetigung per E-Mail mit Storno-Link an den Anmelder senden."""
    cancel_url = request.build_absolute_uri(
        reverse('course_cancel', args=[registration.cancel_token])
    )
    days = ', '.join(registration.course.days)
    locations = ', '.join(loc.name for loc in registration.course.locations.all())

    ical_url = request.build_absolute_uri(
        reverse('course_ical', args=[registration.course.id])
    ) if registration.status == 'CONFIRMED' else None

    subject = render_to_string(
        'courses/email/confirmation_subject.txt',
        {'registration': registration}
    ).strip()
    body = render_to_string(
        'courses/email/confirmation_body.txt',
        {'registration': registration, 'cancel_url': cancel_url,
         'days': days, 'locations': locations, 'ical_url': ical_url}
    )
    send_mail(
        subject=subject,
        message=body,
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        recipient_list=[registration.email],
        fail_silently=True,
    )


# frontend views

def course_list(request):
    from datetime import date
    from django.db.models import Q
    today = date.today()

    courses = (
        Course.objects
        .filter(end_date__gte=today)
        .filter(Q(publish_from__isnull=True) | Q(publish_from__lte=today))
        .order_by('start_date')
    )

    # Optionale Filter aus GET-Parametern
    day_filter  = request.GET.get('day', '')
    type_filter = request.GET.get('type', '')
    if day_filter:
        courses = courses.filter(days__contains=day_filter)
    if type_filter:
        courses = courses.filter(course_type=type_filter)

    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'day_filter': day_filter,
        'type_filter': type_filter,
        'week_days': [
            ('Mo', 'Montag'), ('Di', 'Dienstag'), ('Mi', 'Mittwoch'),
            ('Do', 'Donnerstag'), ('Fr', 'Freitag'), ('Sa', 'Samstag'), ('So', 'Sonntag'),
        ],
        'course_types': Course.COURSE_TYPE_CHOICES,
    })


def register(request, course_id):
    from datetime import date
    course = get_object_or_404(Course, id=course_id)

    # Anmeldung manuell gesperrt
    if course.is_closed:
        messages.error(request, _("Die Anmeldung für diesen Kurs ist derzeit geschlossen."))
        return redirect('course_list')

    # Automatische Sperre: Kurs hat bereits begonnen
    if course.start_date and course.start_date <= date.today():
        messages.error(request, _("Die Anmeldung für diesen Kurs ist nicht mehr möglich, da der Kurs bereits begonnen hat."))
        return redirect('course_list')

    if request.method == 'POST':
        form = RegistrationForm(request.POST, course=course)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Doppel-Anmeldung verhindern (ignoriere stornierte)
            if Registration.objects.filter(course=course, email__iexact=email).exclude(status='CANCELLED').exists():
                messages.error(request, _("Mit dieser E-Mail-Adresse besteht bereits eine Anmeldung für diesen Kurs."))
                return render(request, 'courses/register.html', {'course': course, 'form': form})
            reg = form.save(commit=False)
            reg.course = course
            reg.terms_accepted = True
            if course.is_full():
                reg.status = 'WAITLIST'
            reg.save()
            _send_confirmation_email(request, reg)
            return redirect('course_confirmation', token=reg.cancel_token)
    else:
        form = RegistrationForm(course=course)
    return render(request, 'courses/register.html', {'course': course, 'form': form})


def course_confirmation(request, token):
    """Bestaetigung nach erfolgreicher Anmeldung."""
    registration = get_object_or_404(Registration, cancel_token=token)
    return render(request, 'courses/confirmation.html', {'registration': registration})


def course_cancel(request, token):
    """Storno-Seite: setzt Status auf CANCELLED statt Loeschen.
    Stornierung ist nur bis 48 Stunden vor Kursbeginn möglich."""
    from datetime import date, datetime, timedelta, timezone as dt_tz

    registration = get_object_or_404(Registration, cancel_token=token)

    # Bereits storniert
    if registration.status == 'CANCELLED':
        return render(request, 'courses/cancel_done.html')

    # 48-Stunden-Sperre prüfen (gilt nicht für Warteliste)
    course = registration.course
    if registration.status != 'WAITLIST' and course.start_date:
        # Kursbeginn = start_date + start_time, in UTC
        start_naive = datetime.combine(course.start_date, course.start_time)
        start_dt = start_naive.replace(tzinfo=dt_tz.utc)
        now_dt = datetime.now(tz=dt_tz.utc)
        if now_dt >= start_dt - timedelta(hours=48):
            return render(request, 'courses/cancel_too_late.html',
                          {'registration': registration, 'course': course})

    if request.method == 'POST':
        registration.status = 'CANCELLED'
        registration.save(update_fields=['status'])
        return render(request, 'courses/cancel_done.html')
    return render(request, 'courses/cancel_confirm.html', {'registration': registration})


def course_ical(request, course_id):
    """Gibt eine .ics-Datei mit allen Kurseinheiten zum Kalender-Import zurueck."""
    from datetime import datetime, timezone as dt_tz
    import icalendar

    course = get_object_or_404(Course, id=course_id)
    cal = icalendar.Calendar()
    cal.add('prodid', '-//Kursanmeldung//DE')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', course.name)

    location_str = ', '.join(loc.name for loc in course.locations.all()) or ''

    for session_date in course.session_dates():
        event = icalendar.Event()
        event.add('summary', course.name)
        event.add('dtstart', datetime(
            session_date.year, session_date.month, session_date.day,
            course.start_time.hour, course.start_time.minute,
            tzinfo=dt_tz.utc,
        ))
        event.add('dtend', datetime(
            session_date.year, session_date.month, session_date.day,
            course.end_time.hour, course.end_time.minute,
            tzinfo=dt_tz.utc,
        ))
        if location_str:
            event.add('location', location_str)
        if course.description:
            event.add('description', course.description)
        cal.add_component(event)

    response = HttpResponse(cal.to_ical(), content_type='text/calendar; charset=utf-8')
    safe_name = course.name.replace(' ', '_').replace('/', '-')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}.ics"'
    return response


def privacy(request):
    return render(request, 'courses/privacy.html')


def impressum(request):
    return render(request, 'courses/impressum.html')


# ---------------------------------------------------------------------------
# Interner Webhook: User-Sync von ClubAuth
# ---------------------------------------------------------------------------

@csrf_exempt
@require_POST
def clubauth_sync_user(request):
    """Empfängt eine User-Anlage/-Aktualisierung von ClubAuth.
    Gesichert via INTERNAL_API_KEY im Authorization-Header."""
    expected_key = getattr(django_settings, 'INTERNAL_API_KEY', '')
    auth_header  = request.META.get('HTTP_AUTHORIZATION', '')
    token        = auth_header.removeprefix('Bearer ').strip()

    if not expected_key or not hmac.compare_digest(token, expected_key):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        payload = json.loads(request.body)
    except (ValueError, KeyError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    from django.contrib.auth.models import User, Group

    email      = payload.get('email', '').lower().strip()
    first_name = payload.get('first_name', '')
    last_name  = payload.get('last_name', '')
    role       = payload.get('role', '')
    action     = payload.get('action', 'upsert')  # 'upsert' oder 'remove'

    if not email:
        return JsonResponse({'error': 'Missing email'}, status=400)

    kursleitung_group, _ = Group.objects.get_or_create(name='Kursleitung')
    kassierer_group, _   = Group.objects.get_or_create(name='Kassierer')

    if action == 'remove':
        # Zugriff entziehen: is_staff + is_active entfernen, Gruppen leeren.
        # Suche per E-Mail (case-insensitive) um auch manuell angelegte User zu finden.
        qs = User.objects.filter(email__iexact=email)
        qs.update(is_staff=False, is_active=False)
        for user in qs:
            user.groups.remove(kursleitung_group, kassierer_group)
        return JsonResponse({'status': 'removed', 'email': email})

    if action == 'delete':
        # User vollständig löschen (FK zu Kursen wird auf NULL gesetzt)
        deleted, _ = User.objects.filter(email__iexact=email).delete()
        return JsonResponse({'status': 'deleted', 'email': email, 'count': deleted})

    # Bestehenden User per E-Mail suchen (case-insensitiv), um Duplikate
    # bei manuell angelegten Accounts mit anderem username zu vermeiden.
    user = User.objects.filter(username=email).first() \
           or User.objects.filter(email__iexact=email).order_by('date_joined').first()
    if user is not None:
        User.objects.filter(pk=user.pk).update(
            email=email,
            first_name=first_name or user.first_name,
            last_name=last_name or user.last_name,
            is_staff=True,
            is_active=True,
        )
        user.refresh_from_db()
        created = False
    else:
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_staff=True,
            is_active=True,
        )
        created = True

    if role == 'kursleitung':
        user.groups.add(kursleitung_group)
        user.groups.remove(kassierer_group)
    elif role == 'kassierer':
        user.groups.add(kassierer_group)
        user.groups.remove(kursleitung_group)
    else:
        user.groups.remove(kursleitung_group, kassierer_group)

    return JsonResponse({'status': 'created' if created else 'updated', 'email': email})


# ---------------------------------------------------------------------------
# OIDC-Integration mit ClubAuth
# ---------------------------------------------------------------------------

def oidc_login(request):
    """Startet den OIDC-Flow: leitet zu ClubAuth weiter."""
    base_url = getattr(django_settings, 'OIDC_BASE_URL', '').rstrip('/')
    client_id = getattr(django_settings, 'OIDC_CLIENT_ID', '')
    redirect_uri = getattr(django_settings, 'OIDC_REDIRECT_URI', '')

    if not base_url or not client_id:
        messages.error(request, 'OIDC nicht konfiguriert.')
        return redirect('/admin/login/')

    state = _secrets.token_urlsafe(32)
    request.session['oidc_state'] = state

    # Sicherstellen, dass next nur lokale Pfade akzeptiert werden
    next_url = request.GET.get('next', '/admin/')
    parsed = _urlparse.urlparse(next_url)
    if parsed.scheme or parsed.netloc:
        next_url = '/admin/'
    request.session['oidc_next'] = next_url

    params = _urlparse.urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile roles',
        'state': state,
    })
    return redirect(f'{base_url}/o/authorize/?{params}')


def oidc_callback(request):
    """Empfängt den OIDC-Callback, legt den Django-User an und loggt ihn ein."""
    from django.contrib.auth.models import User, Group
    from django.contrib.auth import login as auth_login

    # State-Validierung (verhindert CSRF-Angriffe auf den OAuth-Flow)
    # WICHTIG: Bei Fehler auf die Startseite leiten, NICHT auf /admin/login/,
    # da das erneut den OIDC-Flow auslöst und eine Redirect-Schleife erzeugt.
    state = request.GET.get('state')
    if not state or state != request.session.pop('oidc_state', None):
        messages.error(request, 'Anmeldung fehlgeschlagen – bitte erneut versuchen.')
        return redirect('course_list')

    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Kein Authentifizierungscode erhalten.')
        return redirect('course_list')

    # OIDC_INTERNAL_URL: interne Adresse für Server-zu-Server-Anfragen (z.B. http://127.0.0.1:8010)
    # Fällt auf OIDC_BASE_URL zurück wenn nicht gesetzt.
    internal_url = getattr(django_settings, 'OIDC_INTERNAL_URL',
                           getattr(django_settings, 'OIDC_BASE_URL', '')).rstrip('/')
    try:
        token_resp = _requests.post(
            f'{internal_url}/o/token/',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': getattr(django_settings, 'OIDC_REDIRECT_URI', ''),
                'client_id': getattr(django_settings, 'OIDC_CLIENT_ID', ''),
                'client_secret': getattr(django_settings, 'OIDC_CLIENT_SECRET', ''),
            },
            timeout=10,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get('access_token', '')

        userinfo_resp = _requests.get(
            f'{internal_url}/o/userinfo/',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()
    except (_requests.RequestException, ValueError) as e:
        messages.error(request, 'Fehler bei der Verbindung zum Authentifizierungsserver.')
        return redirect('course_list')
    email = userinfo.get('email', '').lower().strip()
    name = userinfo.get('name', '')
    roles = userinfo.get('roles', {})
    ka_role = roles.get('kursanmeldung', {}).get('role', '')

    if not email or not ka_role:
        messages.error(request, 'Kein Zugriff auf die Kursanmeldung.')
        return redirect('course_list')

    # Name aufteilen
    parts = name.split(' ', 1)
    first_name = parts[0] if parts else ''
    last_name = parts[1] if len(parts) > 1 else ''

    # Django-User suchen oder neu anlegen.
    # Reihenfolge: 1) username=email (Sync-Konvention), 2) email-Suche, 3) anlegen.
    # So werden Duplikate (manuell angelegte User mit anderem username) sicher gefunden.
    try:
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        users_by_email = User.objects.filter(email__iexact=email)
        if users_by_email.exists():
            # Bevorzuge den mit username=email, sonst den ältesten
            user = users_by_email.filter(username=email).first() \
                   or users_by_email.order_by('date_joined').first()
        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
            )

    # Zugriffsrechte setzen
    user.is_staff = True
    user.is_active = True
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.save(update_fields=['is_staff', 'is_active', 'first_name', 'last_name'])

    # Gruppen synchronisieren — immer vollständig setzen/entfernen
    kursleitung_group, _ = Group.objects.get_or_create(name='Kursleitung')
    kassierer_group, _   = Group.objects.get_or_create(name='Kassierer')

    if ka_role == 'kursleitung':
        user.groups.add(kursleitung_group)
        user.groups.remove(kassierer_group)
    elif ka_role == 'kassierer':
        user.groups.add(kassierer_group)
        user.groups.remove(kursleitung_group)
    else:
        # verwaltung o.ä. — keine einschränkende Gruppe nötig
        user.groups.remove(kursleitung_group)
        user.groups.remove(kassierer_group)

    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    next_url = request.session.pop('oidc_next', '/admin/')
    return redirect(next_url)
