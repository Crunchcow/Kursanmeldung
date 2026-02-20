from django.shortcuts import render, get_object_or_404, redirect
from .models import Course, Registration
from django.utils.translation import gettext_lazy as _
from .forms import RegistrationForm


# frontend views

def course_list(request):
    from datetime import date
    today = date.today()
    courses = Course.objects.filter(end_date__gte=today)
    return render(request, 'courses/course_list.html', {'courses': courses})


def register(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            reg = form.save(commit=False)
            reg.course = course
            if course.is_full():
                reg.status = 'WAITLIST'
            reg.save()
            return redirect('course_list')
    else:
        form = RegistrationForm()
    return render(request, 'courses/register.html', {'course': course, 'form': form})


def privacy(request):
    # simple privacy page; replace text with legal content
    return render(request, 'courses/privacy.html')
