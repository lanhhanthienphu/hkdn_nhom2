from django import forms
from django.contrib import admin
from django.db import router, transaction
from django.urls import reverse
from django.utils.html import format_html

from notifications.ticket_events import notify_ticket_event

from .models import Attachment, Comment, Ticket, TicketHistory


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    fields = ('original_name', 'size', 'uploaded_by', 'created_at', 'download_link')
    readonly_fields = fields
    can_delete = False

    @admin.display(description='Tải tệp')
    def download_link(self, obj):
        if not obj.pk:
            return '-'
        url = reverse('tickets:attachment_download', args=[obj.ticket_id, obj.pk])
        return format_html('<a href="{}">Tải tệp</a>', url)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ('changed_by', 'old_status', 'new_status', 'assigned_to', 'note', 'created_at')
    can_delete = False


class TicketAdminForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = '__all__'

    def clean_assigned_to(self):
        technician = self.cleaned_data.get('assigned_to')
        if technician and (not self.instance.pk or 'assigned_to' in self.changed_data):
            Ticket.validate_technician(technician)
        return technician


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    form = TicketAdminForm
    list_display = (
        'get_code',
        'title',
        'category',
        'priority',
        'status',
        'created_by',
        'assigned_to',
        'created_at',
    )
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('id', 'title', 'description', 'location', 'created_by__username', 'assigned_to__username')
    inlines = [AttachmentInline, CommentInline, TicketHistoryInline]
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        # Admin edits bypass Ticket.assign_technician/change_status. Record their
        # real transitions here; plain saves elsewhere intentionally send no mail.
        database = router.db_for_write(Ticket, instance=obj)
        with transaction.atomic(using=database):
            before = Ticket.objects.using(database).select_for_update().get(pk=obj.pk) if change else None
            assigned_changed = obj.assigned_to_id != (before.assigned_to_id if before else None)
            if assigned_changed and obj.assigned_to_id and obj.status == 'new' and 'status' not in form.changed_data:
                obj.status = 'in_progress'
            super().save_model(request, obj, form, change)

            if before is None:
                TicketHistory.objects.using(database).create(
                    ticket=obj, changed_by=request.user, old_status='', new_status=obj.status,
                    assigned_to=obj.assigned_to, note='Đã tạo yêu cầu hỗ trợ sự cố qua trang quản trị',
                )
                notify_ticket_event(obj, 'created')
                if obj.assigned_to_id:
                    notify_ticket_event(obj, 'assigned')
                return

            if assigned_changed:
                note = f'Phân công cho {obj.assignee_name}' if obj.assigned_to_id else 'Đã bỏ phân công kỹ thuật viên'
                TicketHistory.objects.using(database).create(
                    ticket=obj, changed_by=request.user, old_status=before.status,
                    new_status=obj.status, assigned_to=obj.assigned_to, note=note[:255],
                )
                if obj.assigned_to_id:
                    notify_ticket_event(obj, 'assigned')
            if before.status != obj.status:
                # An automatic new -> in_progress is already in the assignment log.
                if not assigned_changed or 'status' in form.changed_data:
                    TicketHistory.objects.using(database).create(
                        ticket=obj, changed_by=request.user, old_status=before.status,
                        new_status=obj.status, assigned_to=obj.assigned_to,
                        note=f'Cập nhật trạng thái thành {obj.status_label}',
                    )
                if obj.status == 'resolved':
                    notify_ticket_event(obj, 'resolved')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'user__username', 'ticket__title')


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'changed_by', 'old_status', 'new_status', 'assigned_to', 'created_at')
    list_filter = ('old_status', 'new_status', 'created_at')
    search_fields = ('ticket__title', 'changed_by__username', 'note')
