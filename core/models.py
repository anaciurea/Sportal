from django.conf import settings
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255)

    class Meta:
        unique_together = ("company", "name")

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class SportResource(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="resources")
    name = models.CharField(max_length=120)
    sport_type = models.CharField(max_length=80)
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        unique_together = ("location", "name")

    def __str__(self):
        return f"{self.location.name} / {self.name}"


class EmployeeProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee_profile")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="employees")

    def __str__(self):
        return f"{self.user.username} @ {self.location.name}"


class BookingRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="booking_requests")
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="booking_requests")
    resource = models.ForeignKey(SportResource, on_delete=models.CASCADE, related_name="booking_requests")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.CharField(max_length=255, blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_booking_requests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("date", "start_time")

    def __str__(self):
        return f"{self.resource.name} {self.date} {self.start_time}-{self.end_time} ({self.status})"
