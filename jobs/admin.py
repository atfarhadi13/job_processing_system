from django.contrib import admin
from .models import Job, JobResult

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'status', 'scheduled_time', 'created_at')
    list_filter = ('status', 'scheduled_time', 'created_at')
    search_fields = ('name', 'description', 'user__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

@admin.register(JobResult)
class JobResultAdmin(admin.ModelAdmin):
    list_display = ('job', 'completed_at', 'short_output', 'short_error_message')
    search_fields = ('job__name', 'job__user__email')
    readonly_fields = ('completed_at',)

    def short_output(self, obj):
        return (obj.output[:50] + '...') if obj.output and len(obj.output) > 50 else obj.output
    short_output.short_description = 'Output'

    def short_error_message(self, obj):
        return (obj.error_message[:50] + '...') if obj.error_message and len(obj.error_message) > 50 else obj.error_message
    short_error_message.short_description = 'Error Message'
