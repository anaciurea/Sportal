from datetime import time

from django.db import transaction

from core.models import BookingRequest, SportResource


def has_overlap(resource: SportResource, booking_date, start_time: time, end_time: time) -> bool:
    overlapping = BookingRequest.objects.filter(
        resource=resource,
        date=booking_date,
        status__in=[BookingRequest.Status.PENDING, BookingRequest.Status.CONFIRMED],
        start_time__lt=end_time,
        end_time__gt=start_time,
    )
    return overlapping.exists()


@transaction.atomic
def create_booking_request(*, client, resource: SportResource, booking_date, start_time: time, end_time: time):
    resource = SportResource.objects.select_for_update().get(pk=resource.pk)
    if has_overlap(resource, booking_date, start_time, end_time):
        raise ValueError("Interval indisponibil.")
    return BookingRequest.objects.create(
        client=client,
        location=resource.location,
        resource=resource,
        date=booking_date,
        start_time=start_time,
        end_time=end_time,
        status=BookingRequest.Status.PENDING,
    )


@transaction.atomic
def confirm_request(*, request_obj: BookingRequest, employee):
    request_obj = BookingRequest.objects.select_for_update().select_related("resource").get(pk=request_obj.pk)
    if request_obj.status != BookingRequest.Status.PENDING:
        raise ValueError("Cererea nu mai este in asteptare.")

    conflict = BookingRequest.objects.filter(
        resource=request_obj.resource,
        date=request_obj.date,
        status=BookingRequest.Status.CONFIRMED,
        start_time__lt=request_obj.end_time,
        end_time__gt=request_obj.start_time,
    ).exclude(pk=request_obj.pk)

    if conflict.exists():
        raise ValueError("Nu se poate confirma: interval deja ocupat.")

    request_obj.status = BookingRequest.Status.CONFIRMED
    request_obj.handled_by = employee
    request_obj.rejection_reason = ""
    request_obj.save(update_fields=["status", "handled_by", "rejection_reason", "updated_at"])
    return request_obj
