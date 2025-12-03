
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO
import base64
from datetime import date, timedelta


matplotlib.use('Agg')


class ChartGenerator:
    @staticmethod
    def _figure_to_base64(fig):
        """Converts matplotlib figure to base64 image string"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return image_base64

    @staticmethod
    def generate_attendance_chart(dept_attendance_data):
       
        try:
            departments = list(dept_attendance_data.keys())
            percentages = [dept_attendance_data[d]['percentage'] for d in departments]

            fig, ax = plt.subplots(figsize=(10, 6))

            # Color bars based on attendance percentage
            colors = ['#22c55e' if p >= 80 else '#f59e0b' if p >= 70 else '#ef4444' for p in percentages]

            bars = ax.bar(departments, percentages, color=colors, edgecolor='#1f2937', linewidth=1.5)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')

            ax.set_ylabel('Attendance %', fontsize=12, fontweight='bold')
            ax.set_xlabel('Department', fontsize=12, fontweight='bold')
            ax.set_title('Departmental Attendance Overview', fontsize=14, fontweight='bold')
            ax.set_ylim(0, 105)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            return ChartGenerator._figure_to_base64(fig)

        except Exception as e:
            print(f"Error generating attendance chart: {e}")
            return None

    @staticmethod
    def generate_leave_chart(leave_distribution_data):
      
        try:
            if not leave_distribution_data:
                return None

            leave_types = [item['leave_type'] for item in leave_distribution_data]
            counts = [item['count'] for item in leave_distribution_data]

            fig, ax = plt.subplots(figsize=(10, 6))

            colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']
            colors = colors[:len(leave_types)]

            wedges, texts, autotexts = ax.pie(
                counts,
                labels=leave_types,
                autopct='%1.1f%%',
                colors=colors,
                startangle=90,
                textprops={'fontsize': 11, 'fontweight': 'bold'}
            )

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            ax.set_title('Leave Type Distribution', fontsize=14, fontweight='bold')

            plt.tight_layout()

            return ChartGenerator._figure_to_base64(fig)

        except Exception as e:
            print(f"[v0] Error generating leave chart: {e}")
            return None

    @staticmethod
    def generate_attrition_chart(dept_attrition_data):
     
        try:
            departments = list(dept_attrition_data.keys())
            attrition_rates = [dept_attrition_data[d]['attrition_rate'] for d in departments]

            fig, ax = plt.subplots(figsize=(10, 6))

            # Color bars based on attrition rate (lower is better)
            colors = ['#10b981' if r <= 5 else '#f59e0b' if r <= 10 else '#ef4444' for r in attrition_rates]

            bars = ax.bar(departments, attrition_rates, color=colors, edgecolor='#1f2937', linewidth=1.5)

            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')

            ax.set_ylabel('Attrition Rate %', fontsize=12, fontweight='bold')
            ax.set_xlabel('Department', fontsize=12, fontweight='bold')
            ax.set_title('Departmental Attrition Rates', fontsize=14, fontweight='bold')
            ax.set_ylim(0, max(attrition_rates) * 1.15 if attrition_rates else 15)
            ax.grid(axis='y', alpha=0.3, linestyle='--')

            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            return ChartGenerator._figure_to_base64(fig)

        except Exception as e:
            print(f"Error generating attrition chart: {e}")
            return None

    @staticmethod
    def generate_summary_chart(summary_data):
      
        try:
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))

            # Total Employees
            total_emp = summary_data.get('total_employees', 0)
            ax1.text(0.5, 0.5, str(total_emp), ha='center', va='center', fontsize=48, fontweight='bold')
            ax1.text(0.5, 0.15, 'Total Employees', ha='center', va='center', fontsize=12)
            ax1.set_xlim(0, 1)
            ax1.set_ylim(0, 1)
            ax1.axis('off')
            ax1.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, edgecolor='#3b82f6', linewidth=2))

            # Attendance
            attendance_pct = summary_data.get('attendance', {}).get('attendance_percentage', 0)
            color = '#10b981' if attendance_pct >= 80 else '#f59e0b' if attendance_pct >= 70 else '#ef4444'
            ax2.text(0.5, 0.5, f'{attendance_pct:.1f}%', ha='center', va='center', fontsize=48, fontweight='bold', color=color)
            ax2.text(0.5, 0.15, 'Attendance Rate', ha='center', va='center', fontsize=12)
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)
            ax2.axis('off')
            ax2.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, edgecolor=color, linewidth=2))

            # Total Leaves
            total_leaves = summary_data.get('leaves', {}).get('total_leaves', 0)
            ax3.text(0.5, 0.5, str(total_leaves), ha='center', va='center', fontsize=48, fontweight='bold')
            ax3.text(0.5, 0.15, 'Total Leaves', ha='center', va='center', fontsize=12)
            ax3.set_xlim(0, 1)
            ax3.set_ylim(0, 1)
            ax3.axis('off')
            ax3.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, edgecolor='#8b5cf6', linewidth=2))

            # Attrition Rate
            attrition = summary_data.get('attrition', {}).get('attrition_rate', 0)
            color = '#10b981' if attrition <= 5 else '#f59e0b' if attrition <= 10 else '#ef4444'
            ax4.text(0.5, 0.5, f'{attrition:.1f}%', ha='center', va='center', fontsize=48, fontweight='bold', color=color)
            ax4.text(0.5, 0.15, 'Attrition Rate', ha='center', va='center', fontsize=12)
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
            ax4.add_patch(plt.Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, edgecolor=color, linewidth=2))

            fig.suptitle('HR Dashboard Summary', fontsize=16, fontweight='bold')
            plt.tight_layout()

            return ChartGenerator._figure_to_base64(fig)

        except Exception as e:
            print(f"Error generating summary chart: {e}")
            return None
