from django.shortcuts import render, get_object_or_404, redirect
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
    """Bestätigungs-E-Mail mit Storno-Link an den Anmelder senden."""
    cancel_url = request.build_absolute_uri(
        reverse('course_cancel', args=[registration.cancel_token])
    )
    days = ', '.join(registration.course.days)
    locations = ', '.join(loc.name for loc in registration.course.locations.all())

    subject = render_to_string(
        'courses/email/confirmation_subject.txt',
        {'registration': registration}
    ).strip()
    body = render_to_string(
        'courses/email/confirmation_body.txt',
        {'registration': registration, 'cancel_url': cancel_url, 'days': days, 'locations': locations}
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
    today = date.today()
    courses = Course.objects.filter(end_date__gte=today)
    return render(request, 'courses/course_list.html', {'courses': courses})


def register(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Anmeldung gesperrt → sofort zurück mit Fehlermeldung
    if course.is_closed:
        messages.error(request, _("Die Anmeldung für diesen Kurs ist derzeit geschlossen."))
        return redirect('course_list')

    if request.method == 'POST':
        form = RegistrationForm(request.POST, course=course)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Doppel-Anmeldung verhindern
            if Registration.objects.filter(course=course, email__iexact=email).exists():
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
    """Bestätigungsseite nach erfolgreicher Anmeldung."""
    registration = get_object_or_404(Registration, cancel_token=token)
    return render(request, 'courses/confirmation.html', {'registration': registration})


def course_cancel(request, token):
    """Storno-Seite: zeigt Bestätigung, löscht bei POST die Anmeldung."""
    registration = get_object_or_404(Registration, cancel_token=token)
    if request.method == 'POST':
        registration.delete()
        return render(request, 'courses/cancel_done.html')
    return render(request, 'courses/cancel_confirm.html', {'registration': registration})


def privacy(request):
    return render(request, 'courses/privacy.html')


def impressum(request):
    return render(request, 'courses/impressum.html')
