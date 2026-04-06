from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from ..models import CalendarEvent
from ..forms import CalendarEventForm
import json


@login_required
def calendar_view(request):
    return render(request, 'calendar.html')


@login_required
def calendar_events_api(request):
    year = request.GET.get('year', timezone.localdate().year)
    month = request.GET.get('month', timezone.localdate().month)
    events = CalendarEvent.objects.filter(
        user=request.user,
        event_date__year=year,
        event_date__month=month,
    )
    data = []
    for e in events:
        data.append({
            'id': e.id,
            'date': e.event_date.strftime('%Y-%m-%d'),
            'title': e.title,
            'event_type': e.event_type,
            'amount': int(e.amount) if e.amount else None,
            'is_processed': e.is_processed,
        })
    return JsonResponse({'events': data})


@login_required
def add_event_view(request):
    initial = {}
    date_param = request.GET.get('date')
    if date_param:
        initial['event_date'] = date_param

    if request.method == 'POST':
        form = CalendarEventForm(request.user, request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user
            event.save()
            return redirect('calendar')
    else:
        form = CalendarEventForm(request.user, initial=initial)
    return render(request, 'calendar_add_event.html', {'form': form})


@login_required
def delete_event_view(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
    if request.method == 'POST':
        event.delete()
    return redirect('calendar')
