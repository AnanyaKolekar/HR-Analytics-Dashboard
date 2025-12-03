
from django.core.exceptions import ValidationError
from datetime import datetime, date
import re


class DataValidator:
    @staticmethod
    def validate_date_range(start_date, end_date):
     
        if not start_date or not end_date:
            return True, None

        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return False, "Invalid date format. Use YYYY-MM-DD"

        if start > end:
            return False, "Start date must be before end date"

        # Check if range is reasonable (within 5 years)
        days_diff = (end - start).days
        if days_diff > 1825:  # ~5 years
            return False, "Date range cannot exceed 5 years"

        return True, None

    @staticmethod
    def validate_department(department, valid_departments):
      
        if not department:
            return True, None

        if department not in valid_departments:
            return False, f"Invalid department: {department}"

        return True, None

    @staticmethod
    def validate_employee_data(emp_id, name, department, join_date):
        """Validate employee master data"""
        errors = []

        if not emp_id or len(emp_id.strip()) == 0:
            errors.append("Employee ID is required")
        elif not re.match(r'^[A-Z0-9-]+$', emp_id):
            errors.append("Employee ID must contain only uppercase letters, numbers, and hyphens")

        if not name or len(name.strip()) == 0:
            errors.append("Employee name is required")
        elif len(name) > 100:
            errors.append("Employee name must be less than 100 characters")

        if not department or len(department.strip()) == 0:
            errors.append("Department is required")

        try:
            join_dt = datetime.strptime(join_date, '%Y-%m-%d').date()
            if join_dt > date.today():
                errors.append("Join date cannot be in the future")
        except ValueError:
            errors.append("Invalid join date format")

        return len(errors) == 0, errors

    @staticmethod
    def validate_attendance_data(emp_id, attendance_date, status):
        """Validate attendance record data"""
        errors = []

        if not emp_id:
            errors.append("Employee ID is required")

        try:
            att_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
            if att_date > date.today():
                errors.append("Attendance date cannot be in the future")
        except ValueError:
            errors.append("Invalid attendance date format")

        valid_statuses = ['present', 'absent', 'half-day']
        if status not in valid_statuses:
            errors.append(f"Status must be one of: {', '.join(valid_statuses)}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_leave_data(emp_id, leave_type, start_date, end_date, duration):
        """Validate leave record data"""
        errors = []

        if not emp_id:
            errors.append("Employee ID is required")

        valid_types = ['sick', 'annual', 'casual', 'unpaid', 'maternity']
        if leave_type not in valid_types:
            errors.append(f"Leave type must be one of: {', '.join(valid_types)}")

        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()

            if start > end:
                errors.append("Start date must be before end date")

            if start > date.today():
                errors.append("Leave start date cannot be in the future")

        except ValueError:
            errors.append("Invalid date format for leave dates")

        try:
            dur = int(duration)
            if dur <= 0:
                errors.append("Duration must be a positive integer")
            elif dur > 365:
                errors.append("Leave duration cannot exceed 365 days")
        except ValueError:
            errors.append("Duration must be a valid integer")

        return len(errors) == 0, errors

    @staticmethod
    def validate_attrition_data(emp_id, exit_date, reason):
        """Validate attrition record data"""
        errors = []

        if not emp_id:
            errors.append("Employee ID is required")

        try:
            exit_dt = datetime.strptime(exit_date, '%Y-%m-%d').date()
            if exit_dt > date.today():
                errors.append("Exit date cannot be in the future")
        except ValueError:
            errors.append("Invalid exit date format")

        valid_reasons = ['voluntary', 'terminated', 'retired', 'laid_off', 'other']
        if reason not in valid_reasons:
            errors.append(f"Reason must be one of: {', '.join(valid_reasons)}")

        return len(errors) == 0, errors


class ErrorHandler:
    """Handle and format errors for API responses"""

    @staticmethod
    def format_validation_error(errors):
        """Format validation errors for JSON response"""
        return {
            'success': False,
            'error': 'Validation failed',
            'details': errors
        }

    @staticmethod
    def format_error(message, status_code=400):
        """Format generic error for JSON response"""
        return {
            'success': False,
            'error': message,
            'status_code': status_code
        }

    @staticmethod
    def format_success(data=None, message='Success'):
        """Format success response"""
        return {
            'success': True,
            'message': message,
            'data': data
        }
