"""Management Command: Synchronisiert Kursanmeldungs-User aus ClubAuth.

Ruft den ClubAuth-Endpoint /api/app-users/?app=kursanmeldung ab und legt
fehlende Django-User in der Kursanmeldungs-Datenbank an (oder aktualisiert sie).
So können Kursleiter als instructor_user hinterlegt werden, bevor sie sich
das erste Mal eingeloggt haben.

Verwendung auf dem Server:
    python manage.py sync_kursleiter
"""

import requests
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Group
from django.conf import settings


class Command(BaseCommand):
    help = "Synchronisiert Kursanmeldungs-User aus ClubAuth"

    def handle(self, *args, **options):
        base_url = getattr(settings, "OIDC_INTERNAL_URL",
                           getattr(settings, "OIDC_BASE_URL", "")).rstrip("/")
        api_key = getattr(settings, "INTERNAL_API_KEY", "")

        if not base_url or not api_key:
            raise CommandError(
                "OIDC_BASE_URL (oder OIDC_INTERNAL_URL) und INTERNAL_API_KEY "
                "müssen in den Settings gesetzt sein."
            )

        url = f"{base_url}/api/app-users/?app=kursanmeldung"
        try:
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise CommandError(f"Fehler beim Abruf von ClubAuth: {e}")

        users_data = resp.json().get("users", [])
        if not users_data:
            self.stdout.write(self.style.WARNING("Keine User von ClubAuth erhalten."))
            return

        kursleitung_group, _ = Group.objects.get_or_create(name="Kursleitung")
        kassierer_group, _   = Group.objects.get_or_create(name="Kassierer")

        created = updated = 0
        for entry in users_data:
            email      = entry.get("email", "").lower().strip()
            first_name = entry.get("first_name", "")
            last_name  = entry.get("last_name", "")
            role       = entry.get("role", "")

            if not email:
                continue

            user, is_new = User.objects.update_or_create(
                username=email,
                defaults={
                    "email":      email,
                    "first_name": first_name,
                    "last_name":  last_name,
                    "is_staff":   True,
                    "is_active":  True,
                },
            )

            # Gruppen synchronisieren
            if role == "kursleitung":
                user.groups.add(kursleitung_group)
                user.groups.remove(kassierer_group)
            elif role == "kassierer":
                user.groups.add(kassierer_group)
                user.groups.remove(kursleitung_group)
            elif role in ("verwaltung", "admin"):
                user.groups.remove(kursleitung_group)
                user.groups.remove(kassierer_group)

            if is_new:
                created += 1
                self.stdout.write(f"  Neu angelegt: {email} ({role})")
            else:
                updated += 1
                self.stdout.write(f"  Aktualisiert: {email} ({role})")

        self.stdout.write(
            self.style.SUCCESS(
                f"Fertig: {created} angelegt, {updated} aktualisiert."
            )
        )
