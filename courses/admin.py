from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.http import urlencode
from django.http import HttpResponseRedirect, HttpResponse
from .models import Location, Course, Registration


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'start_date', 'end_date',
        'start_time', 'end_time', 'days',
        'utilization_display', 'registrations_link', 'attendance_export_link', 'is_closed',
    )
    list_editable = ('is_closed',)
    list_filter = ('is_closed', 'days', 'locations', 'start_date', 'instructor_user')
    inlines = [RegistrationInline]
    readonly_fields = ('session_count_display',)
    actions = ['export_attendance_list']

    def utilization_display(self, obj):
        confirmed = obj.current_registrations()
        total = obj.max_participants
        pct = int(confirmed / total * 100) if total else 0
        if pct >= 100:
            color = '#c00000'
        elif pct >= 75:
            color = '#e67e00'
        else:
            color = '#2e7d32'
        return format_html(
            '<span style="color:{};font-weight:bold;">{}/{}</span> '
            '<span style="color:#888;font-size:0.85em;">({}&nbsp;%)</span>',
            color, confirmed, total, pct,
        )
    utilization_display.short_description = _('Auslastung')

    def registrations_link(self, obj):
        confirmed = obj.registration_set.filter(status='CONFIRMED').count()
        waitlist  = obj.registration_set.filter(status='WAITLIST').count()
        url = (
            reverse('admin:courses_registration_changelist')
            + '?' + urlencode({'course__id__exact': obj.pk})
        )
        label = f'{confirmed} Teilnehmer'
        if waitlist:
            label += f' + {waitlist} Warteliste'
        return format_html('<a href="{}">{} &rarr;</a>', url, label)
    registrations_link.short_description = _('Anmeldungen')
    registrations_link.admin_order_field = None

    def attendance_export_link(self, obj):
        url = reverse('admin:courses_course_export_attendance', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" '
            'style="background:#c00000;color:#fff;padding:3px 10px;'
            'border-radius:4px;white-space:nowrap;font-size:0.85em;'
            'text-decoration:none;">'
            '&#8595; Excel</a>',
            url
        )
    attendance_export_link.short_description = _('Anwesenheitsliste')
    attendance_export_link.admin_order_field = None

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<int:course_id>/export-attendance/',
                self.admin_site.admin_view(self.export_attendance_direct),
                name='courses_course_export_attendance',
            ),
        ]
        return custom + urls

    def export_attendance_direct(self, request, course_id):
        """Direkt-Download der Anwesenheitsliste für einen einzelnen Kurs."""
        from django.shortcuts import get_object_or_404
        course = get_object_or_404(Course, pk=course_id)
        # Kursleitung darf nur eigene Kurse exportieren
        if (
            request.user.groups.filter(name='Kursleitung').exists()
            and course.instructor_user != request.user
        ):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        from django.contrib.admin import ModelAdmin
        qs = Course.objects.filter(pk=course_id)
        return self.export_attendance_list(request, qs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Kursleitung').exists():
            # limit to courses where the logged‑in user has been assigned
            return qs.filter(instructor_user=request.user)
        return qs

    def has_change_permission(self, request, obj=None):
        # Kursleitung may not change any data; they only need to list/export
        if request.user.groups.filter(name='Kursleitung').exists():
            if obj is None:
                return True
            return obj.instructor_user == request.user
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.groups.filter(name='Kursleitung').exists():
            return False
        return super().has_delete_permission(request, obj)

    def session_count_display(self, obj):
        return obj.session_count()
    session_count_display.short_description = _('Einheiten')

    def export_attendance_list(self, request, queryset):
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from django.http import HttpResponse
        import zipfile, io

        red_fill   = PatternFill(start_color='C00000', end_color='C00000', fill_type='solid')
        grey_fill  = PatternFill(start_color='D8D8D8', end_color='D8D8D8', fill_type='solid')
        white_fill = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')
        thin       = Side(style='thin')
        border     = Border(left=thin, right=thin, top=thin, bottom=thin)
        center     = Alignment(horizontal='center', vertical='center')
        left_align = Alignment(horizontal='left', vertical='center')

        def make_wb(course):
            wb = Workbook()
            ws = wb.active
            ws.title = 'Anwesenheit'

            dates     = course.session_dates()
            locations = ', '.join(l.name for l in course.locations.all()) or '-'
            days_str  = ', '.join(course.days) if course.days else '-'
            last_col  = get_column_letter(3 + len(dates))

            # ── Zeile 1: Kursname ──────────────────────────────────────────
            ws.merge_cells(f'A1:{last_col}1')
            c = ws['A1']
            c.value     = f'Anwesenheitsliste – {course.name}'
            c.font      = Font(color='FFFFFF', bold=True, size=14)
            c.fill      = red_fill
            c.alignment = center
            ws.row_dimensions[1].height = 24

            # ── Zeile 2: Kursinfo ──────────────────────────────────────────
            ws.merge_cells(f'A2:{last_col}2')
            c = ws['A2']
            c.value = (
                f'Zeitraum: {course.start_date.strftime("%d.%m.%Y")} – '
                f'{course.end_date.strftime("%d.%m.%Y")}   |   '
                f'Zeit: {course.start_time.strftime("%H:%M")} – '
                f'{course.end_time.strftime("%H:%M")} Uhr   |   '
                f'Tage: {days_str}   |   Ort: {locations}   |   '
                f'Einheiten: {len(dates)}'
            )
            c.font      = Font(size=10)
            c.fill      = grey_fill
            c.alignment = left_align
            ws.row_dimensions[2].height = 16

            # ── Zeile 3: Leerzeile ─────────────────────────────────────────
            ws.row_dimensions[3].height = 8

            # ── Zeile 4: Spaltenüberschriften ──────────────────────────────
            for col, h in enumerate(['Nr.', 'Nachname', 'Vorname'], 1):
                c = ws.cell(row=4, column=col, value=h)
                c.font      = Font(color='FFFFFF', bold=True, size=11)
                c.fill      = red_fill
                c.border    = border
                c.alignment = center

            for i, d in enumerate(dates, 1):
                c = ws.cell(row=4, column=3 + i,
                            value=d.strftime('%d.%m.\n%a'))
                c.font      = Font(color='FFFFFF', bold=True, size=10)
                c.fill      = red_fill
                c.border    = border
                c.alignment = Alignment(horizontal='center', vertical='center',
                                        wrap_text=True)
            ws.row_dimensions[4].height = 30

            # ── Datenzeilen ────────────────────────────────────────────────
            registrations = (
                course.registration_set
                .filter(status='CONFIRMED')
                .order_by('last_name', 'first_name')
            )
            for idx, reg in enumerate(registrations, 1):
                data_row  = 4 + idx
                row_fill  = white_fill if idx % 2 == 1 else grey_fill

                for col, val in enumerate([idx, reg.last_name, reg.first_name], 1):
                    c = ws.cell(row=data_row, column=col, value=val)
                    c.border    = border
                    c.fill      = row_fill
                    c.alignment = center if col == 1 else left_align

                for i in range(1, len(dates) + 1):
                    c = ws.cell(row=data_row, column=3 + i, value='')
                    c.border    = border
                    c.fill      = row_fill
                    c.alignment = center

                ws.row_dimensions[data_row].height = 18

            # ── Spaltenbreiten ─────────────────────────────────────────────
            ws.column_dimensions['A'].width = 5
            ws.column_dimensions['B'].width = 22
            ws.column_dimensions['C'].width = 16
            for i in range(1, len(dates) + 1):
                ws.column_dimensions[get_column_letter(3 + i)].width = 7

            # Erste 3 Spalten einfrieren
            ws.freeze_panes = 'D5'
            return wb

        courses = list(queryset)
        if len(courses) == 1:
            wb = make_wb(courses[0])
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            safe = courses[0].name.replace('/', '-')
            response['Content-Disposition'] = f'attachment; filename="Anwesenheit_{safe}.xlsx"'
            wb.save(response)
            return response

        # Mehrere Kurse → ZIP
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for course in courses:
                xlsx = io.BytesIO()
                make_wb(course).save(xlsx)
                safe = course.name.replace('/', '-')
                zf.writestr(f'Anwesenheit_{safe}.xlsx', xlsx.getvalue())
        buf.seek(0)
        response = HttpResponse(buf, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename="Anwesenheitslisten.zip"'
        return response

    export_attendance_list.short_description = str(_("Anwesenheitsliste als Excel exportieren"))


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('course', 'last_name', 'first_name', 'email', 'status')
    list_filter = ('status', 'course')
    search_fields = ('first_name', 'last_name', 'email')
    actions = ['export_as_csv', 'export_debits', 'export_wiso_meinverein']

    def changelist_view(self, request, extra_context=None):
        # Kursleitung ohne Kurs-Filter → direkt zur Kursliste schicken
        if (
            request.user.groups.filter(name='Kursleitung').exists()
            and 'course__id__exact' not in request.GET
        ):
            return HttpResponseRedirect(
                reverse('admin:courses_course_changelist')
            )
        return super().changelist_view(request, extra_context)

    def get_actions(self, request):
        actions = super().get_actions(request)
        # WISO-Export enthält IBAN/BIC – nur Kassierer und Superuser dürfen ihn sehen
        is_kassierer = request.user.groups.filter(name='Kassierer').exists()
        if not (request.user.is_superuser or is_kassierer):
            actions.pop('export_wiso_meinverein', None)
        return actions

    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        field_names = ['course', 'first_name', 'last_name', 'email', 'status', 'terms_accepted', 'price', 'created']
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=registrations.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([
                obj.course.name,
                obj.first_name,
                obj.last_name,
                obj.email,
                obj.status,
                obj.terms_accepted,
                obj.price(),
                obj.created,
            ])
        return response
    export_as_csv.short_description = str(_('Anmeldungen als CSV exportieren'))

    def export_debits(self, request, queryset):
        """CSV für den Kassierer: nur die wirklich nötigen Daten, semikolongetrennt
        (wir verwenden `;` weil Excel in Deutschland sonst Probleme mit
        Kommas in Zahlen hat)."""
        import csv
        from django.http import HttpResponse

        # Felder, wie sie in der ersten Zeile stehen sollen
        headers = [
            str(_('Kurs')),
            str(_('Vorname')),
            str(_('Nachname')),
            str(_('IBAN')),
            str(_('BIC')),
            str(_('Kontoinhaber')),
            str(_('Betrag')),
        ]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=einzuege.csv'
        # Excel-kompatibler Separator
        writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        for reg in queryset.filter(status='CONFIRMED'):
            amount = '{:.2f}'.format(reg.total_price()).replace('.', ',')
            writer.writerow([
                reg.course.name,
                reg.first_name,
                reg.last_name,
                reg.iban,
                reg.bic or '',
                reg.account_holder,
                amount,
            ])
        return response
    export_debits.short_description = _('Einzüge als CSV exportieren')

    def export_wiso_meinverein(self, request, queryset):
        """Exportiert bestätigte Anmeldungen als CSV-Datei im Format von
        WISO MeinVerein (Buhl) für den SEPA-Lastschrift-Import.

        Pflichtfelder laut WisoMeinVerein:
          Vorname, Nachname, IBAN, BIC, Kontoinhaber,
          Betrag, Verwendungszweck, Mandatsreferenz, Mandatsdatum
        """
        from django.contrib import messages
        from django.http import HttpResponse
        import csv

        # Hard-Guard: IBAN/BIC sind datenschutzrelevant – Zugriff nur für Kassierer/Superuser
        is_kassierer = request.user.groups.filter(name='Kassierer').exists()
        if not (request.user.is_superuser or is_kassierer):
            self.message_user(request, _('Sie haben keine Berechtigung für diesen Export.'), messages.ERROR)
            return

        headers = [
            'Vorname',
            'Nachname',
            'IBAN',
            'BIC',
            'Kontoinhaber',
            'Betrag',
            'Verwendungszweck',
            'Mandatsreferenz',
            'Mandatsdatum',
        ]

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename=wiso_meinverein_lastschriften.csv'
        # WisoMeinVerein erwartet Semikolon als Trennzeichen
        writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)

        for reg in queryset.filter(status='CONFIRMED'):
            # Betrag im deutschen Format (Komma als Dezimaltrennzeichen)
            amount = '{:.2f}'.format(reg.total_price()).replace('.', ',')
            # Mandatsdatum = Datum der Kursanmeldung (= Erteilung des SEPA-Mandats)
            mandate_date = reg.created.strftime('%d.%m.%Y')
            # Eindeutige Mandatsreferenz aus Kürzel + Anmelde-ID
            mandate_ref = f'KURS-{reg.id:06d}'
            # Verwendungszweck: Kursname + ggf. Halber Kurs
            purpose_parts = [reg.course.name]
            if reg.half_course and reg.course.allow_half:
                purpose_parts.append('(Halber Kurs)')
            purpose = ' '.join(purpose_parts)

            writer.writerow([
                reg.first_name,
                reg.last_name,
                reg.iban,
                reg.bic or '',
                reg.account_holder,
                amount,
                purpose,
                mandate_ref,
                mandate_date,
            ])
        return response
    export_wiso_meinverein.short_description = _('WISO MeinVerein – SEPA-Lastschriften exportieren')

    # permission overrides for group-based access
    def has_module_permission(self, request):
        # Kursleitung or Kassierer can view the module/app
        if request.user.groups.filter(name__in=['Kursleitung', 'Kassierer']).exists():
            return True
        return super().has_module_permission(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Kursleitung').exists():
            # only registrations for courses the user is responsible for
            return qs.filter(course__instructor_user=request.user)
        return qs

    def has_view_permission(self, request, obj=None):
        # Kursleitung and Kassierer can view list; object-level filtering happens in get_queryset
        if request.user.groups.filter(name__in=['Kursleitung', 'Kassierer']).exists():
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        # nobody may add registrations via admin
        return False

    def has_change_permission(self, request, obj=None):
        # Kursleitung or Kassierer may not edit individual registrations but need
        # change perm to see actions on the changelist.
        if request.user.groups.filter(name__in=['Kursleitung', 'Kassierer']).exists():
            return False if obj else True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # only staff outside Kursleitung/Kassierer may delete
        if request.user.groups.filter(name__in=['Kursleitung', 'Kassierer']).exists():
            return False
        return super().has_delete_permission(request, obj)
