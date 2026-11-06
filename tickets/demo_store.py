"""Temporary, session-scoped data for Frontend 1. Replace with backend queries later.

No ticket model is created here. Attachments retain metadata only, never file bytes.
"""

from copy import deepcopy
from datetime import datetime, timedelta

from django.conf import settings
from django.http import Http404
from django.utils import timezone


SESSION_KEY = 'frontend1_demo_tickets_v1'
OWNER_KEY = 'frontend1_demo_owner_v1'
MAX_TICKETS = 30
MAX_REPLIES = 30
CATEGORIES = [('network', 'Mạng LAN / Wi-Fi'), ('vpn', 'Kết nối VPN'),
              ('printer', 'Máy in'), ('other', 'Sự cố khác')]
PRIORITIES = [('low', 'Thấp'), ('normal', 'Bình thường'),
              ('high', 'Cao'), ('urgent', 'Khẩn cấp')]
STATUSES = [('new', 'Chờ tiếp nhận'), ('in_progress', 'Đang xử lý'),
            ('resolved', 'Đã xử lý'), ('closed', 'Đã đóng')]


def is_enabled():
    return getattr(settings, 'FRONTEND_DEMO_ENABLED', settings.DEBUG)


def require_demo():
    # Demo pages are unavailable in production unless explicitly enabled.
    if not is_enabled():
        raise Http404('Giao diện xem thử chưa được bật.')


def _fixtures(reporter):
    examples = [
        (1006, 'Wi-Fi chập chờn trong giờ học', 'network', 'high', 'in_progress', 'A.201'),
        (1005, 'Máy in không nhận lệnh từ máy tính', 'printer', 'normal', 'new', 'Phòng giáo vụ'),
        (1004, 'Không kết nối được VPN từ nhà', 'vpn', 'normal', 'resolved', 'Làm việc từ xa'),
        (1003, 'Máy tính phòng thực hành mất mạng', 'network', 'urgent', 'new', 'B.302'),
        (1002, 'Cổng mạng tại bàn làm việc không hoạt động', 'other', 'low', 'closed', 'A.105'),
        (1001, 'Không tìm thấy máy in trong mạng nội bộ', 'printer', 'normal', 'in_progress', 'Thư viện'),
    ]
    tickets = []
    now = timezone.now()
    for index, (pk, title, category, priority, status, location) in enumerate(examples):
        created = (now - timedelta(days=index + 1)).isoformat()
        events = [{'title': 'Đã tạo ticket mẫu', 'at': created}]
        replies = []
        if status != 'new':
            updated = (now - timedelta(days=index, hours=20)).isoformat()
            events.append({'title': 'Kỹ thuật viên đã tiếp nhận (mẫu)', 'at': updated})
            replies.append({'author': 'Kỹ thuật viên (mẫu)', 'role': 'staff', 'at': updated,
                            'content': 'Bộ phận kỹ thuật đã nhận thông tin và đang kiểm tra kết nối tại vị trí bạn báo.'})
        if status in ('resolved', 'closed'):
            events.append({'title': 'Đã xử lý sự cố (mẫu)',
                           'at': (now - timedelta(days=index, hours=18)).isoformat()})
        if status == 'closed':
            events.append({'title': 'Đã đóng ticket (mẫu)',
                           'at': (now - timedelta(days=index, hours=16)).isoformat()})
        tickets.append({
            'id': pk, 'title': title, 'category': category, 'priority': priority,
            'status': status, 'location': location, 'reporter': reporter,
            'description': 'Đây là nội dung minh họa để kiểm tra giao diện. Kết nối bị gián đoạn trong lúc sử dụng. Đã thử kết nối lại nhưng tình trạng vẫn tiếp diễn.',
            'created_at': created, 'attachment': None, 'replies': replies, 'events': events,
        })
    return tickets


def get_tickets(request):
    require_demo()
    owner = str(request.user.pk)
    if SESSION_KEY not in request.session or request.session.get(OWNER_KEY) != owner:
        reporter = request.user.get_full_name() or request.user.get_username()
        request.session[SESSION_KEY] = _fixtures(reporter)
        request.session[OWNER_KEY] = owner
    return deepcopy(request.session[SESSION_KEY])


def save_tickets(request, tickets):
    request.session[SESSION_KEY] = tickets


def summary(tickets):
    return {
        'total': len(tickets),
        **{status: sum(t['status'] == status for t in tickets) for status, _ in STATUSES},
    }


def present(ticket):
    result = deepcopy(ticket)
    result['code'] = f"HD-{ticket['id']}"
    result['category_label'] = dict(CATEGORIES)[ticket['category']]
    result['priority_label'] = dict(PRIORITIES)[ticket['priority']]
    result['status_label'] = dict(STATUSES)[ticket['status']]
    result['created_at'] = datetime.fromisoformat(ticket['created_at'])
    for entry in result['replies'] + result['events']:
        entry['at'] = datetime.fromisoformat(entry['at'])
    current = [key for key, _ in STATUSES].index(ticket['status'])
    result['steps'] = [
        {'label': label, 'done': index <= current, 'current': index == current}
        for index, (_, label) in enumerate(STATUSES)
    ]
    return result
