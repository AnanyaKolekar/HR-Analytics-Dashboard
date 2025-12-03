from django.db.models import Q
from datetime import date, timedelta
from .models import Employee, Attendance, LeaveRecord, AttritionRecord


class DashboardFilter:
    def __init__(self, department=None, start_date=None, end_date=None):
        self.department = department
        self.start_date = start_date or (date.today() - timedelta(days=30))
        self.end_date = end_date or date.today()

    def filter_employees(self):
       
        query = Employee.objects.filter(status='active')

        if self.department:
            query = query.filter(department=self.department)

        return query

    def filter_attendance(self):
       
        query = Attendance.objects.filter(date__range=[self.start_date, self.end_date])

        if self.department:
            query = query.filter(emp__department=self.department)

        return query

    def filter_leaves(self):
       
        query = LeaveRecord.objects.filter(
            start_date__range=[self.start_date, self.end_date],
            approved=True
        )

        if self.department:
            query = query.filter(emp__department=self.department)

        return query

    def filter_attrition(self):
        
        query = AttritionRecord.objects.filter(
            exit_date__range=[self.start_date, self.end_date]
        )

        if self.department:
            query = query.filter(emp__department=self.department)

        return query

    @staticmethod
    def get_departments():
        
        return Employee.objects.filter(
            status='active'
        ).values_list('department', flat=True).distinct().order_by('department')
