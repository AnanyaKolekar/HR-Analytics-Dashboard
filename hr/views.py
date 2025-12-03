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
from datetime import datetime, date
import json

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
    """Main dashboard page showing KPIs and charts"""
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

            # Calculate KPIs with error handling
            try:
                kpis = {
                    'total_employees': EmployeeAnalytics.get_total_employees(status='active'),
                    'attendance': AttendanceAnalytics.get_attendance_percentage(
                        start_date=start_date,
                        end_date=end_date
                    ),
                    'leaves': LeaveAnalytics.get_total_leaves(
                        start_date=start_date,
                        end_date=end_date
                    ),
                    'attrition': AttritionAnalytics.get_attrition_rate(
                        start_date=start_date,
                        end_date=end_date
                    ),
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
    """API endpoint for attendance chart data"""
    login_url = 'admin:login'

    def get(self, request):
        """Return attendance chart as base64 image"""
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
