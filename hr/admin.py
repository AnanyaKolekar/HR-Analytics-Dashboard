from django.contrib import admin
from .models import Employee, Attendance, LeaveRecord, AttritionRecord


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['emp_id', 'name', 'department', 'status', 'join_date']
    list_filter = ['status', 'department', 'join_date']
    search_fields = ['emp_id', 'name', 'department']
    ordering = ['emp_id']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['emp', 'date', 'status']
    list_filter = ['status', 'date', 'emp__department']
    search_fields = ['emp__emp_id', 'emp__name']
    ordering = ['-date']


@admin.register(LeaveRecord)
class LeaveRecordAdmin(admin.ModelAdmin):
    list_display = ['emp', 'leave_type', 'start_date', 'end_date', 'duration', 'approved']
    list_filter = ['leave_type', 'approved', 'start_date']
    search_fields = ['emp__emp_id', 'emp__name']
    ordering = ['-start_date']


@admin.register(AttritionRecord)
class AttritionRecordAdmin(admin.ModelAdmin):
    list_display = ['emp', 'exit_date', 'reason']
    list_filter = ['reason', 'exit_date']
    search_fields = ['emp__emp_id', 'emp__name']
    ordering = ['-exit_date']
