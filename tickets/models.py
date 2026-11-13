from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from notifications.ticket_events import notify_ticket_event

from .attachment_storage import PrivateAttachmentStorage, attachment_upload_path


class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ('network', 'Mạng LAN / Wi-Fi'),
        ('vpn', 'Kết nối VPN'),
        ('printer', 'Máy in'),
        ('other', 'Sự cố khác'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Thấp'),
        ('normal', 'Bình thường'),
        ('high', 'Cao'),
        ('urgent', 'Khẩn cấp'),
    ]

    STATUS_CHOICES = [
        ('new', 'Chờ tiếp nhận'),
        ('in_progress', 'Đang xử lý'),
        ('resolved', 'Đã xử lý'),
        ('closed', 'Đã đóng'),
    ]

    title = models.CharField(max_length=150, verbose_name="Tiêu đề sự cố")
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='network',
        verbose_name="Nhóm sự cố",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name="Độ ưu tiên",
    )
    location = models.CharField(max_length=100, verbose_name="Vị trí xảy ra sự cố")
    description = models.TextField(verbose_name="Mô tả chi tiết")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Trạng thái",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tickets",
        verbose_name="Người tạo",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tickets",
        verbose_name="Người phụ trách",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian tạo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Cập nhật lần cuối")
    attachment_name = models.CharField(max_length=255, blank=True, default="", verbose_name="Tên file đính kèm")
    attachment_size = models.PositiveIntegerField(null=True, blank=True, verbose_name="Dung lượng file (bytes)")

    class Meta:
        db_table = "tickets"
        ordering = ['-created_at']
        verbose_name = "Phiếu hỗ trợ (Ticket)"
        verbose_name_plural = "Danh sách Phiếu hỗ trợ"

    def __str__(self):
        return f"{self.get_code()} - {self.title}"

    def get_code(self) -> str:
        return f"HD-{self.id}"

    @property
    def code(self) -> str:
        return self.get_code()

    @property
    def category_label(self) -> str:
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)

    @property
    def priority_label(self) -> str:
        return dict(self.PRIORITY_CHOICES).get(self.priority, self.priority)

    @property
    def status_label(self) -> str:
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    @property
    def reporter(self) -> str:
        return self.created_by.get_full_name() or self.created_by.get_username()

    @property
    def attachment(self):
        if self.attachment_name:
            return {'name': self.attachment_name, 'size': self.attachment_size or 0}
        return None

    @property
    def replies(self):
        result = []
        for c in self.comments.select_related('user').all():
            is_staff = c.user.is_staff or c.user.is_superuser
            if hasattr(c.user, 'profile') and c.user.profile.is_technician():
                is_staff = True
            result.append({
                'id': c.id,
                'author': c.user.get_full_name() or c.user.get_username(),
                'role': 'staff' if is_staff else 'user',
                'content': c.content,
                'at': c.created_at,
            })
        return result

    @property
    def events(self):
        result = [{
            'title': 'Đã tạo ticket',
            'at': self.created_at,
        }]
        for h in self.histories.all():
            title = h.note or f"Chuyển trạng thái: {h.new_status}"
            result.append({
                'title': title,
                'at': h.created_at,
            })
        return result

    @property
    def assignee_name(self) -> str:
        if self.assigned_to:
            return self.assigned_to.get_full_name() or self.assigned_to.get_username()
        return "Chưa phân công"

    @property
    def steps(self):
        keys = [k for k, _ in self.STATUS_CHOICES]
        current_idx = keys.index(self.status) if self.status in keys else 0
        return [
            {
                'label': label,
                'done': idx <= current_idx,
                'current': idx == current_idx,
            }
            for idx, (_, label) in enumerate(self.STATUS_CHOICES)
        ]

    def can_view(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if self.created_by_id == user.id or self.assigned_to_id == user.id:
            return True
        if hasattr(user, 'profile') and user.profile.is_technician():
            return True
        return False

    @staticmethod
    def validate_technician(tech):
        is_tech = tech and hasattr(tech, 'profile') and tech.profile.is_technician()
        if not tech or not tech.is_active or not (tech.is_superuser or is_tech):
            raise ValidationError('Chỉ được phân công cho kỹ thuật viên hoặc quản trị viên đang hoạt động.')

    def assign_technician(self, tech, by, note: str = "") -> bool:
        self.validate_technician(tech)
        database = self._state.db or 'default'
        with transaction.atomic(using=database):
            current = Ticket.objects.using(database).select_for_update().get(pk=self.pk)
            if current.assigned_to_id == tech.pk:
                self.refresh_from_db(using=database)
                return False
            old_status = current.status
            current.assigned_to = tech
            if current.status == 'new':
                current.status = 'in_progress'
            current.save(using=database, update_fields=['assigned_to', 'status', 'updated_at'])
            log_note = note or f"Phân công cho {tech.get_full_name() or tech.get_username()}"
            TicketHistory.objects.using(database).create(
                ticket=current, changed_by=by, old_status=old_status,
                new_status=current.status, assigned_to=tech, note=log_note[:255],
            )
            notify_ticket_event(current, 'assigned')
            self.refresh_from_db(using=database)
        return True

    def change_status(self, new_status: str, by, note: str = "") -> bool:
        if new_status == 'open':
            new_status = 'new'
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValidationError('Trạng thái không hợp lệ.')
        database = self._state.db or 'default'
        with transaction.atomic(using=database):
            current = Ticket.objects.using(database).select_for_update().get(pk=self.pk)
            if current.status == new_status:
                self.refresh_from_db(using=database)
                return False
            old_status = current.status
            current.status = new_status
            current.save(using=database, update_fields=['status', 'updated_at'])
            log_note = note or f"Cập nhật trạng thái thành {current.status_label}"
            TicketHistory.objects.using(database).create(
                ticket=current, changed_by=by, old_status=old_status,
                new_status=new_status, assigned_to=current.assigned_to, note=log_note[:255],
            )
            if new_status == 'resolved':
                notify_ticket_event(current, 'resolved')
            self.refresh_from_db(using=database)
        return True


class Attachment(models.Model):
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name='attachments', verbose_name='Ticket',
    )
    file = models.FileField(
        'Tệp', upload_to=attachment_upload_path, storage=PrivateAttachmentStorage(), max_length=255,
    )
    original_name = models.CharField('Tên tệp', max_length=255)
    size = models.PositiveIntegerField('Dung lượng (bytes)')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ticket_attachments', verbose_name='Người tải lên',
    )
    created_at = models.DateTimeField('Ngày tải lên', auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'pk']
        verbose_name = 'Tệp đính kèm'
        verbose_name_plural = 'Tệp đính kèm'

    def __str__(self):
        return self.original_name


class Comment(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Ticket",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ticket_comments",
        verbose_name="Người bình luận",
    )
    content = models.TextField(verbose_name="Nội dung trao đổi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian")

    class Meta:
        db_table = "comments"
        ordering = ['created_at']
        verbose_name = "Bình luận"
        verbose_name_plural = "Bình luận"

    def __str__(self):
        return f"Bình luận bởi {self.user.username} trên {self.ticket.get_code()}"


class TicketHistory(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="histories",
        verbose_name="Ticket",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ticket_history_changes",
        verbose_name="Người thực hiện",
    )
    old_status = models.CharField(max_length=20, blank=True, verbose_name="Trạng thái cũ")
    new_status = models.CharField(max_length=20, blank=True, verbose_name="Trạng thái mới")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ticket_history_assignments",
        verbose_name="Gán cho kỹ thuật viên",
    )
    note = models.CharField(max_length=255, blank=True, verbose_name="Ghi chú")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian ghi nhận")

    class Meta:
        db_table = "ticket_history"
        ordering = ['created_at']
        verbose_name = "Lịch sử xử lý ticket"
        verbose_name_plural = "Lịch sử xử lý ticket"

    def __str__(self):
        return f"Lịch sử {self.ticket.get_code()} ({self.new_status}) lúc {self.created_at}"
