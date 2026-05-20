from datetime import date, time

from django.contrib.auth.models import User
from django.test import TestCase

from core.models import BookingRequest, Company, Location, SportResource
from core.services.booking_service import confirm_request, create_booking_request


class BookingServiceTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(username="client1", password="pass1234")
        self.employee_user = User.objects.create_user(username="employee1", password="pass1234")
        company = Company.objects.create(name="Sportal Co")
        location = Location.objects.create(company=company, name="Arena Nord", address="Str. Test 1")
        self.resource = SportResource.objects.create(
            location=location, name="Teren 1", sport_type="fotbal", price_per_hour=100
        )

    def test_create_request_success(self):
        req = create_booking_request(
            client=self.client_user,
            resource=self.resource,
            booking_date=date(2026, 4, 3),
            start_time=time(18, 0),
            end_time=time(19, 0),
        )
        self.assertEqual(req.status, BookingRequest.Status.PENDING)

    def test_create_request_reject_overlap(self):
        create_booking_request(
            client=self.client_user,
            resource=self.resource,
            booking_date=date(2026, 4, 3),
            start_time=time(18, 0),
            end_time=time(19, 0),
        )
        with self.assertRaises(ValueError):
            create_booking_request(
                client=self.client_user,
                resource=self.resource,
                booking_date=date(2026, 4, 3),
                start_time=time(18, 30),
                end_time=time(19, 30),
            )

    def test_confirm_request_success(self):
        req = create_booking_request(
            client=self.client_user,
            resource=self.resource,
            booking_date=date(2026, 4, 3),
            start_time=time(19, 0),
            end_time=time(20, 0),
        )
        updated = confirm_request(request_obj=req, employee=self.employee_user)
        self.assertEqual(updated.status, BookingRequest.Status.CONFIRMED)
