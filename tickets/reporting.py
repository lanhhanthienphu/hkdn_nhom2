"""Validated filters and CSV output shared by the report page and download."""

import csv
import datetime
import unicodedata
from urllib.parse import urlencode

from django import forms
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from .models import Ticket


def _day_boundary(day, *, end=False):
    clock = datetime.time.max if end else datetime.time.min
    return timezone.make_aware(datetime.datetime.combine(day, clock))


class ReportFilterForm(forms.Form):
    date_from = forms.DateField(
        label='Từ ngày', required=False, input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
    )
    date_to = forms.DateField(
        label='Đến ngày', required=False, input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'class': 'form-control'}),
    )
    category = forms.ChoiceField(
        label='Nhóm sự cố', required=False,
        choices=[('', 'Tất cả nhóm')] + Ticket.CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    technician = forms.ChoiceField(
        label='Người phụ trách', required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        label='Trạng thái', required=False,
        choices=[('', 'Tất cả trạng thái')] + Ticket.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    priority = forms.ChoiceField(
        label='Độ ưu tiên', required=False,
        choices=[('', 'Tất cả mức ưu tiên')] + Ticket.PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    def __init__(self, *args, technicians, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['technician'].choices = [('', 'Tất cả người phụ trách'), ('unassigned', 'Chưa phân công')] + [
            (str(tech.pk), (tech.get_full_name() or tech.get_username()) + ('' if tech.is_active else ' (đã vô hiệu hóa)'))
            for tech in technicians
        ]
        for field in self.fields.values():
            field.error_messages.update({
                'invalid': 'Ngày không hợp lệ. Vui lòng dùng định dạng năm-tháng-ngày.',
                'invalid_choice': 'Lựa chọn không hợp lệ. Vui lòng chọn lại.',
            })

    def clean(self):
        data = super().clean()
        start, end = data.get('date_from'), data.get('date_to')
        if start and end and start > end:
            raise forms.ValidationError('Từ ngày phải nhỏ hơn hoặc bằng Đến ngày.')
        # Reject dates which cannot be represented in UTC for the configured zone.
        for name, day, is_end in [('date_from', start, False), ('date_to', end, True)]:
            if day:
                try:
                    _day_boundary(day, end=is_end).astimezone(datetime.timezone.utc)
                except (ValueError, OverflowError):
                    self.add_error(name, 'Ngày nằm ngoài phạm vi hỗ trợ của múi giờ hệ thống.')
        return data

    def filter_queryset(self, queryset):
        if not self.is_valid():
            raise ValueError('Validate the report filters before querying tickets.')
        data = self.cleaned_data
        if data['date_from']:
            queryset = queryset.filter(created_at__gte=_day_boundary(data['date_from']))
        if data['date_to']:
            queryset = queryset.filter(created_at__lte=_day_boundary(data['date_to'], end=True))
        for name in ('category', 'status', 'priority'):
            if data[name]:
                queryset = queryset.filter(**{name: data[name]})
        if data['technician'] == 'unassigned':
            queryset = queryset.filter(assigned_to__isnull=True)
        elif data['technician']:
            queryset = queryset.filter(assigned_to_id=int(data['technician']))
        return queryset

    def query_string(self):
        if not self.is_valid():
            return ''
        return urlencode([
            (name, value.isoformat() if isinstance(value, datetime.date) else value)
            for name in self.fields if (value := self.cleaned_data.get(name))
        ])


def report_technician_stats(queryset, technicians, selected=''):
    counts = {
        row['assigned_to_id']: row
        for row in queryset.order_by().values('assigned_to_id').annotate(
            total=Count('pk'),
            resolved=Count('pk', filter=Q(status__in=['resolved', 'closed'])),
            in_progress=Count('pk', filter=Q(status='in_progress')),
        )
    }
    rows = []
    for tech in technicians:
        if selected == 'unassigned' or (selected and selected != str(tech.pk)):
            continue
        row = counts.get(tech.pk, {})
        rows.append({'tech': tech, **{key: row.get(key, 0) for key in ('total', 'resolved', 'in_progress')}})
    return sorted(rows, key=lambda row: (-row['resolved'], row['tech'].get_username(), row['tech'].pk))


def report_time_series(queryset, *, anchor=None):
    """Aggregate the filtered set in two queries, relative to the selected end day."""
    anchor = anchor or timezone.localdate()
    first_day = max(datetime.date.min + datetime.timedelta(days=29), anchor) - datetime.timedelta(days=29)
    days = [first_day + datetime.timedelta(days=i) for i in range((anchor - first_day).days + 1)]
    zone = timezone.get_current_timezone()
    daily = {
        row['day']: row['total'] for row in queryset.filter(
            created_at__gte=_day_boundary(first_day), created_at__lte=_day_boundary(anchor, end=True),
        ).order_by().annotate(day=TruncDate('created_at', tzinfo=zone)).values('day').annotate(total=Count('pk'))
    }
    month_index = (anchor.year - 1) * 12 + anchor.month - 1
    months = [datetime.date(index // 12 + 1, index % 12 + 1, 1)
              for index in range(max(0, month_index - 5), month_index + 1)]
    monthly = {
        (row['month'].year, row['month'].month): row['total'] for row in queryset.filter(
            created_at__gte=_day_boundary(months[0]), created_at__lte=_day_boundary(anchor, end=True),
        ).order_by().annotate(month=TruncMonth('created_at', tzinfo=zone)).values('month').annotate(total=Count('pk'))
    }
    return {
        'days_7': {'labels': [day.strftime('%d/%m') for day in days[-7:]],
                   'data': [daily.get(day, 0) for day in days[-7:]]},
        'days_30': {'labels': [day.strftime('%d/%m') for day in days],
                    'data': [daily.get(day, 0) for day in days]},
        'months': {'labels': [day.strftime('%m/%Y') for day in months],
                   'data': [monthly.get((day.year, day.month), 0) for day in months]},
    }


class _CsvBuffer:
    def write(self, value):
        return value


def _csv_text(value):
    text = str(value) if value is not None else ''
    # CSV is intended for viewing in Excel. Keep quotes/line breaks in one cell;
    # prefix potential formulas with a tab inside that quoted cell (OWASP).
    probe = unicodedata.normalize('NFKC', text).lstrip(' \t\r\n\ufeff')
    return '\t' + text if probe.startswith(('=', '+', '-', '@')) else text


def report_csv_rows(queryset, *, zone=None):
    zone = zone or timezone.get_current_timezone()
    writer = csv.writer(_CsvBuffer(), quoting=csv.QUOTE_ALL)
    yield '\ufeff'  # Excel recognizes Vietnamese text when opening UTF-8 with BOM.
    yield writer.writerow([
        'Mã ticket', 'Tiêu đề', 'Nhóm sự cố', 'Độ ưu tiên', 'Trạng thái',
        'Vị trí', 'Người gửi', 'Người phụ trách', 'Ngày tạo (ISO 8601)',
    ])
    for ticket in queryset.order_by('-created_at', '-pk').iterator(chunk_size=1000):
        yield writer.writerow([_csv_text(value) for value in (
            ticket.code, ticket.title, ticket.category_label, ticket.priority_label,
            ticket.status_label, ticket.location, ticket.reporter, ticket.assignee_name,
            timezone.localtime(ticket.created_at, zone).isoformat(timespec='seconds'),
        )])
