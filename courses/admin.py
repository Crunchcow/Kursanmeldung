from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
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
        'name', 'instructor_user', 'start_date', 'end_date',
        'start_time', 'end_time', 'days', 'max_participants',
        'utilization_display', 'is_closed',
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
        from django.http import HttpResponse

        for course in queryset:
            wb = Workbook()
            ws = wb.active
            ws.title = 'Teilnehmerliste'

            # Header style
            header_fill = PatternFill(start_color='c00000', end_color='c00000', fill_type='solid')
            header_font = Font(color='FFFFFF', bold=True, size=12)
            border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )

            # Title and course info
            ws['A1'] = f"Teilnehmerliste: {course.name}"
            ws['A1'].font = Font(bold=True, size=14)
            ws['A1'].fill = header_fill
            ws['A1'].font = Font(color='FFFFFF', bold=True, size=14)
            ws.merge_cells('A1:E1')

            row = 3
            ws[f'A{row}'] = str(_("Datum"))
            ws[f'B{row}'] = str(_("Beginn"))
            ws[f'C{row}'] = str(_("Ende"))
            ws[f'D{row}'] = str(_("Wochentage"))
            ws[f'E{row}'] = str(_("Ort"))

            ws[f'A{row+1}'] = str(course.start_date) + ' - ' + str(course.end_date)
            ws[f'B{row+1}'] = str(course.start_time)
            ws[f'C{row+1}'] = str(course.end_time)
            ws[f'D{row+1}'] = ', '.join(course.days) if course.days else '-'
            ws[f'E{row+1}'] = ', '.join([l.name for l in course.locations.all()]) if course.locations.exists() else '-'

            # Participant table header
            row = 6
            headers = [str(_('Vorname')), str(_('Nachname')), str(_("E-Mail")), str(_('Status')), str(_("Anwesend"))]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=row, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.border = border
                cell.alignment = Alignment(horizontal='center')

            # Participants
            registrations = course.registration_set.filter(status='CONFIRMED').order_by('last_name', 'first_name')
            for reg in registrations:
                row += 1
                ws.cell(row=row, column=1, value=reg.first_name).border = border
                ws.cell(row=row, column=2, value=reg.last_name).border = border
                ws.cell(row=row, column=3, value=reg.email).border = border
                ws.cell(row=row, column=4, value=reg.get_status_display()).border = border
                ws.cell(row=row, column=5, value='☐').border = border  # Checkbox
                ws.cell(row=row, column=5).alignment = Alignment(horizontal='center')

            # Set column widths
            ws.column_dimensions['A'].width = 15
            ws.column_dimensions['B'].width = 15
            ws.column_dimensions['C'].width = 15
            ws.column_dimensions['D'].width = 20
            ws.column_dimensions['E'].width = 20

            # Return Excel file
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="Teilnehmerliste_{course.name}.xlsx"'
            wb.save(response)
            return response

        # If multiple courses selected, export only the first
        return self.export_attendance_list(request, queryset[:1])

    export_attendance_list.short_description = str(_("Teilnehmerliste als Excel exportieren"))


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('course', 'first_name', 'last_name', 'email', 'status', 'terms_accepted')
    list_filter = ('status', 'course')
    search_fields = ('first_name', 'last_name', 'email')
    actions = ['export_as_csv', 'export_debits', 'export_wiso_meinverein']

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
