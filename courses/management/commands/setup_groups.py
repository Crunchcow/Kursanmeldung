from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from courses.models import Registration, Course

class Command(BaseCommand):
    help = 'Setup groups and permissions for Kursleitung and Abteilungsleitung'

    def handle(self, *args, **options):
        # Create Kursleitung group
        kursleitung_group, created = Group.objects.get_or_create(name='Kursleitung')
        if created:
            self.stdout.write(self.style.SUCCESS('Created group: Kursleitung'))
        
        # Get permissions
        registration_ct = ContentType.objects.get_for_model(Registration)
        course_ct = ContentType.objects.get_for_model(Course)
        
        # Assign view permissions to Kursleitung
        view_registration_perm = Permission.objects.get(
            content_type=registration_ct,
            codename='view_registration'
        )
        view_course_perm = Permission.objects.get(
            content_type=course_ct,
            codename='view_course'
        )
        
        kursleitung_group.permissions.add(view_registration_perm, view_course_perm)
        self.stdout.write(self.style.SUCCESS('Added permissions to Kursleitung group'))
        
        self.stdout.write(self.style.SUCCESS('Setup complete!'))
