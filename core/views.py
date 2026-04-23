import json
from datetime import datetime

from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.forms import ClientRegistrationForm
from core.models import BookingRequest, SportResource
from core.services.booking_service import confirm_request, create_booking_request


def is_employee(user):
    return hasattr(user, "employee_profile")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("dashboard")
    else:
        form = ClientRegistrationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    if is_employee(request.user):
        pending = BookingRequest.objects.filter(status=BookingRequest.Status.PENDING).select_related(
            "client", "resource", "location"
        )
        return render(request, "core/employee_dashboard.html", {"pending_requests": pending})

    resources = SportResource.objects.select_related("location").all()
    sport_types = (
        SportResource.objects.order_by("sport_type")
        .values_list("sport_type", flat=True)
        .distinct()
    )
    history = BookingRequest.objects.filter(client=request.user).select_related("resource", "location")
    most_visited_sports = [
        {
            "sport": "Tennis",
            "location": "Tenix's Club Galaxy",
            "city": "Bucharest",
            "rating": "4.8",
            "price": "120 RON / hour",
            "image_url": "https://images.unsplash.com/photo-1560012057-4372e14c5085?auto=format&fit=crop&w=1200&q=80",
        },
        {
            "sport": "Football",
            "location": "Lia Manoliu Sports Complex",
            "city": "Bucharest",
            "rating": "4.7",
            "price": "300 RON / hour",
            "image_url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=1200&q=80",
        },
    ]
    return render(
        request,
        "core/client_dashboard.html",
        {
            "resources": resources,
            "sport_types": sport_types,
            "history": history,
            "most_visited_sports": most_visited_sports,
        },
    )


@login_required
@require_GET
def availability(request):
    resource_id = request.GET.get("resource_id")
    date_value = request.GET.get("date")
    if not resource_id or not date_value:
        return HttpResponseBadRequest("Missing parameters.")

    resource = get_object_or_404(SportResource, pk=resource_id)
    try:
        booking_date = datetime.strptime(date_value, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Invalid date.")

    entries = BookingRequest.objects.filter(resource=resource, date=booking_date).exclude(
        status=BookingRequest.Status.REJECTED
    )
    slots = [
        {
            "id": booking.id,
            "start_time": booking.start_time.strftime("%H:%M"),
            "end_time": booking.end_time.strftime("%H:%M"),
            "status": booking.status,
        }
        for booking in entries
    ]
    return JsonResponse({"slots": slots})


@login_required
@require_POST
def create_request_view(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON.")

    required = ["resource_id", "date", "start_time", "end_time"]
    if any(key not in payload for key in required):
        return HttpResponseBadRequest("Missing booking fields.")

    resource = get_object_or_404(SportResource, pk=payload["resource_id"])
    try:
        booking_date = datetime.strptime(payload["date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(payload["start_time"], "%H:%M").time()
        end_time = datetime.strptime(payload["end_time"], "%H:%M").time()
    except ValueError:
        return HttpResponseBadRequest("Invalid date/time values.")

    if start_time >= end_time:
        return HttpResponseBadRequest("Start time must be before end time.")

    try:
        booking = create_booking_request(
            client=request.user,
            resource=resource,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
        )
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=409)

    return JsonResponse({"id": booking.id, "status": booking.status}, status=201)


@login_required
@require_POST
def decide_request_view(request, booking_id):
    if not is_employee(request.user):
        return JsonResponse({"error": "Only employees can decide requests."}, status=403)

    booking = get_object_or_404(BookingRequest, pk=booking_id)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON.")

    action = payload.get("action")
    if action == "confirm":
        try:
            booking = confirm_request(request_obj=booking, employee=request.user)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=409)
        notify_client_booking_decision(booking=booking)
        return JsonResponse({"id": booking.id, "status": booking.status})

    if action == "reject":
        if booking.status != BookingRequest.Status.PENDING:
            return JsonResponse({"error": "The request is no longer pending."}, status=409)
        booking.status = BookingRequest.Status.REJECTED
        booking.rejection_reason = payload.get("reason", "").strip()
        booking.handled_by = request.user
        booking.save(update_fields=["status", "rejection_reason", "handled_by", "updated_at"])
        notify_client_booking_decision(booking=booking)
        return JsonResponse({"id": booking.id, "status": booking.status})

    return HttpResponseBadRequest("Invalid action.")


def notify_client_booking_decision(*, booking: BookingRequest):
    if not booking.client.email:
        return

    status_label = booking.get_status_display().lower()
    subject = f"Sportal - Your booking was {status_label}"
    reason_line = ""
    if booking.status == BookingRequest.Status.REJECTED and booking.rejection_reason:
        reason_line = f"\nReason: {booking.rejection_reason}"

    message = (
        f"Hi, {booking.client.username}!\n\n"
        f"Your booking request for {booking.resource.name} ({booking.location.name}) on {booking.date} "
        f"between {booking.start_time.strftime('%H:%M')} and {booking.end_time.strftime('%H:%M')} "
        f"was {status_label}."
        f"{reason_line}\n\n"
        "Thank you,\nSportal Team"
    )
    send_mail(subject, message, None, [booking.client.email], fail_silently=settings.EMAIL_FAIL_SILENTLY)
