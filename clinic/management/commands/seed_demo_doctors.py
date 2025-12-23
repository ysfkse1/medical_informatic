from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from clinic.utils import ensure_demo_doctors
from clinic.models import Doctor


class Command(BaseCommand):
    help = "Create or reset demo doctor users with default password."

    def handle(self, *args, **options):
        ensure_demo_doctors()
        User = get_user_model()
        updated = 0
        for doctor in Doctor.objects.select_related("user"):
            user = doctor.user
            if not user:
                continue
            user.set_password("doktor123")
            user.save()
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Demo doktor hesapları hazır. Toplam: {updated}, şifre: doktor123"))
