from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from . import demo_store
from .forms import ReplyForm, TicketForm


@require_GET
def home(request):
    return render(request, 'tickets/home.html')


@require_GET
def ticket_list(request):
    tickets = demo_store.get_tickets(request)
    stats = {
        'total': len(tickets),
        'new': sum(t['status'] == 'new' for t in tickets),
        'active': sum(t['status'] == 'in_progress' for t in tickets),
        'resolved': sum(t['status'] in ('resolved', 'closed') for t in tickets),
    }
    query = request.GET.get('q', '').strip()[:150]
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    sort = request.GET.get('sort', 'newest')
    if status not in dict(demo_store.STATUSES):
        status = ''
    if category not in dict(demo_store.CATEGORIES):
        category = ''
    if sort not in ('newest', 'oldest', 'priority'):
        sort = 'newest'
    if query:
        tickets = [t for t in tickets if query.casefold() in
                   f"HD-{t['id']} {t['title']} {t['location']}".casefold()]
    if status:
        tickets = [t for t in tickets if t['status'] == status]
    if category:
        tickets = [t for t in tickets if t['category'] == category]
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
        'has_filters': bool(query or status or category),
    })


@require_http_methods(['GET', 'POST'])
def ticket_create(request):
    tickets = demo_store.get_tickets(request)
    initial = {'location': request.GET.get('location', '')[:100]}
    if request.GET.get('category') in dict(demo_store.CATEGORIES):
        initial['category'] = request.GET['category']
    form = TicketForm(request.POST if request.method == 'POST' else None,
                      request.FILES if request.method == 'POST' else None, initial=initial)
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
                'attachment': {'name': attachment.name, 'size': attachment.size} if attachment else None,
                'events': [{'title': 'Đã tạo ticket xem thử', 'at': now}],
            }
            tickets.append(ticket)
            demo_store.save_tickets(request, tickets)
            messages.success(request, 'Đã tạo ticket xem thử. Yêu cầu này chưa được gửi đến bộ phận kỹ thuật.')
            return redirect('tickets:detail', ticket_id=ticket['id'])
    return render(request, 'tickets/create.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def ticket_detail(request, ticket_id):
    tickets = demo_store.get_tickets(request)
    ticket = next((t for t in tickets if t['id'] == ticket_id), None)
    if ticket is None:
        raise Http404('Không tìm thấy ticket trong phiên xem thử này.')
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
    return render(request, 'tickets/detail.html', {'ticket': demo_store.present(ticket), 'form': form})
