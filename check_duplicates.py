import pandas as pd

employees = pd.read_excel("data/Employees.xlsx")

# Find duplicate EmployeeIDs
duplicates = employees[employees.duplicated(subset=["EmployeeID"], keep=False)]

print(f"Total duplicate rows found: {len(duplicates)}")
print(duplicates.sort_values("EmployeeID"))