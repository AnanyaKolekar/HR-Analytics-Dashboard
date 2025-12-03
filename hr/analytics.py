from django.db.models import Count, Q, F, Case, When, IntegerField, Sum
from django.utils import timezone
from datetime import timedelta, date
from .models import Employee, Attendance, LeaveRecord, AttritionRecord


class AttendanceAnalytics:
 

    @staticmethod
    def get_attendance_percentage(emp_id=None, start_date=None, end_date=None):
       
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()

        query = Attendance.objects.filter(date__range=[start_date, end_date])
        if emp_id:
            query = query.filter(emp__emp_id=emp_id)

        total_records = query.count()
        if total_records == 0:
            return {'attendance_percentage': 0, 'total_days': 0, 'present_days': 0}

        present_days = query.filter(status__in=['present', 'half-day']).count()

        return {
            'attendance_percentage': round((present_days / total_records) * 100, 2),
            'total_days': total_records,
            'present_days': present_days,
            'absent_days': total_records - present_days,
        }

    @staticmethod
    def get_departmental_attendance(start_date=None, end_date=None):
       
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()

        departments = Employee.objects.filter(status='active').values('department').distinct()
        result = {}

        for dept_obj in departments:
            dept = dept_obj['department']
            dept_emps = Employee.objects.filter(department=dept, status='active')

            attendance_records = Attendance.objects.filter(
                emp__in=dept_emps,
                date__range=[start_date, end_date]
            )

            total = attendance_records.count()
            if total == 0:
                result[dept] = {'percentage': 0, 'count': 0}
                continue

            present = attendance_records.filter(status__in=['present', 'half-day']).count()
            result[dept] = {
                'percentage': round((present / total) * 100, 2),
                'count': total,
                'present': present,
            }

        return result


class LeaveAnalytics:
   

    @staticmethod
    def get_leave_distribution(start_date=None, end_date=None):
       
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        leave_types = LeaveRecord.objects.filter(
            start_date__range=[start_date, end_date],
            approved=True
        ).values('leave_type').annotate(count=Count('id')).order_by('-count')

        return list(leave_types)

    @staticmethod
    def get_total_leaves(emp_id=None, start_date=None, end_date=None):
        """Get total approved leaves for employee(s)"""
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        query = LeaveRecord.objects.filter(
            start_date__range=[start_date, end_date],
            approved=True
        )

        if emp_id:
            query = query.filter(emp__emp_id=emp_id)

        total_duration = query.aggregate(total=Sum('duration'))['total'] or 0
        total_leaves = query.count()

        return {
            'total_leaves': total_leaves,
            'total_days': total_duration,
            'average_duration': round(total_duration / total_leaves, 2) if total_leaves > 0 else 0,
        }

    @staticmethod
    def get_departmental_leaves(start_date=None, end_date=None):
        """Get leave statistics by department"""
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        departments = Employee.objects.filter(status='active').values('department').distinct()
        result = {}

        for dept_obj in departments:
            dept = dept_obj['department']
            dept_leaves = LeaveRecord.objects.filter(
                emp__department=dept,
                start_date__range=[start_date, end_date],
                approved=True
            )

            total_days = dept_leaves.aggregate(total=Sum('duration'))['total'] or 0
            result[dept] = {
                'total_leaves': dept_leaves.count(),
                'total_days': total_days,
            }

        return result


class AttritionAnalytics:
    

    @staticmethod
    def get_attrition_rate(start_date=None, end_date=None):
       
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        # Count employees who left during period
        separated = AttritionRecord.objects.filter(
            exit_date__range=[start_date, end_date]
        ).count()

        # Get average active employee count
        # This is simplified; in production, track employee count over time
        avg_employees = Employee.objects.filter(status='active').count()

        if avg_employees == 0:
            return {'attrition_rate': 0, 'separated_count': 0, 'employee_count': avg_employees}

        attrition_rate = round((separated / avg_employees) * 100, 2)

        return {
            'attrition_rate': attrition_rate,
            'separated_count': separated,
            'employee_count': avg_employees,
        }

    @staticmethod
    def get_attrition_by_reason(start_date=None, end_date=None):
        """Get attrition breakdown by reason"""
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        reasons = AttritionRecord.objects.filter(
            exit_date__range=[start_date, end_date]
        ).values('reason').annotate(count=Count('id')).order_by('-count')

        return list(reasons)

    @staticmethod
    def get_departmental_attrition(start_date=None, end_date=None):
        """Get attrition statistics by department"""
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        departments = Employee.objects.values('department').distinct()
        result = {}

        for dept_obj in departments:
            dept = dept_obj['department']
            dept_employees = Employee.objects.filter(department=dept).count()
            dept_attrition = AttritionRecord.objects.filter(
                emp__department=dept,
                exit_date__range=[start_date, end_date]
            ).count()

            if dept_employees == 0:
                result[dept] = {'attrition_rate': 0, 'count': 0}
            else:
                result[dept] = {
                    'attrition_rate': round((dept_attrition / dept_employees) * 100, 2),
                    'count': dept_attrition,
                }

        return result


class EmployeeAnalytics:
    """Calculate employee-related KPIs"""

    @staticmethod
    def get_total_employees(status=None):
        """Get total employee count"""
        query = Employee.objects.all()
        if status:
            query = query.filter(status=status)

        return query.count()

    @staticmethod
    def get_employees_by_department():
        """Get employee count by department"""
        departments = Employee.objects.filter(
            status='active'
        ).values('department').annotate(count=Count('id')).order_by('-count')

        return list(departments)

    @staticmethod
    def get_summary_kpis(start_date=None, end_date=None):
        """Get comprehensive KPI summary"""
        if start_date is None:
            start_date = date.today() - timedelta(days=30)
        if end_date is None:
            end_date = date.today()

        total_employees = Employee.objects.filter(status='active').count()
        attendance = AttendanceAnalytics.get_attendance_percentage(start_date=start_date, end_date=end_date)
        leaves = LeaveAnalytics.get_total_leaves(start_date=start_date, end_date=end_date)
        attrition = AttritionAnalytics.get_attrition_rate(start_date=start_date, end_date=end_date)

        return {
            'total_employees': total_employees,
            'attendance': attendance,
            'leaves': leaves,
            'attrition': attrition,
        }
