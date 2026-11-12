from django.contrib import admin
from .models import Comment, Ticket, TicketHistory


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ('changed_by', 'old_status', 'new_status', 'assigned_to', 'note', 'created_at')
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
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
    inlines = [CommentInline, TicketHistoryInline]
    readonly_fields = ('created_at', 'updated_at')


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
