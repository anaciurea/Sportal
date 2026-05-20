import json
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Avg, Count, Exists, OuterRef
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from core.forms import ClientRegistrationForm
from core.models import BookingRequest, Review, SportResource
from core.services.booking_service import confirm_request, create_booking_request

_SPORT_IMAGES = {
    "fotbal": "https://images.unsplash.com/photo-1553778263-73a83bab9b0c?auto=format&fit=crop&w=800&q=80",
    "tenis": "https://images.unsplash.com/photo-1595435934249-5df7ed86e1c0?auto=format&fit=crop&w=800&q=80",
    "padel": "https://images.unsplash.com/photo-1612872087720-bb876e2e67d1?auto=format&fit=crop&w=800&q=80",
    "basket": "https://images.unsplash.com/photo-1546519638-68e109498ffc?auto=format&fit=crop&w=800&q=80",
    "volei": "https://images.unsplash.com/photo-1592656094267-764a45160876?auto=format&fit=crop&w=800&q=80",
    "handbal": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=800&q=80",
    "badminton": "https://images.unsplash.com/photo-1626224583764-f87db24ac4ea?auto=format&fit=crop&w=800&q=80",
}
_DEFAULT_IMAGE = "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=800&q=80"


def is_employee(user):
    return user.is_staff or hasattr(user, "employee_profile")


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
        confirmed = (
            BookingRequest.objects.filter(status=BookingRequest.Status.CONFIRMED)
            .select_related("client", "resource", "location")
            .order_by("-date", "-start_time")[:30]
        )
        resources = SportResource.objects.select_related("location").order_by("location__name", "name")
        return render(request, "core/employee_dashboard.html", {
            "pending_requests": pending,
            "confirmed_requests": confirmed,
            "resources": resources,
        })

    resources = SportResource.objects.select_related("location").all()
    history = (
        BookingRequest.objects
        .filter(client=request.user)
        .select_related("resource", "location")
        .annotate(has_review=Exists(Review.objects.filter(booking=OuterRef("pk"))))
        .order_by("-date", "-start_time")
    )
    today = date.today()
    resources_with_images = [
        {"resource": r, "image_url": _SPORT_IMAGES.get(r.sport_type, _DEFAULT_IMAGE)}
        for r in resources
    ]
    return render(
        request,
        "core/client_dashboard.html",
        {
            "resources": resources,
            "history": history,
            "resources_with_images": resources_with_images,
            "today": today,
        },
    )


@login_required
def resource_detail(request, resource_id):
    resource = get_object_or_404(SportResource, pk=resource_id)
    image_url = _SPORT_IMAGES.get(resource.sport_type, _DEFAULT_IMAGE)
    return render(request, "core/resource_detail.html", {"resource": resource, "image_url": image_url})


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
        return JsonResponse({"error": "Date invalide."}, status=400)

    required = ["resource_id", "date", "start_time", "end_time"]
    if any(key not in payload for key in required):
        return JsonResponse({"error": "Completează toate câmpurile (dată, oră start, oră sfârșit)."}, status=400)

    if not payload["date"]:
        return JsonResponse({"error": "Selectează o dată."}, status=400)

    resource = get_object_or_404(SportResource, pk=payload["resource_id"])
    try:
        booking_date = datetime.strptime(payload["date"], "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Dată invalidă."}, status=400)

    try:
        start_time = datetime.strptime(payload["start_time"][:5], "%H:%M").time()
        end_time = datetime.strptime(payload["end_time"][:5], "%H:%M").time()
    except ValueError:
        return JsonResponse({"error": "Oră invalidă."}, status=400)

    if start_time >= end_time:
        return JsonResponse({"error": "Ora de start trebuie să fie înainte de ora de sfârșit."}, status=400)

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


@login_required
@require_GET
def calendar_api(request):
    if not is_employee(request.user):
        return JsonResponse({"error": "Forbidden"}, status=403)

    date_value = request.GET.get("date")
    if not date_value:
        return HttpResponseBadRequest("Missing date.")
    try:
        booking_date = datetime.strptime(date_value, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Invalid date.")

    resources = SportResource.objects.select_related("location").order_by("location__name", "name")
    bookings = (
        BookingRequest.objects.filter(date=booking_date)
        .exclude(status=BookingRequest.Status.REJECTED)
        .select_related("client", "resource")
    )

    bookings_by_resource = {}
    for b in bookings:
        bookings_by_resource.setdefault(b.resource_id, []).append({
            "id": b.id,
            "start_time": b.start_time.strftime("%H:%M"),
            "end_time": b.end_time.strftime("%H:%M"),
            "status": b.status,
            "client": b.client.username,
        })

    result = [
        {
            "id": r.id,
            "name": r.name,
            "location": r.location.name,
            "sport_type": r.sport_type,
            "bookings": bookings_by_resource.get(r.id, []),
        }
        for r in resources
    ]
    return JsonResponse({"date": date_value, "resources": result})


@login_required
def stats_view(request):
    if not is_employee(request.user):
        return redirect("dashboard")

    today = date.today()

    # Last 7 days — bookings count per day (non-rejected)
    last_7 = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = (
            BookingRequest.objects
            .filter(date=day)
            .exclude(status=BookingRequest.Status.REJECTED)
            .count()
        )
        last_7.append({"label": day.strftime("%d %b"), "count": count})

    max_count = max((d["count"] for d in last_7), default=0) or 1
    for d in last_7:
        d["pct"] = round(d["count"] / max_count * 100)

    # Status totals all-time
    status_totals_qs = BookingRequest.objects.values("status").annotate(total=Count("id"))
    status_totals = {s["status"]: s["total"] for s in status_totals_qs}

    # This week totals
    week_start = today - timedelta(days=today.weekday())
    week_confirmed = BookingRequest.objects.filter(
        date__gte=week_start, status=BookingRequest.Status.CONFIRMED
    ).count()
    # Per-resource stats
    resource_stats = []
    for r in SportResource.objects.select_related("location").order_by("location__name", "name"):
        confirmed_qs = BookingRequest.objects.filter(resource=r, status=BookingRequest.Status.CONFIRMED)
        total = BookingRequest.objects.filter(resource=r).exclude(status=BookingRequest.Status.REJECTED).count()
        revenue = 0.0
        for b in confirmed_qs:
            hours = (
                datetime.combine(date.min, b.end_time) - datetime.combine(date.min, b.start_time)
            ).seconds / 3600
            revenue += float(r.price_per_hour) * hours
        avg_rating = Review.objects.filter(booking__resource=r).aggregate(avg=Avg("rating"))["avg"]
        resource_stats.append({
            "resource": r,
            "confirmed": confirmed_qs.count(),
            "total": total,
            "revenue": round(revenue, 2),
            "avg_rating": round(avg_rating, 1) if avg_rating else None,
        })

    total_revenue = round(sum(rs["revenue"] for rs in resource_stats), 2)

    return render(request, "core/employee_stats.html", {
        "last_7": last_7,
        "status_totals": status_totals,
        "week_confirmed": week_confirmed,
        "resource_stats": resource_stats,
        "total_revenue": total_revenue,
        "today": today,
    })


@login_required
@require_POST
def submit_review_view(request, booking_id):
    booking = get_object_or_404(BookingRequest, pk=booking_id, client=request.user)

    if booking.status != BookingRequest.Status.CONFIRMED:
        return JsonResponse({"error": "Poți recenza doar rezervări confirmate."}, status=400)
    if booking.date >= date.today():
        return JsonResponse({"error": "Rezervarea nu a trecut încă."}, status=400)
    if Review.objects.filter(booking=booking).exists():
        return JsonResponse({"error": "Ai recenzat deja această rezervare."}, status=400)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Date invalide."}, status=400)

    rating = payload.get("rating")
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return JsonResponse({"error": "Rating invalid (1–5)."}, status=400)

    Review.objects.create(
        booking=booking,
        rating=rating,
        comment=payload.get("comment", "").strip(),
    )
    return JsonResponse({"ok": True})


@require_GET
def resource_reviews_api(request, resource_id):
    resource = get_object_or_404(SportResource, pk=resource_id)
    reviews_qs = (
        Review.objects
        .filter(booking__resource=resource)
        .select_related("booking__client")
        .order_by("-created_at")[:20]
    )
    avg = Review.objects.filter(booking__resource=resource).aggregate(avg=Avg("rating"))["avg"]
    return JsonResponse({
        "avg": round(avg, 1) if avg else None,
        "count": Review.objects.filter(booking__resource=resource).count(),
        "reviews": [
            {
                "rating": r.rating,
                "comment": r.comment,
                "client": r.booking.client.username,
                "date": r.booking.date.strftime("%d %b %Y"),
            }
            for r in reviews_qs
        ],
    })


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
