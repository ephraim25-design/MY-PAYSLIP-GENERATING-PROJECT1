import pandas as pd
from fpdf import FPDF
import yagmail
import os
from dotenv import load_dotenv
from typing import Dict, Any

class PayslipGenerator:
    def __init__(self):
        load_dotenv()
        self.EMAIL = os.getenv("EMAIL")
        self.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

        self.yag = yagmail.SMTP(self.EMAIL, self.EMAIL_PASSWORD)
        self.OUTPUT_DIR = "payslips"
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

        self.REQUIRED_COLUMNS = [
            'Employee Id', 'Name', 'Email',
            'Basic Salary', 'Allowances', 'Deductions'
        ]

    def validate_excel_file(self, file_path: str) -> pd.DataFrame:
        try:
            df = pd.read_excel("employees.xlsx")
            df.columns = df.columns.str.strip().str.title()

            missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing:
                raise ValueError(f"Missing columns: {', '.join(missing)}")
            return df
        except Exception as e:
            print(f"Error reading file: {e}")
            exit()

    def calculate_net_salary(self, row: pd.Series) -> float:
        return row['Basic Salary'] + row['Allowances'] - row['Deductions']

    def create_payslip(self, employee_data: Dict[str, Any]) -> str:
        pdf = FPDF()
        pdf.add_page()

        # Background color
        pdf.set_fill_color(248, 239, 231)  # Beige
        pdf.rect(0, 0, 210, 297, 'F')

        # Header
        pdf.set_font("Helvetica", 'B', 28)
        pdf.set_text_color(138, 51, 36)  # Brown
        pdf.cell(0, 15, "Payslip", ln=True, align='C')

        pdf.set_font("Helvetica", size=16)
        pdf.cell(0, 10, "Creative Studios Inc.", ln=True, align='C')
        pdf.ln(10)

        # Employee Info
        pdf.set_text_color(88, 44, 33)
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(0, 10, "Billed To:", ln=True)
        pdf.set_font("Helvetica", size=11)
        pdf.cell(0, 8, f"Employee ID: {employee_data['Employee Id']}", ln=True)
        pdf.cell(0, 8, f"Name: {employee_data['Name']}", ln=True)
        pdf.cell(0, 8, f"Email: {employee_data['Email']}", ln=True)
        pdf.ln(5)

        # Salary Table
        table_data = [
            ("Basic Salary", f"${employee_data['Basic Salary']:.2f}"),
            ("Allowances", f"${employee_data['Allowances']:.2f}"),
            ("Deductions", f"${employee_data['Deductions']:.2f}"),
            ("Net Salary", f"${employee_data['net_salary']:.2f}")
        ]

        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_fill_color(138, 51, 36)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(95, 10, "CATEGORY", 1, 0, 'C', True)
        pdf.cell(95, 10, "AMOUNT", 1, 1, 'C', True)

        pdf.set_text_color(88, 44, 33)
        pdf.set_font("Helvetica", size=11)

        for label, value in table_data:
            pdf.cell(95, 10, label, 1)
            pdf.cell(95, 10, value, 1, ln=True)

        # Footer
        pdf.ln(15)
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(138, 51, 36)
        pdf.cell(0, 10, "Thank you", ln=True, align='C')

        # Save file
        pdf_path = f"{self.OUTPUT_DIR}/{employee_data['Employee Id']}.pdf"
        pdf.output(pdf_path)
        return pdf_path

    def send_payslip(self, email: str, name: str, pdf_path: str) -> None:
        try:
            self.yag.send(
                to=email,
                subject="Your Monthly Payslip",
                contents=f"Dear {name},\n\nPlease find attached your payslip for this month.\n\nBest regards,\nCreative Studios Inc.",
                attachments=pdf_path
            )
            print(f"Sent payslip to {email}")
        except Exception as e:
            print(f"Failed to send to {email}: {str(e)}")

    def process_all_employees(self, excel_file: str) -> None:
        df = self.validate_excel_file(excel_file)
        for _, row in df.iterrows():
            employee_data = dict(row)
            employee_data['net_salary'] = self.calculate_net_salary(row)
            pdf_path = self.create_payslip(employee_data)
            self.send_payslip(
                email=employee_data['Email'],
                name=employee_data['Name'],
                pdf_path=pdf_path
            )

if __name__ == "__main__":
    generator = PayslipGenerator()
    generator.process_all_employees("employees.xlsx")
