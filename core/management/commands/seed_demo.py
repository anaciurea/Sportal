from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Company, EmployeeProfile, Location, SportResource


class Command(BaseCommand):
    help = "Populate demo data for Sportal MVP."

    def handle(self, *args, **options):
        user_model = get_user_model()

        admin_user, admin_created = user_model.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": "admin@sportal.local"},
        )
        if admin_created:
            admin_user.set_password("admin1234")
            admin_user.save()
        elif not admin_user.email:
            admin_user.email = "admin@sportal.local"
            admin_user.save(update_fields=["email"])

        client_user, client_created = user_model.objects.get_or_create(
            username="client_demo", defaults={"email": "client_demo@sportal.local"}
        )
        if client_created:
            client_user.set_password("client1234")
            client_user.save()
        elif not client_user.email:
            client_user.email = "client_demo@sportal.local"
            client_user.save(update_fields=["email"])

        employee_user, employee_created = user_model.objects.get_or_create(
            username="employee_demo", defaults={"email": "employee_demo@sportal.local"}
        )
        if employee_created:
            employee_user.set_password("employee1234")
            employee_user.save()
        elif not employee_user.email:
            employee_user.email = "employee_demo@sportal.local"
            employee_user.save(update_fields=["email"])

        ana_user, ana_created = user_model.objects.get_or_create(
            username="ana_ciurea", defaults={"email": "anaciurea644@gmail.com"}
        )
        if ana_created:
            ana_user.set_password("ana1234")
            ana_user.save()
        elif ana_user.email != "anaciurea644@gmail.com":
            ana_user.email = "anaciurea644@gmail.com"
            ana_user.save(update_fields=["email"])

        company, _ = Company.objects.get_or_create(name="Sportal Demo Company")
        locations = [
            ("Arena Centrala", "Bd. Sportului 10"),
            ("Complex Padel Nord", "Str. Nordului 22"),
            ("Sala Polivalenta Sud", "Calea Sudului 8"),
            ("Parc Sportiv Est", "Str. Stadionului 14"),
        ]
        location_by_name = {}
        for location_name, address in locations:
            location_obj, _ = Location.objects.get_or_create(
                company=company,
                name=location_name,
                defaults={"address": address},
            )
            location_by_name[location_name] = location_obj

        resources = [
            ("Arena Centrala", "Teren Fotbal 1", "fotbal", 150),
            ("Arena Centrala", "Teren Tenis 1", "tenis", 120),
            ("Complex Padel Nord", "Teren Padel 1", "padel", 170),
            ("Complex Padel Nord", "Teren Padel 2", "padel", 180),
            ("Sala Polivalenta Sud", "Teren Basket 1", "basket", 140),
            ("Sala Polivalenta Sud", "Teren Volei 1", "volei", 130),
            ("Parc Sportiv Est", "Teren Handbal 1", "handbal", 135),
            ("Parc Sportiv Est", "Teren Badminton 1", "badminton", 110),
        ]
        for location_name, resource_name, sport_type, price_per_hour in resources:
            SportResource.objects.get_or_create(
                location=location_by_name[location_name],
                name=resource_name,
                defaults={"sport_type": sport_type, "price_per_hour": price_per_hour},
            )

        EmployeeProfile.objects.get_or_create(
            user=employee_user, defaults={"location": location_by_name["Arena Centrala"]}
        )

        self.stdout.write(self.style.SUCCESS("Demo seed completed."))
        self.stdout.write("Users:")
        self.stdout.write("  admin / admin1234")
        self.stdout.write("  client_demo / client1234")
        self.stdout.write("  employee_demo / employee1234")
        self.stdout.write("  anaciurea644@gmail.com / ana1234")
