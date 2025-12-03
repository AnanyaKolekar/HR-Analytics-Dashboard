from django.db import models
from django.core.exceptions import ValidationError
from datetime import date


class Employee(models.Model):
    """Employee master data model"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    emp_id = models.CharField(max_length=20, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=50)
    join_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['emp_id']
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.emp_id} - {self.name}"


class Attendance(models.Model):
    """Daily/Monthly attendance records"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('half-day', 'Half-Day'),
    ]

    emp = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('emp', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['emp', 'date']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.emp.emp_id} - {self.date} - {self.status}"


class LeaveRecord(models.Model):
    """Leave type, duration, and department records"""
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('annual', 'Annual Leave'),
        ('casual', 'Casual Leave'),
        ('unpaid', 'Unpaid Leave'),
        ('maternity', 'Maternity Leave'),
    ]

    emp = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_records')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    duration = models.IntegerField(help_text="Duration in days")
    reason = models.TextField(blank=True, null=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['emp', 'start_date']),
            models.Index(fields=['leave_type']),
        ]

    def clean(self):
        """Validate leave dates"""
        if self.start_date > self.end_date:
            raise ValidationError("Start date must be before end date")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.emp.emp_id} - {self.leave_type} ({self.start_date} to {self.end_date})"


class AttritionRecord(models.Model):
    """Employee exits and reasons"""
    EXIT_REASONS = [
        ('voluntary', 'Voluntary Resignation'),
        ('terminated', 'Termination'),
        ('retired', 'Retirement'),
        ('laid_off', 'Lay Off'),
        ('other', 'Other'),
    ]

    emp = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='attrition_record')
    exit_date = models.DateField()
    reason = models.CharField(max_length=20, choices=EXIT_REASONS)
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-exit_date']
        indexes = [
            models.Index(fields=['exit_date']),
            models.Index(fields=['reason']),
        ]

    def __str__(self):
        return f"{self.emp.emp_id} - Attrition on {self.exit_date}"
