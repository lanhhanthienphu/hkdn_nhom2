import datetime
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.db.models import Case, Count, IntegerField, Q, Value, When
from django.db.models.functions import Concat
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST, require_safe

from kb.models import Article

from . import demo_store
from .attachment_services import create_ticket_with_attachment
from .forms import ReplyForm, TicketForm
from .models import Attachment, Comment, Ticket

User = get_user_model()
logger = logging.getLogger(__name__)


def is_admin_user(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(hasattr(user, 'profile') and user.profile.is_admin())


def is_technician_user(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return bool(hasattr(user, 'profile') and user.profile.is_technician())


def get_technicians_queryset():
    tech_role_names = [
        'technician', 'admin', 'it support', 'kỹ thuật viên',
        'kythuatvien', 'support', 'quản trị viên', 'quantri'
    ]
    return User.objects.filter(
        Q(is_superuser=True) |
        Q(profile__role__name__in=tech_role_names)
    ).filter(is_active=True).distinct().select_related('profile').order_by('first_name', 'username')


def get_category_stats(base_qs=None):
    if base_qs is None:
        base_qs = Ticket.objects.all()

    choice_dict = dict(Ticket.CATEGORY_CHOICES)
    counts = {}
    for cat_key, _ in Ticket.CATEGORY_CHOICES:
        counts[cat_key] = 0

    db_counts = base_qs.values('category').annotate(count=Count('id'))
    for item in db_counts:
        cat = item['category']
        counts[cat] = item['count']
        if cat not in choice_dict:
            choice_dict[cat] = cat.capitalize()

    labels = [choice_dict.get(k, k) for k in counts.keys()]
    data = list(counts.values())
    return labels, data


def get_ticket_time_series():
    today = timezone.localdate()

    labels_7d, data_7d = [], []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))
        day_end = timezone.make_aware(datetime.datetime.combine(day, datetime.time.max))
        cnt = Ticket.objects.filter(created_at__range=(day_start, day_end)).count()
        labels_7d.append(day.strftime('%d/%m'))
        data_7d.append(cnt)

    labels_30d, data_30d = [], []
    for i in range(29, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_start = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))
        day_end = timezone.make_aware(datetime.datetime.combine(day, datetime.time.max))
        cnt = Ticket.objects.filter(created_at__range=(day_start, day_end)).count()
        labels_30d.append(day.strftime('%d/%m'))
        data_30d.append(cnt)

    labels_months, data_months = [], []
    for i in range(5, -1, -1):
        m = (today.month - 1 - i) % 12 + 1
        y = today.year + ((today.month - 1 - i) // 12)
        cnt = Ticket.objects.filter(created_at__year=y, created_at__month=m).count()
        labels_months.append(f"T{m:02d}")
        data_months.append(cnt)

    return {
        'days_7': {'labels': labels_7d, 'data': data_7d},
        'days_30': {'labels': labels_30d, 'data': data_30d},
        'months': {'labels': labels_months, 'data': data_months},
    }


@require_GET
@never_cache
def home(request):
    demo_setting = getattr(settings, 'FRONTEND_DEMO_ENABLED', None)
    if demo_setting is True:
        tickets = demo_store.get_tickets(request)
        recent = sorted(tickets, key=lambda t: t['created_at'], reverse=True)[:3]
        return render(request, 'tickets/home.html', {
            'ticket_demo_enabled': True,
            'stats': demo_store.summary(tickets),
            'recent_tickets': [demo_store.present(t) for t in recent],
            'articles': Article.objects.filter(is_published=True).order_by('-updated_at', '-pk')[:3],
        })
    elif demo_setting is False:
        return render(request, 'tickets/home.html', {
            'ticket_demo_enabled': False,
            'stats': {'total': 0, 'new': 0, 'in_progress': 0, 'resolved': 0, 'closed': 0},
            'recent_tickets': [],
            'articles': Article.objects.filter(is_published=True).order_by('-updated_at', '-pk')[:3],
        })

    user = request.user
    if not user.is_authenticated:
        stats = {'total': 0, 'new': 0, 'in_progress': 0, 'resolved': 0, 'closed': 0}
        recent_tickets = []
    else:
        is_tech = hasattr(user, 'profile') and user.profile.is_technician()
        if is_tech or user.is_superuser:
            qs = Ticket.objects.all()
        else:
            qs = Ticket.objects.filter(created_by=user)

        stats = {
            'total': qs.count(),
            'new': qs.filter(status='new').count(),
            'in_progress': qs.filter(status='in_progress').count(),
            'resolved': qs.filter(status='resolved').count(),
            'closed': qs.filter(status='closed').count(),
        }
        recent_tickets = list(qs.order_by('-created_at', '-pk')[:3])

    return render(request, 'tickets/home.html', {
        'ticket_demo_enabled': False,
        'stats': stats,
        'recent_tickets': recent_tickets,
        'articles': Article.objects.filter(is_published=True).order_by('-updated_at', '-pk')[:3],
    })


@require_GET
@never_cache
def ticket_list(request):
    demo_setting = getattr(settings, 'FRONTEND_DEMO_ENABLED', None)
    if demo_setting is False:
        demo_store.require_demo()
    elif demo_setting is True:
        tickets = demo_store.get_tickets(request)
        stats = demo_store.summary(tickets)
        query = request.GET.get('q', '').strip()[:150]
        status = request.GET.get('status', '')
        category = request.GET.get('category', '')
        priority = request.GET.get('priority', '')
        sort = request.GET.get('sort', 'newest')
        if status not in dict(demo_store.STATUSES):
            status = ''
        if category not in dict(demo_store.CATEGORIES):
            category = ''
        if priority not in dict(demo_store.PRIORITIES):
            priority = ''
        if sort not in ('newest', 'oldest', 'priority'):
            sort = 'newest'
        if query:
            tickets = [t for t in tickets if query.casefold() in
                       f"HD-{t['id']} {t['title']} {t['location']} {t.get('reporter', '')}".casefold()]
        if status:
            tickets = [t for t in tickets if t['status'] == status]
        if category:
            tickets = [t for t in tickets if t['category'] == category]
        if priority:
            tickets = [t for t in tickets if t['priority'] == priority]
        if sort == 'priority':
            ranks = {key: index for index, (key, _) in enumerate(demo_store.PRIORITIES)}
            tickets.sort(key=lambda t: (ranks[t['priority']], t['created_at']), reverse=True)
        else:
            tickets.sort(key=lambda t: t['created_at'], reverse=sort == 'newest')
        page = Paginator([demo_store.present(t) for t in tickets], 5).get_page(request.GET.get('page'))
        params = request.GET.copy()
        params.pop('page', None)
        return render(request, 'tickets/list.html', {
            'page_obj': page, 'stats': stats, 'query': query, 'status': status,
            'category': category, 'sort': sort, 'statuses': demo_store.STATUSES,
            'categories': demo_store.CATEGORIES, 'filter_query': params.urlencode(),
            'priority': priority, 'priorities': demo_store.PRIORITIES,
            'has_filters': bool(query or status or category or priority),
            'ticket_demo_enabled': True,
        })

    user = request.user
    is_tech = hasattr(user, 'profile') and user.profile.is_technician()
    if is_tech or user.is_superuser:
        base_qs = Ticket.objects.select_related('created_by', 'assigned_to').all()
    else:
        base_qs = Ticket.objects.select_related('created_by', 'assigned_to').filter(created_by=user)

    stats = {
        'total': base_qs.count(),
        'new': base_qs.filter(status='new').count(),
        'in_progress': base_qs.filter(status='in_progress').count(),
        'resolved': base_qs.filter(status='resolved').count(),
        'closed': base_qs.filter(status='closed').count(),
    }

    query = request.GET.get('q', '').strip()[:150]
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    priority = request.GET.get('priority', '')
    sort = request.GET.get('sort', 'newest')

    qs = base_qs
    if status in dict(Ticket.STATUS_CHOICES):
        qs = qs.filter(status=status)
    else:
        status = ''

    if category in dict(Ticket.CATEGORY_CHOICES):
        qs = qs.filter(category=category)
    else:
        category = ''

    if priority in dict(Ticket.PRIORITY_CHOICES):
        qs = qs.filter(priority=priority)
    else:
        priority = ''

    if query:
        qs = qs.alias(reporter_full_name=Concat(
            'created_by__first_name', Value(' '), 'created_by__last_name',
        ))
        q_filter = (
            Q(title__icontains=query) |
            Q(location__icontains=query) |
            Q(created_by__username__icontains=query) |
            Q(created_by__first_name__icontains=query) |
            Q(created_by__last_name__icontains=query) |
            Q(reporter_full_name__icontains=query)
        )
        raw_id = query[3:] if query.upper().startswith('HD-') else query
        # isdigit() also accepts characters such as ², which int() cannot parse.
        if raw_id.isascii() and raw_id.isdecimal():
            ticket_id = int(raw_id)
            if 0 < ticket_id <= 9223372036854775807:
                q_filter |= Q(pk=ticket_id)
        qs = qs.filter(q_filter)

    if sort == 'oldest':
        qs = qs.order_by('created_at', 'pk')
    elif sort == 'priority':
        qs = qs.annotate(
            priority_rank=Case(
                When(priority='urgent', then=Value(4)),
                When(priority='high', then=Value(3)),
                When(priority='normal', then=Value(2)),
                When(priority='low', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-priority_rank', '-created_at', '-pk')
    else:
        sort = 'newest'
        qs = qs.order_by('-created_at', '-pk')

    page = Paginator(qs, 5).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'tickets/list.html', {
        'page_obj': page,
        'stats': stats,
        'query': query,
        'status': status,
        'category': category,
        'sort': sort,
        'statuses': Ticket.STATUS_CHOICES,
        'categories': Ticket.CATEGORY_CHOICES,
        'filter_query': params.urlencode(),
        'priority': priority,
        'priorities': Ticket.PRIORITY_CHOICES,
        'has_filters': bool(query or status or category or priority),
        'ticket_demo_enabled': False,
    })


@transaction.non_atomic_requests
@require_http_methods(['GET', 'POST'])
@never_cache
def ticket_create(request):
    demo_setting = getattr(settings, 'FRONTEND_DEMO_ENABLED', None)
    if demo_setting is False:
        demo_store.require_demo()
    elif demo_setting is True:
        tickets = demo_store.get_tickets(request)
        initial = {'location': request.GET.get('location', '')[:100]}
        if request.GET.get('category') in dict(demo_store.CATEGORIES):
            initial['category'] = request.GET['category']
        form = TicketForm(request.POST if request.method == 'POST' else None,
                          request.FILES if request.method == 'POST' else None, initial=initial, demo_mode=True)
        if request.method == 'POST' and form.is_valid():
            if len(tickets) >= demo_store.MAX_TICKETS:
                form.add_error(None, 'Phiên xem thử đã đạt 30 ticket. Hãy mở một phiên trình duyệt mới để thử tiếp.')
            else:
                data = form.cleaned_data
                attachment = data.get('attachment')
                now = timezone.now().isoformat()
                ticket = {
                    'id': max((t['id'] for t in tickets), default=1000) + 1,
                    **{key: data[key] for key in ('title', 'description', 'category', 'priority', 'location')},
                    'status': 'new', 'created_at': now, 'replies': [],
                    'reporter': request.user.get_full_name() or request.user.get_username(),
                    'attachment': {'name': attachment.name, 'size': attachment.size} if attachment else None,
                    'events': [{'title': 'Đã tạo ticket xem thử', 'at': now}],
                }
                tickets.append(ticket)
                demo_store.save_tickets(request, tickets)
                messages.success(request, 'Đã tạo ticket xem thử. Yêu cầu này chưa được gửi đến bộ phận kỹ thuật.')
                return redirect('tickets:detail', ticket_id=ticket['id'])
        kb_query = {'network': 'Wi-Fi', 'vpn': 'VPN', 'printer': 'máy in'}.get(form['category'].value(), '')
        return render(request, 'tickets/create.html', {'form': form, 'kb_query': kb_query, 'ticket_demo_enabled': True})

    initial = {'location': request.GET.get('location', '')[:100]}
    if request.GET.get('category') in dict(Ticket.CATEGORY_CHOICES):
        initial['category'] = request.GET['category']

    form = TicketForm(
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None,
        initial=initial,
    )

    if request.method == 'POST' and form.is_valid():
        try:
            ticket = create_ticket_with_attachment(author=request.user, data=form.cleaned_data)
        except ValidationError as exc:
            form.add_error('attachment', exc)
        except (OSError, DatabaseError):
            logger.exception('Could not create ticket for user %s', request.user.pk)
            form.add_error(None, 'Chưa lưu được ticket. Vui lòng thử lại; nếu có tệp đính kèm, hãy chọn lại tệp.')
        else:
            messages.success(request, 'Đã tạo yêu cầu hỗ trợ thành công. Kỹ thuật viên sẽ tiếp nhận và xử lý.')
            return redirect('tickets:detail', ticket_id=ticket.id)

    kb_query = {'network': 'Wi-Fi', 'vpn': 'VPN', 'printer': 'máy in'}.get(form['category'].value(), '')
    return render(request, 'tickets/create.html', {'form': form, 'kb_query': kb_query, 'ticket_demo_enabled': False})


@require_http_methods(['GET', 'POST'])
@never_cache
def ticket_detail(request, ticket_id):
    demo_setting = getattr(settings, 'FRONTEND_DEMO_ENABLED', None)
    if demo_setting is False:
        demo_store.require_demo()
    elif demo_setting is True:
        tickets = demo_store.get_tickets(request)
        ticket = next((t for t in tickets if t['id'] == ticket_id), None)
        if ticket is None:
            return render(request, '404.html', {
                'error_message': 'Ticket này không tồn tại trong phiên của bạn hoặc phiên xem thử trước đó đã kết thúc.',
            }, status=404)
        form = ReplyForm(request.POST if request.method == 'POST' else None)
        if request.method == 'POST' and form.is_valid():
            if ticket['status'] == 'closed':
                form.add_error(None, 'Ticket đã đóng, không thể thêm phản hồi.')
            elif len(ticket['replies']) >= demo_store.MAX_REPLIES:
                form.add_error(None, 'Ticket xem thử đã đạt giới hạn 30 phản hồi.')
            else:
                ticket['replies'].append({'author': 'Bạn', 'role': 'user',
                                          'content': form.cleaned_data['content'],
                                          'at': timezone.now().isoformat()})
                demo_store.save_tickets(request, tickets)
                messages.success(request, 'Đã thêm phản hồi xem thử. Nội dung chưa được gửi đến kỹ thuật viên.')
                return redirect(reverse('tickets:detail', args=[ticket_id]) + '#conversation')
        return render(request, 'tickets/detail.html', {'ticket': demo_store.present(ticket), 'form': form, 'ticket_demo_enabled': True})

    ticket = Ticket.objects.select_related('created_by', 'created_by__profile', 'assigned_to', 'assigned_to__profile').filter(id=ticket_id).first()
    if ticket is None or not ticket.can_view(request.user):
        return render(request, '404.html', {
            'error_message': 'Ticket này không tồn tại hoặc bạn không có quyền xem.',
        }, status=404)

    form = ReplyForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        if ticket.status == 'closed':
            form.add_error(None, 'Ticket đã đóng, không thể thêm phản hồi.')
        else:
            try:
                with transaction.atomic():
                    Comment.objects.create(
                        ticket=ticket,
                        user=request.user,
                        content=form.cleaned_data['content'],
                    )
            except DatabaseError:
                logger.exception('Could not save reply for ticket %s', ticket.pk)
                form.add_error(None, 'Chưa gửi được phản hồi. Nội dung của bạn vẫn được giữ bên dưới; vui lòng thử lại.')
            else:
                messages.success(request, 'Đã thêm phản hồi thành công.')
                return redirect(reverse('tickets:detail', args=[ticket_id]) + '#conversation')

    user_admin = is_admin_user(request.user)
    user_tech = is_technician_user(request.user)
    technicians = get_technicians_queryset() if user_admin else []
    histories = ticket.histories.select_related('changed_by', 'assigned_to').order_by('created_at')

    return render(request, 'tickets/detail.html', {
        'ticket': ticket,
        'form': form,
        'ticket_demo_enabled': False,
        'attachments': ticket.attachments.all(),
        'technicians': technicians,
        'histories': histories,
        'user_is_admin': user_admin,
        'user_is_tech': user_tech,
        'can_assign': user_admin,
        'can_claim': (user_tech and not user_admin and ticket.assigned_to_id != request.user.id),
        'can_change_status': user_admin or user_tech or (ticket.created_by_id == request.user.id),
        'statuses': Ticket.STATUS_CHOICES,
    })


@never_cache
@login_required
@require_safe
def attachment_download(request, ticket_id, attachment_id):
    if getattr(settings, 'FRONTEND_DEMO_ENABLED', None) in (True, False):
        raise Http404('Tệp không có trong chế độ xem thử.')
    attachment = get_object_or_404(
        Attachment.objects.select_related('ticket', 'ticket__created_by', 'ticket__assigned_to'),
        pk=attachment_id, ticket_id=ticket_id,
    )
    if not attachment.ticket.can_view(request.user):
        raise Http404('Không tìm thấy tệp đính kèm.')
    try:
        stream = attachment.file.open('rb')
    except FileNotFoundError:
        raise Http404('Nội dung tệp không còn trên máy chủ.') from None
    response = FileResponse(
        stream, as_attachment=True, filename=attachment.original_name,
        content_type='application/octet-stream',
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@require_POST
@never_cache
def ticket_assign(request, ticket_id):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("Vui lòng đăng nhập.")

    is_admin = is_admin_user(user)
    is_tech = is_technician_user(user)
    if not (is_tech or is_admin):
        return HttpResponseForbidden("Bạn không có quyền phân công sự cố.")

    ticket = get_object_or_404(Ticket, id=ticket_id)
    tech_id = request.POST.get('technician_id')
    note = request.POST.get('note', '').strip()

    try:
        tech_id = int(tech_id)
        if tech_id <= 0 or tech_id > 9223372036854775807:
            raise ValueError
    except (TypeError, ValueError):
        raise Http404('Không tìm thấy kỹ thuật viên.')

    tech = get_object_or_404(User, id=tech_id)

    # Requirement 2.2: Không cho phép kỹ thuật viên tự ý phân công Ticket cho người khác nếu không có quyền Admin.
    if is_tech and not is_admin and tech.id != user.id:
        return HttpResponseForbidden("Kỹ thuật viên không có quyền phân công ticket cho người khác.")
    try:
        changed = ticket.assign_technician(tech, by=user, note=note)
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    else:
        if changed:
            messages.success(request, f"Đã phân công ticket cho kỹ thuật viên {tech.get_full_name() or tech.username}.")
        else:
            messages.info(request, 'Ticket đã được phân công cho người này.')

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('tickets:detail', ticket_id=ticket.id)


@require_POST
@never_cache
def ticket_change_status(request, ticket_id):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("Vui lòng đăng nhập.")

    ticket = get_object_or_404(Ticket, id=ticket_id)
    is_admin = is_admin_user(user)
    is_tech = is_technician_user(user)
    is_creator = ticket.created_by_id == user.id

    new_status = request.POST.get('status', '').strip()
    if new_status == 'open':
        new_status = 'new'
    if new_status not in dict(Ticket.STATUS_CHOICES):
        return HttpResponseForbidden("Trạng thái không hợp lệ.")

    if not (is_admin or is_tech or (is_creator and new_status == 'closed')):
        return HttpResponseForbidden("Bạn không có quyền thay đổi trạng thái ticket này.")

    note = request.POST.get('note', '').strip()
    if ticket.change_status(new_status, by=user, note=note):
        messages.success(request, f"Đã cập nhật trạng thái thành {ticket.status_label}.")
    else:
        messages.info(request, 'Trạng thái ticket không thay đổi.')

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('tickets:detail', ticket_id=ticket.id)


@login_required
@never_cache
def dashboard_dispatcher(request):
    user = request.user
    if is_admin_user(user):
        return redirect('tickets:admin_dashboard')
    elif is_technician_user(user):
        return redirect('tickets:technician_dashboard')
    return redirect('tickets:home')


@login_required
@never_cache
def admin_dashboard(request):
    user = request.user
    if not is_admin_user(user):
        return HttpResponseForbidden("Bạn không có quyền truy cập Dashboard Quản trị viên.")

    base_qs = Ticket.objects.select_related('created_by', 'assigned_to').all()

    # 1. Thống kê tổng quan thẻ cards
    stats = {
        'total': base_qs.count(),
        'open': base_qs.filter(status='new').count(),
        'in_progress': base_qs.filter(status='in_progress').count(),
        'resolved': base_qs.filter(status='resolved').count(),
        'closed': base_qs.filter(status='closed').count(),
    }

    # Thống kê theo mức độ ưu tiên
    priority_stats = {
        'urgent': base_qs.filter(priority='urgent').count(),
        'high': base_qs.filter(priority='high').count(),
        'normal': base_qs.filter(priority='normal').count(),
        'low': base_qs.filter(priority='low').count(),
    }

    # Thống kê theo danh mục
    category_labels, category_data = get_category_stats(base_qs)

    # Time series cho biểu đồ xu hướng
    time_series = get_ticket_time_series()

    # Dữ liệu chuẩn bị cho 4 Chart.js
    chart_data = {
        'status': {
            'labels': ['Chờ xử lý (Open)', 'Đang xử lý (In Progress)', 'Đã giải quyết (Resolved)', 'Đã đóng (Closed)'],
            'data': [stats['open'], stats['in_progress'], stats['resolved'], stats['closed']],
            'colors': ['#f59e0b', '#2563eb', '#10b981', '#64748b'],
        },
        'priority': {
            'labels': ['Thấp (Low)', 'Bình thường (Normal)', 'Cao (High)', 'Khẩn cấp (Critical)'],
            'data': [priority_stats['low'], priority_stats['normal'], priority_stats['high'], priority_stats['urgent']],
            'colors': ['#10b981', '#0284c7', '#f97316', '#ef4444'],
        },
        'category': {
            'labels': category_labels,
            'data': category_data,
            'colors': ['#2563eb', '#8b5cf6', '#0d9488', '#ea580c', '#6366f1', '#ec4899'],
        },
        'time_series': time_series,
    }

    # 2. Bộ lọc và danh sách Ticket mới nhất
    qs = base_qs
    query = request.GET.get('q', '').strip()[:150]
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    technician_id = request.GET.get('technician', '').strip()
    date_filter = request.GET.get('date_range', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    sort = request.GET.get('sort', 'newest')

    if status in dict(Ticket.STATUS_CHOICES):
        qs = qs.filter(status=status)
    elif status == 'open':
        qs = qs.filter(status='new')

    if priority in dict(Ticket.PRIORITY_CHOICES):
        qs = qs.filter(priority=priority)

    if technician_id == 'unassigned':
        qs = qs.filter(assigned_to__isnull=True)
    elif technician_id:
        try:
            t_id = int(technician_id)
            qs = qs.filter(assigned_to_id=t_id)
        except (ValueError, TypeError):
            pass

    # Lọc theo ngày tạo
    today = timezone.localdate()
    if date_filter == 'today':
        qs = qs.filter(created_at__date=today)
    elif date_filter == '7days':
        qs = qs.filter(created_at__gte=timezone.now() - datetime.timedelta(days=7))
    elif date_filter == '30days':
        qs = qs.filter(created_at__gte=timezone.now() - datetime.timedelta(days=30))
    elif date_filter == 'month':
        qs = qs.filter(created_at__year=today.year, created_at__month=today.month)
    elif date_from or date_to:
        if date_from:
            try:
                df = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
                qs = qs.filter(created_at__date__gte=df)
            except ValueError:
                pass
        if date_to:
            try:
                dt = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
                qs = qs.filter(created_at__date__lte=dt)
            except ValueError:
                pass

    if query:
        qs = qs.alias(reporter_full_name=Concat(
            'created_by__first_name', Value(' '), 'created_by__last_name',
        ))
        q_filter = (
            Q(title__icontains=query) |
            Q(location__icontains=query) |
            Q(created_by__username__icontains=query) |
            Q(created_by__first_name__icontains=query) |
            Q(created_by__last_name__icontains=query) |
            Q(reporter_full_name__icontains=query)
        )
        raw_id = query[3:] if query.upper().startswith('HD-') else query
        if raw_id.isascii() and raw_id.isdecimal():
            ticket_id = int(raw_id)
            if 0 < ticket_id <= 9223372036854775807:
                q_filter |= Q(pk=ticket_id)
        qs = qs.filter(q_filter)

    if sort == 'oldest':
        qs = qs.order_by('created_at', 'pk')
    elif sort == 'priority':
        qs = qs.annotate(
            priority_rank=Case(
                When(priority='urgent', then=Value(4)),
                When(priority='high', then=Value(3)),
                When(priority='normal', then=Value(2)),
                When(priority='low', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-priority_rank', '-created_at', '-pk')
    else:
        sort = 'newest'
        qs = qs.order_by('-created_at', '-pk')

    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)

    technicians = get_technicians_queryset()

    return render(request, 'tickets/admin_dashboard.html', {
        'page_obj': page,
        'stats': stats,
        'priority_stats': priority_stats,
        'chart_data_json': json.dumps(chart_data),
        'chart_data': chart_data,
        'query': query,
        'status': status,
        'priority': priority,
        'technician_id': technician_id,
        'date_filter': date_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort': sort,
        'statuses': Ticket.STATUS_CHOICES,
        'priorities': Ticket.PRIORITY_CHOICES,
        'technicians': technicians,
        'filter_query': params.urlencode(),
        'has_filters': bool(query or status or priority or technician_id or date_filter or date_from or date_to),
    })


@login_required
@never_cache
def technician_dashboard(request):
    user = request.user
    if not is_technician_user(user):
        return HttpResponseForbidden("Bạn không có quyền truy cập Dashboard Kỹ thuật viên.")

    base_qs = Ticket.objects.select_related('created_by', 'assigned_to').filter(assigned_to=user)

    stats = {
        'total': base_qs.count(),
        'open': base_qs.filter(status='new').count(),
        'in_progress': base_qs.filter(status='in_progress').count(),
        'resolved': base_qs.filter(status='resolved').count(),
        'closed': base_qs.filter(status='closed').count(),
    }

    qs = base_qs
    query = request.GET.get('q', '').strip()[:150]
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    date_filter = request.GET.get('date_range', '').strip()
    sort = request.GET.get('sort', 'newest')

    if status in dict(Ticket.STATUS_CHOICES):
        qs = qs.filter(status=status)
    elif status == 'open':
        qs = qs.filter(status='new')

    if priority in dict(Ticket.PRIORITY_CHOICES):
        qs = qs.filter(priority=priority)

    today = timezone.localdate()
    if date_filter == 'today':
        qs = qs.filter(created_at__date=today)
    elif date_filter == '7days':
        qs = qs.filter(created_at__gte=timezone.now() - datetime.timedelta(days=7))
    elif date_filter == '30days':
        qs = qs.filter(created_at__gte=timezone.now() - datetime.timedelta(days=30))

    if query:
        qs = qs.alias(reporter_full_name=Concat(
            'created_by__first_name', Value(' '), 'created_by__last_name',
        ))
        q_filter = (
            Q(title__icontains=query) |
            Q(location__icontains=query) |
            Q(created_by__username__icontains=query) |
            Q(reporter_full_name__icontains=query)
        )
        raw_id = query[3:] if query.upper().startswith('HD-') else query
        if raw_id.isascii() and raw_id.isdecimal():
            ticket_id = int(raw_id)
            if 0 < ticket_id <= 9223372036854775807:
                q_filter |= Q(pk=ticket_id)
        qs = qs.filter(q_filter)

    if sort == 'oldest':
        qs = qs.order_by('created_at', 'pk')
    elif sort == 'priority':
        qs = qs.annotate(
            priority_rank=Case(
                When(priority='urgent', then=Value(4)),
                When(priority='high', then=Value(3)),
                When(priority='normal', then=Value(2)),
                When(priority='low', then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-priority_rank', '-created_at', '-pk')
    else:
        sort = 'newest'
        qs = qs.order_by('-created_at', '-pk')

    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'tickets/technician_dashboard.html', {
        'page_obj': page,
        'stats': stats,
        'query': query,
        'status': status,
        'priority': priority,
        'date_filter': date_filter,
        'sort': sort,
        'statuses': Ticket.STATUS_CHOICES,
        'priorities': Ticket.PRIORITY_CHOICES,
        'filter_query': params.urlencode(),
        'has_filters': bool(query or status or priority or date_filter),
    })


@login_required
@never_cache
def reports_view(request):
    user = request.user
    if not (is_admin_user(user) or is_technician_user(user)):
        return HttpResponseForbidden("Bạn không có quyền truy cập trang báo cáo thống kê.")

    base_qs = Ticket.objects.select_related('created_by', 'assigned_to').all()

    stats = {
        'total': base_qs.count(),
        'open': base_qs.filter(status='new').count(),
        'in_progress': base_qs.filter(status='in_progress').count(),
        'resolved': base_qs.filter(status='resolved').count(),
        'closed': base_qs.filter(status='closed').count(),
    }

    priority_stats = {
        'urgent': base_qs.filter(priority='urgent').count(),
        'high': base_qs.filter(priority='high').count(),
        'normal': base_qs.filter(priority='normal').count(),
        'low': base_qs.filter(priority='low').count(),
    }

    category_labels, category_data = get_category_stats(base_qs)
    time_series = get_ticket_time_series()

    chart_data = {
        'status': {
            'labels': ['Chờ xử lý (Open)', 'Đang xử lý (In Progress)', 'Đã giải quyết (Resolved)', 'Đã đóng (Closed)'],
            'data': [stats['open'], stats['in_progress'], stats['resolved'], stats['closed']],
            'colors': ['#f59e0b', '#2563eb', '#10b981', '#64748b'],
        },
        'priority': {
            'labels': ['Thấp (Low)', 'Bình thường (Normal)', 'Cao (High)', 'Khẩn cấp (Critical)'],
            'data': [priority_stats['low'], priority_stats['normal'], priority_stats['high'], priority_stats['urgent']],
            'colors': ['#10b981', '#0284c7', '#f97316', '#ef4444'],
        },
        'category': {
            'labels': category_labels,
            'data': category_data,
            'colors': ['#2563eb', '#8b5cf6', '#0d9488', '#ea580c', '#6366f1', '#ec4899'],
        },
        'time_series': time_series,
    }

    tech_stats = []
    technicians = get_technicians_queryset()
    for tech in technicians:
        assigned_cnt = Ticket.objects.filter(assigned_to=tech).count()
        resolved_cnt = Ticket.objects.filter(assigned_to=tech, status__in=['resolved', 'closed']).count()
        in_progress_cnt = Ticket.objects.filter(assigned_to=tech, status='in_progress').count()
        tech_stats.append({
            'tech': tech,
            'total': assigned_cnt,
            'resolved': resolved_cnt,
            'in_progress': in_progress_cnt,
        })
    tech_stats.sort(key=lambda x: x['resolved'], reverse=True)

    return render(request, 'tickets/reports.html', {
        'stats': stats,
        'priority_stats': priority_stats,
        'chart_data_json': json.dumps(chart_data),
        'chart_data': chart_data,
        'tech_stats': tech_stats,
    })
