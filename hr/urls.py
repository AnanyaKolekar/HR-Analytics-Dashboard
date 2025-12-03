"""
URL configuration for HR Dashboard app.
"""
from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    # Dashboard main view
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Chart API endpoints
    path('api/attendance-chart/', views.AttendanceChartView.as_view(), name='attendance_chart'),
    path('api/leave-chart/', views.LeaveChartView.as_view(), name='leave_chart'),
    path('api/attrition-chart/', views.AttritionChartView.as_view(), name='attrition_chart'),
]
