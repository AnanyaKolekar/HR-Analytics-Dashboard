"""
Django management command to generate sample HR data.

Usage:
    python manage.py generate_sample_data

This command generates:
- Departments
- Employees (5-10 per department)
- Attendance records (random but valid)
- Leave records
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random

from hr.models import Employee, Attendance, LeaveRecord, AttritionRecord


class Command(BaseCommand):
    help = 'Generate sample HR data for testing and demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before generating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            AttritionRecord.objects.all().delete()
            LeaveRecord.objects.all().delete()
            Attendance.objects.all().delete()
            Employee.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # Generate departments
        departments = [
            'Engineering',
            'Sales',
            'Marketing',
            'HR',
            'Finance',
            'Operations',
            'Product',
            'Support'
        ]

        # First names and last names for generating employee names
        first_names = [
            'Ananya', 'Raj', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Kavya', 'Rohan',
            'Meera', 'Arjun', 'Divya', 'Siddharth', 'Anjali', 'Karan', 'Neha', 'Rahul',
            'Shreya', 'Aditya', 'Pooja', 'Vivek', 'Riya', 'Sahil', 'Aishwarya', 'Manish',
            'Kritika', 'Nikhil', 'Tanvi', 'Harsh', 'Isha', 'Yash', 'Sanya', 'Varun',
            'Anika', 'Rishabh', 'Aarushi', 'Kunal', 'Maya', 'Abhishek', 'Zara', 'Ravi'
        ]
        
        last_names = [
            'Sharma', 'Patel', 'Kumar', 'Singh', 'Gupta', 'Verma', 'Reddy', 'Mehta',
            'Joshi', 'Shah', 'Malhotra', 'Agarwal', 'Nair', 'Rao', 'Iyer', 'Menon',
            'Chopra', 'Kapoor', 'Bansal', 'Goyal', 'Saxena', 'Tiwari', 'Mishra', 'Pandey'
        ]

        # Leave types
        leave_types = ['sick', 'annual', 'casual', 'unpaid', 'maternity']

        employees_created = 0
        attendance_created = 0
        leaves_created = 0

        # Generate employees for each department
        for dept in departments:
            # Random number of employees per department (5-10)
            num_employees = random.randint(5, 10)
            
            self.stdout.write(f'Creating {num_employees} employees for {dept}...')
            
            for i in range(num_employees):
                # Generate employee ID
                emp_id = f"{dept[:3].upper()}{1000 + employees_created:04d}"
                
                # Generate name
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                name = f"{first_name} {last_name}"
                
                # Generate join date (random date in last 2 years)
                days_ago = random.randint(30, 730)
                join_date = date.today() - timedelta(days=days_ago)
                
                # Create employee
                employee, created = Employee.objects.get_or_create(
                    emp_id=emp_id,
                    defaults={
                        'name': name,
                        'department': dept,
                        'join_date': join_date,
                        'status': 'active'
                    }
                )
                
                if created:
                    employees_created += 1
                    
                    # Generate attendance records for last 90 days
                    attendance_start = date.today() - timedelta(days=90)
                    current_date = attendance_start
                    
                    while current_date <= date.today():
                        # Skip weekends (Saturday=5, Sunday=6)
                        if current_date.weekday() < 5:  # Monday to Friday
                            # Random attendance status (85% present, 10% absent, 5% half-day)
                            rand = random.random()
                            if rand < 0.85:
                                status = 'present'
                            elif rand < 0.95:
                                status = 'absent'
                            else:
                                status = 'half-day'
                            
                            Attendance.objects.get_or_create(
                                emp=employee,
                                date=current_date,
                                defaults={'status': status}
                            )
                            attendance_created += 1
                        
                        current_date += timedelta(days=1)
                    
                    # Generate leave records (1-3 leaves per employee)
                    num_leaves = random.randint(1, 3)
                    for _ in range(num_leaves):
                        # Random leave start date in last 6 months
                        leave_start_days_ago = random.randint(1, 180)
                        leave_start = date.today() - timedelta(days=leave_start_days_ago)
                        
                        # Leave duration (1-5 days)
                        duration = random.randint(1, 5)
                        leave_end = leave_start + timedelta(days=duration - 1)
                        
                        # Ensure end date is not in future
                        if leave_end > date.today():
                            leave_end = date.today()
                            duration = (leave_end - leave_start).days + 1
                        
                        # Random leave type
                        leave_type = random.choice(leave_types)
                        
                        # 90% approved, 10% pending
                        approved = random.random() < 0.9
                        
                        LeaveRecord.objects.create(
                            emp=employee,
                            leave_type=leave_type,
                            start_date=leave_start,
                            end_date=leave_end,
                            duration=duration,
                            reason=f'Sample {leave_type} leave',
                            approved=approved
                        )
                        leaves_created += 1
        
        # Generate some attrition records (5-10% of employees)
        active_employees = list(Employee.objects.filter(status='active'))
        num_attrition = max(1, int(len(active_employees) * random.uniform(0.05, 0.10)))
        
        if num_attrition > 0:
            self.stdout.write(f'Creating {num_attrition} attrition records...')
            employees_to_exit = random.sample(active_employees, min(num_attrition, len(active_employees)))
            
            exit_reasons = ['voluntary', 'terminated', 'retired', 'laid_off', 'other']
            
            for employee in employees_to_exit:
                # Exit date in last 6 months
                exit_days_ago = random.randint(1, 180)
                exit_date = date.today() - timedelta(days=exit_days_ago)
                
                reason = random.choice(exit_reasons)
                
                # Mark employee as inactive
                employee.status = 'inactive'
                employee.save()
                
                # Create attrition record
                AttritionRecord.objects.create(
                    emp=employee,
                    exit_date=exit_date,
                    reason=reason,
                    details=f'Sample {reason} exit'
                )

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Sample data generation completed!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Departments: {len(departments)}')
        self.stdout.write(f'Employees created: {employees_created}')
        self.stdout.write(f'Attendance records created: {attendance_created}')
        self.stdout.write(f'Leave records created: {leaves_created}')
        self.stdout.write(f'Attrition records created: {num_attrition}')
        self.stdout.write(self.style.SUCCESS('='*50))

