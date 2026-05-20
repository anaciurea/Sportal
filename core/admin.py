from django.contrib import admin
from core.models import BookingRequest, Company, EmployeeProfile, Location, SportResource


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", "address")
    list_filter = ("company",)
    search_fields = ("name", "address")


@admin.register(SportResource)
class SportResourceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sport_type", "location", "price_per_hour")
    list_filter = ("sport_type", "location")
    search_fields = ("name", "sport_type")


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "location")
    list_filter = ("location",)


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "location", "resource", "date", "start_time", "end_time", "status")
    list_filter = ("status", "location", "date")
    search_fields = ("client__username", "resource__name")
