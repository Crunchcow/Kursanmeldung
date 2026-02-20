from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Location, Course, Registration


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'instructor_user', 'start_date', 'end_date', 'start_time', 'end_time', 'days', 'max_participants')
    list_filter = ('days', 'locations', 'start_date', 'instructor_user')
    inlines = [RegistrationInline]
    readonly_fields = ('session_count_display',)
    actions = ['export_attendance_list']

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
    actions = ['export_as_csv']

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
    export_as_csv.short_description = "Export ausgewählter Anmeldungen als CSV"

    # permission overrides for group-based access
    def has_module_permission(self, request):
        # Kursleitung can view the module/app
        if request.user.groups.filter(name='Kursleitung').exists():
            return True
        return super().has_module_permission(request)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.groups.filter(name='Kursleitung').exists():
            # only registrations for courses the user is responsible for
            return qs.filter(course__instructor_user=request.user)
        return qs

    def has_view_permission(self, request, obj=None):
        # Kursleitung can view list; object-level filtering happens in get_queryset
        if request.user.groups.filter(name='Kursleitung').exists():
            return True
        return super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        # nobody may add registrations via admin
        return False

    def has_change_permission(self, request, obj=None):
        # Kursleitung group can view and export only
        if request.user.groups.filter(name='Kursleitung').exists():
            return False if obj else True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # only non-Kursleitung staff can delete
        if request.user.groups.filter(name='Kursleitung').exists():
            return False
        return super().has_delete_permission(request, obj)
