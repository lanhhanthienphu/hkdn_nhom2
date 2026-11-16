"""First-resolution measurements derived from existing status history."""

from decimal import Decimal

from django.db.models import (
    Avg, Case, CharField, Count, DateTimeField, DurationField,
    ExpressionWrapper, F, OuterRef, Q, Subquery, Value, When,
)

from .models import TicketHistory


def with_first_resolution(queryset):
    """One measurement per ticket; assignment logs are not status transitions.

    A valid event has a known previous status, changes to resolved, and occurs
    no earlier than ticket creation. A corrupt earliest event, or earlier evidence
    of an already resolved ticket, is not replaced by a later resolution.
    """
    histories = TicketHistory.objects.filter(ticket_id=OuterRef('pk'))
    events = histories.filter(
        old_status__in=['new', 'in_progress', 'closed'], new_status='resolved',
    ).order_by('created_at', 'pk')
    evidence = histories.filter(Q(old_status='resolved') | Q(new_status='resolved')).order_by('created_at', 'pk')
    return queryset.annotate(
        _first_resolution_event=Subquery(events.values('created_at')[:1]),
        _first_resolution_evidence=Subquery(evidence.values('created_at')[:1]),
    ).annotate(
        first_resolved_at=Case(
            When(Q(_first_resolution_event__gte=F('created_at')) &
                 Q(_first_resolution_event=F('_first_resolution_evidence')), then=F('_first_resolution_event')),
            default=Value(None), output_field=DateTimeField(),
        ),
    ).annotate(
        first_resolution_duration=ExpressionWrapper(
            F('first_resolved_at') - F('created_at'), output_field=DurationField(),
        ),
    ).annotate(
        first_resolution_state=Case(
            When(first_resolution_duration__isnull=False, then=Value('measured')),
            When(Q(status__in=['resolved', 'closed']) | Q(_first_resolution_evidence__isnull=False), then=Value('missing')),
            default=Value('pending'), output_field=CharField(),
        ),
    )


def format_resolution_duration(duration):
    """Round to the nearest second for the report, including an actual zero."""
    if duration is None:
        return 'Chưa đủ dữ liệu'
    seconds = duration.days * 86400 + duration.seconds + (duration.microseconds >= 500000)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    parts = [f'{value} {label}' for value, label in (
        (days, 'ngày'), (hours, 'giờ'), (minutes, 'phút'), (seconds, 'giây'),
    ) if value]
    return ' '.join(parts) or '0 giây'


def resolution_minutes(duration):
    if duration is None:
        return ''
    seconds = Decimal(duration.days * 86400 + duration.seconds) + Decimal(duration.microseconds) / 1000000
    return f'{seconds / 60:.2f}'


def first_resolution_summary(queryset):
    """Aggregate an annotated, already filtered report queryset."""
    result = queryset.aggregate(
        total=Count('pk'),
        measured=Count('pk', filter=Q(first_resolution_duration__isnull=False)),
        missing=Count('pk', filter=Q(first_resolution_state='missing')),
        average=Avg('first_resolution_duration'),
    )
    result['pending'] = result['total'] - result['measured'] - result['missing']
    result['average_label'] = (format_resolution_duration(result['average'])
                               if result['average'] is not None else 'Chưa có dữ liệu')
    return result


def first_resolution_row(ticket):
    state = ticket.first_resolution_state
    return {
        'ticket': ticket,
        'resolved_at': ticket.first_resolved_at,
        'duration_label': format_resolution_duration(ticket.first_resolution_duration),
        'state': state,
        'state_label': {'measured': 'Đủ dữ liệu', 'pending': 'Chưa giải quyết', 'missing': 'Chưa đủ dữ liệu'}[state],
    }
