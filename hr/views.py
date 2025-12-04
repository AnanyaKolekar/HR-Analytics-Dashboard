"""
Views for HR Dashboard.
Handles request routing, KPI calculation, and template rendering.
"""
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.db.models import Sum
from datetime import datetime, date, timedelta
from django.db.models import Sum
import json

from .models import Employee, Attendance, LeaveRecord, AttritionRecord
from .analytics import (
    AttendanceAnalytics,
    LeaveAnalytics,
    AttritionAnalytics,
    EmployeeAnalytics
)
from .filters import DashboardFilter
from .validation import DataValidator, ErrorHandler
from .charts import ChartGenerator


class DashboardView(LoginRequiredMixin, View):
  
    login_url = 'admin:login'

    def get(self, request):
        """Render dashboard with filtered KPIs and charts"""
        try:
            # Get filter parameters from query string
            department = request.GET.get('department', None)
            start_date_str = request.GET.get('start_date', None)
            end_date_str = request.GET.get('end_date', None)

            is_valid, error_msg = DataValidator.validate_date_range(start_date_str, end_date_str)
            if not is_valid:
                return render(request, 'hr/dashboard.html', {
                    'error': error_msg,
                    'kpis': {},
                    'filter': {}
                })

            # Parse dates
            start_date = None
            end_date = None
            try:
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError as e:
                return render(request, 'hr/dashboard.html', {
                    'error': f'Invalid date format: {str(e)}',
                    'kpis': {},
                    'filter': {}
                })

            valid_depts = list(DashboardFilter.get_departments())
            is_valid, error_msg = DataValidator.validate_department(department, valid_depts)
            if not is_valid:
                return render(request, 'hr/dashboard.html', {
                    'error': error_msg,
                    'kpis': {},
                    'filter': {}
                })

            # Create filter
            dashboard_filter = DashboardFilter(
                department=department,
                start_date=start_date,
                end_date=end_date
            )

           
            try:
                # Filter total employees by department if specified
                if department:
                    total_employees = Employee.objects.filter(
                        department=department,
                        status='active'
                    ).count()
                    
                    # Filter attendance by department
                    dept_employees = Employee.objects.filter(department=department, status='active')
                    attendance_start = start_date or (date.today() - timedelta(days=30))
                    attendance_end = end_date or date.today()
                    attendance_query = Attendance.objects.filter(
                        emp__in=dept_employees,
                        date__range=[attendance_start, attendance_end]
                    )
                    attendance_total = attendance_query.count()
                    attendance_present = attendance_query.filter(status__in=['present', 'half-day']).count()
                    attendance_percentage = round((attendance_present / attendance_total * 100), 2) if attendance_total > 0 else 0
                    
                    attendance_data = {
                        'attendance_percentage': attendance_percentage,
                        'total_days': attendance_total,
                        'present_days': attendance_present,
                    }
                    
                    # Filter leaves by department
                    leaves_start = start_date or (date.today() - timedelta(days=365))
                    leaves_end = end_date or date.today()
                    leaves_query = LeaveRecord.objects.filter(
                        emp__department=department,
                        start_date__range=[leaves_start, leaves_end],
                        approved=True
                    )
                    leaves_total = leaves_query.count()
                    leaves_days = leaves_query.aggregate(total=Sum('duration'))['total'] or 0
                    
                    leaves_data = {
                        'total_leaves': leaves_total,
                        'total_days': leaves_days,
                    }
                    
                    # Filter attrition by department
                    dept_total_employees = Employee.objects.filter(department=department).count()
                    attrition_start = start_date or (date.today() - timedelta(days=365))
                    attrition_end = end_date or date.today()
                    attrition_query = AttritionRecord.objects.filter(
                        emp__department=department,
                        exit_date__range=[attrition_start, attrition_end]
                    )
                    attrition_separated = attrition_query.count()
                    attrition_rate = round((attrition_separated / dept_total_employees * 100), 2) if dept_total_employees > 0 else 0
                    
                    attrition_data = {
                        'attrition_rate': attrition_rate,
                        'separated_count': attrition_separated,
                    }
                else:
                    total_employees = EmployeeAnalytics.get_total_employees(status='active')
                    attendance_data = AttendanceAnalytics.get_attendance_percentage(
                        start_date=start_date,
                        end_date=end_date
                    )
                    leaves_data = LeaveAnalytics.get_total_leaves(
                        start_date=start_date,
                        end_date=end_date
                    )
                    attrition_data = AttritionAnalytics.get_attrition_rate(
                        start_date=start_date,
                        end_date=end_date
                    )
                
                kpis = {
                    'total_employees': total_employees,
                    'attendance': attendance_data,
                    'leaves': leaves_data,
                    'attrition': attrition_data,
                    'departments': valid_depts,
                }
            except Exception as e:
                return render(request, 'hr/dashboard.html', {
                    'error': f'Error calculating KPIs: {str(e)}',
                    'kpis': {},
                    'filter': {}
                })

            context = {
                'kpis': kpis,
                'filter': {
                    'department': department,
                    'start_date': start_date_str or '',
                    'end_date': end_date_str or '',
                },
                'page_title': 'HR Dashboard'
            }

            return render(request, 'hr/dashboard.html', context)

        except Exception as e:
            return render(request, 'hr/dashboard.html', {
                'error': f'Unexpected error: {str(e)}',
                'kpis': {},
                'filter': {}
            })


class AttendanceChartView(LoginRequiredMixin, View):
    
    login_url = 'admin:login'

    def get(self, request):
        
        try:
            department = request.GET.get('department', None)
            start_date_str = request.GET.get('start_date', None)
            end_date_str = request.GET.get('end_date', None)

            is_valid, error_msg = DataValidator.validate_date_range(start_date_str, end_date_str)
            if not is_valid:
                return JsonResponse(ErrorHandler.format_error(error_msg), status=400)

            # Parse dates
            start_date = None
            end_date = None
            try:
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(ErrorHandler.format_error('Invalid date format'), status=400)

            # Get departmental attendance data
            dept_attendance = AttendanceAnalytics.get_departmental_attendance(
                start_date=start_date,
                end_date=end_date
            )

            # Filter by department if specified
            if department:
                dept_attendance = {k: v for k, v in dept_attendance.items() if k == department}

            # Generate chart image
            if dept_attendance:
                chart_image = ChartGenerator.generate_attendance_chart(dept_attendance)
                return JsonResponse({
                    'data': list(dept_attendance.keys()),
                    'image': chart_image,
                    'success': True
                })
            else:
                return JsonResponse({'data': [], 'image': None, 'success': False})

        except Exception as e:
            print(f"[v0] Attendance chart error: {str(e)}")
            return JsonResponse(ErrorHandler.format_error(f'Error generating chart: {str(e)}'), status=500)


class LeaveChartView(LoginRequiredMixin, View):
    
    login_url = 'admin:login'

    def get(self, request):
       
        try:
            start_date_str = request.GET.get('start_date', None)
            end_date_str = request.GET.get('end_date', None)

            is_valid, error_msg = DataValidator.validate_date_range(start_date_str, end_date_str)
            if not is_valid:
                return JsonResponse(ErrorHandler.format_error(error_msg), status=400)

            # Parse dates
            start_date = None
            end_date = None
            try:
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(ErrorHandler.format_error('Invalid date format'), status=400)

            # Get leave distribution data
            leave_dist = LeaveAnalytics.get_leave_distribution(start_date=start_date, end_date=end_date)

            # Map leave type codes to labels
            leave_type_labels = {
                'sick': 'Sick Leave',
                'annual': 'Annual Leave',
                'casual': 'Casual Leave',
                'unpaid': 'Unpaid Leave',
                'maternity': 'Maternity Leave',
            }

            chart_data = []
            for leave_type_data in leave_dist:
                label = leave_type_labels.get(leave_type_data['leave_type'], leave_type_data['leave_type'])
                chart_data.append({
                    'leave_type': label,
                    'count': leave_type_data['count'],
                })

            if chart_data:
                chart_image = ChartGenerator.generate_leave_chart(chart_data)
                return JsonResponse({
                    'data': chart_data,
                    'image': chart_image,
                    'success': True
                })
            else:
                return JsonResponse({'data': [], 'image': None, 'success': False})

        except Exception as e:
            print(f"[v0] Leave chart error: {str(e)}")
            return JsonResponse(ErrorHandler.format_error(f'Error generating chart: {str(e)}'), status=500)


class AttritionChartView(LoginRequiredMixin, View):
   
    login_url = 'admin:login'

    def get(self, request):
        """Return attrition chart as base64 image"""
        try:
            department = request.GET.get('department', None)
            start_date_str = request.GET.get('start_date', None)
            end_date_str = request.GET.get('end_date', None)

            is_valid, error_msg = DataValidator.validate_date_range(start_date_str, end_date_str)
            if not is_valid:
                return JsonResponse(ErrorHandler.format_error(error_msg), status=400)

            # Parse dates
            start_date = None
            end_date = None
            try:
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                if end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse(ErrorHandler.format_error('Invalid date format'), status=400)

            # Get departmental attrition data
            dept_attrition = AttritionAnalytics.get_departmental_attrition(
                start_date=start_date,
                end_date=end_date
            )

            # Filter by department if specified
            if department:
                dept_attrition = {k: v for k, v in dept_attrition.items() if k == department}

            if dept_attrition:
                chart_image = ChartGenerator.generate_attrition_chart(dept_attrition)
                return JsonResponse({
                    'data': list(dept_attrition.keys()),
                    'image': chart_image,
                    'success': True
                })
            else:
                return JsonResponse({'data': [], 'image': None, 'success': False})

        except Exception as e:
            print(f"[v0] Attrition chart error: {str(e)}")
            return JsonResponse(ErrorHandler.format_error(f'Error generating chart: {str(e)}'), status=500)


class EmployeesByDepartmentView(LoginRequiredMixin, View):
    """API endpoint to return employees by department"""
    login_url = 'admin:login'

    def get(self, request):
        """Return list of employees for a given department"""
        try:
            department = request.GET.get('department', None)
            
            if not department:
                return JsonResponse({
                    'success': False,
                    'error': 'Department parameter is required'
                }, status=400)
            
            # Validate department exists
            valid_depts = list(DashboardFilter.get_departments())
            if department not in valid_depts:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid department: {department}'
                }, status=400)
            
            # Get employees for the department
            employees_queryset = Employee.objects.filter(
                department=department,
                status='active'
            ).order_by('name').values('emp_id', 'name', 'department', 'join_date')
            
            employees_list = list(employees_queryset)
            
            return JsonResponse({
                'success': True,
                'department': department,
                'employees': employees_list,
                'count': len(employees_list)
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error in EmployeesByDepartmentView: {error_trace}")
            return JsonResponse({
                'success': False,
                'error': f'Error fetching employees: {str(e)}'
            }, status=500)


class EmployeeDetailsView(LoginRequiredMixin, View):
    """API endpoint to return individual employee attendance stats"""
    login_url = 'admin:login'

    def get(self, request, emp_id):
        """Return employee details including attendance stats"""
        try:
            # Get date range from query params (optional)
            start_date_str = request.GET.get('start_date', None)
            end_date_str = request.GET.get('end_date', None)
            
            # Parse dates
            start_date = None
            end_date = None
            if start_date_str:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if end_date_str:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Get employee
            try:
                employee = Employee.objects.get(emp_id=emp_id, status='active')
            except Employee.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Employee with ID {emp_id} not found'
                }, status=404)
            
            # Get attendance stats
            attendance_stats = AttendanceAnalytics.get_attendance_percentage(
                emp_id=emp_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Get leave stats
            leave_stats = LeaveAnalytics.get_total_leaves(
                emp_id=emp_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Calculate total working days (attendance records count)
            if start_date and end_date:
                total_working_days = Attendance.objects.filter(
                    emp=employee,
                    date__range=[start_date, end_date]
                ).count()
            else:
                # Default to last 30 days if no date range provided
                default_start = date.today() - timedelta(days=30)
                total_working_days = Attendance.objects.filter(
                    emp=employee,
                    date__gte=default_start
                ).count()
            
            return JsonResponse({
                'success': True,
                'employee': {
                    'emp_id': employee.emp_id,
                    'name': employee.name,
                    'department': employee.department,
                    'join_date': employee.join_date.isoformat(),
                },
                'attendance_rate': attendance_stats.get('attendance_percentage', 0),
                'total_leaves': leave_stats.get('total_leaves', 0),
                'total_working_days': total_working_days,
                'attendance_details': {
                    'present_days': attendance_stats.get('present_days', 0),
                    'absent_days': attendance_stats.get('absent_days', 0),
                    'total_days': attendance_stats.get('total_days', 0),
                },
                'leave_details': {
                    'total_days': leave_stats.get('total_days', 0),
                    'average_duration': leave_stats.get('average_duration', 0),
                }
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid date format: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error fetching employee details: {str(e)}'
            }, status=500)
