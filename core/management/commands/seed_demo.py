from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import BookingRequest, Company, EmployeeProfile, Location, SportResource


class Command(BaseCommand):
    help = "Populate demo data for Sportal MVP."

    def handle(self, *args, **options):
        user_model = get_user_model()

        # ── users ──────────────────────────────────────────────────────────
        admin_user, created = user_model.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "email": "admin@sportal.local"},
        )
        if created:
            admin_user.set_password("admin1234")
            admin_user.save()

        client_user, created = user_model.objects.get_or_create(
            username="client_demo", defaults={"email": "client_demo@sportal.local"}
        )
        if created:
            client_user.set_password("client1234")
            client_user.save()

        employee_user, created = user_model.objects.get_or_create(
            username="employee_demo", defaults={"email": "employee_demo@sportal.local"}
        )
        if created:
            employee_user.set_password("employee1234")
            employee_user.save()

        ana_user, created = user_model.objects.get_or_create(
            username="ana_ciurea", defaults={"email": "anaciurea644@gmail.com"}
        )
        if created:
            ana_user.set_password("ana1234")
            ana_user.save()

        # ── reset sport data (keep users & bookings untouched if resources unchanged) ──
        BookingRequest.objects.all().delete()
        SportResource.objects.all().delete()
        Location.objects.all().delete()
        Company.objects.all().delete()
        EmployeeProfile.objects.all().delete()

        # ── venues: one court per sport ────────────────────────────────────
        # (company, location_name, address, court_name, sport_type, price)
        venues = [
            ("Arena Națională",           "Bd. Basarabia 37-39, București",          "Arena Națională",        "fotbal",   300),
            ("BNR Arenas",                "Bd. Pierre de Coubertin 3-5, București",  "BNR Arenas",             "tenis",    120),
            ("Padel Arena București",     "Str. Erou Iancu Nicolae 128, Voluntari",  "Padel Arena București",  "padel",    170),
            ("Sala Dinamo",               "Str. Ștefan cel Mare 9, București",       "Sala Dinamo",            "basket",   250),
            ("Sala Polivalentă",          "Str. Maior Coravu 6, București",          "Sala Polivalentă",       "volei",    200),
            ("Arena CSM București",       "Bd. Lacul Tei 124, București",            "Arena CSM București",    "handbal",  180),
            ("Complexul Lia Manoliu",     "Bd. Basarabia 37-39, București",          "Complexul Lia Manoliu",  "badminton",110),
            ("Stadionul Giulești",        "Calea Giulești 18, București",            "Stadionul Giulești",     "fotbal",   280),
            ("World Royal Padel",         "Str. Biharia 67-77, București",           "World Royal Padel",      "padel",    160),
        ]

        first_location = None
        for loc_name, address, court_name, sport_type, price in venues:
            company, _ = Company.objects.get_or_create(name=loc_name)
            location, _ = Location.objects.get_or_create(
                company=company, name=loc_name, defaults={"address": address}
            )
            SportResource.objects.create(
                location=location, name=court_name, sport_type=sport_type, price_per_hour=price
            )
            if first_location is None:
                first_location = location

        EmployeeProfile.objects.create(user=employee_user, location=first_location)

        # ── historical & upcoming bookings ────────────────────────────────
        today = date.today()
        resources = {r.sport_type: r for r in SportResource.objects.select_related("location").all()}

        def book(client, sport, days_offset, start_h, end_h, status, handled=None):
            r = resources.get(sport)
            if not r:
                return
            BookingRequest.objects.create(
                client=client,
                location=r.location,
                resource=r,
                date=today + timedelta(days=days_offset),
                start_time=time(start_h, 0),
                end_time=time(end_h, 0),
                status=status,
                handled_by=handled,
            )

        S = BookingRequest.Status
        # trecut – confirmate pentru istoric
        book(client_user, "fotbal",    -7, 10, 12, S.CONFIRMED, employee_user)
        book(client_user, "tenis",     -5, 14, 15, S.CONFIRMED, employee_user)
        book(ana_user,    "padel",     -3, 16, 17, S.CONFIRMED, employee_user)
        book(client_user, "basket",    -2, 18, 20, S.CONFIRMED, employee_user)
        book(ana_user,    "volei",     -1, 10, 11, S.CONFIRMED, employee_user)
        book(client_user, "badminton", -1, 14, 15, S.CONFIRMED, employee_user)
        # trecut – respinse
        book(ana_user,    "handbal",   -4, 20, 22, S.REJECTED,  employee_user)
        book(client_user, "volei",     -6, 22, 23, S.REJECTED,  employee_user)
        # azi – pending
        book(client_user, "fotbal",     0, 10, 12, S.PENDING)
        book(ana_user,    "tenis",      0, 14, 16, S.PENDING)
        book(client_user, "padel",      0, 18, 19, S.PENDING)
        # maine – pending
        book(ana_user,    "basket",     1, 11, 13, S.PENDING)
        book(client_user, "handbal",    1, 16, 17, S.PENDING)
        book(ana_user,    "badminton",  1, 10, 11, S.PENDING)
        # poimaine – pending
        book(client_user, "volei",      2, 14, 15, S.PENDING)
        book(ana_user,    "fotbal",     2, 17, 19, S.PENDING)
        # confirmate viitoare
        book(client_user, "tenis",      3, 10, 11, S.CONFIRMED, employee_user)
        book(ana_user,    "padel",      4, 15, 16, S.CONFIRMED, employee_user)

        self.stdout.write(self.style.SUCCESS("Demo seed completed."))
        self.stdout.write("Users:")
        self.stdout.write("  admin / admin1234")
        self.stdout.write("  client_demo / client1234")
        self.stdout.write("  employee_demo / employee1234")
        self.stdout.write("  ana_ciurea / ana1234")
