import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv('divorce_survey.csv')

# Display initial info
print("Initial data shape:", df.shape)
print("\nColumns with missing values:")
print(df.isnull().sum()[df.isnull().sum() > 0])
print("\nAnnual_Income sample:", df['Annual_Income'].head(5).tolist())
print("Change_In_Income_After_Divorce sample:", df['Change_In_Income_After_Divorce'].head(5).tolist())

# Step 1: Normalize Annual_Income into numbers
def clean_income(value):
    if pd.isna(value):
        return np.nan
    
    # Convert to string and clean
    value_str = str(value).strip()
    
    # Remove dollar signs, commas, and 'USD'
    value_str = value_str.replace('$', '').replace(',', '').replace('USD', '').replace(' ', '')
    
    # Remove 'k' and multiply by 1000
    if 'k' in value_str.lower():
        value_str = value_str.lower().replace('k', '')
        try:
            return float(value_str) * 1000
        except:
            return np.nan
    
    # Try to convert to float
    try:
        return float(value_str)
    except:
        return np.nan

df['Annual_Income_Clean'] = df['Annual_Income'].apply(clean_income)

# Step 2: Parse Change_In_Income_After_Divorce into usable values
def parse_income_change(value):
    if pd.isna(value):
        return np.nan
    
    value_str = str(value).strip().lower()
    
    # Handle percentage changes
    if '%' in value_str:
        try:
            # Remove % and convert to decimal
            percent = float(value_str.replace('%', '').replace(' ', ''))
            return percent / 100  # Return as decimal (0.10 for 10%)
        except:
            return np.nan
    
    # Handle dollar amount changes (up/down Xk)
    if any(x in value_str for x in ['up', 'down']):
        try:
            # Extract the number
            num_str = value_str.replace('up', '').replace('down', '').replace(' ', '').replace('k', '')
            amount = float(num_str) * 1000  # Convert k to actual dollars
            
            # Apply direction
            if 'down' in value_str:
                return -amount
            else:
                return amount
        except:
            return np.nan
    
    # Handle simple dollar amounts
    try:
        # Remove any non-numeric characters except minus sign
        clean_str = ''.join([c for c in value_str if c.isdigit() or c == '-' or c == '.'])
        if clean_str and clean_str != '-':
            return float(clean_str)
        else:
            return np.nan
    except:
        return np.nan

df['Income_Change_Amount'] = df['Change_In_Income_After_Divorce'].apply(parse_income_change)

# Step 3 & 4: Compute New_Annual_Income
def calculate_new_income(row):
    if pd.isna(row['Annual_Income_Clean']) or pd.isna(row['Income_Change_Amount']):
        return np.nan
    
    change = row['Income_Change_Amount']
    
    # If change is a percentage (between -1 and 1, or between -100 and 100)
    if abs(change) <= 1 or (abs(change) <= 100 and abs(change) > 1):
        # Assume it's percentage if <= 1, otherwise scale down
        if abs(change) > 1:
            change = change / 100
        return row['Annual_Income_Clean'] * (1 + change)
    
    # If change is a dollar amount
    else:
        return row['Annual_Income_Clean'] + change

df['New_Annual_Income'] = df.apply(calculate_new_income, axis=1)

# Step 5: Run diagnostics
print("\n" + "="*50)
print("DIAGNOSTICS REPORT")
print("="*50)

# Check conversion success rates
income_success = df['Annual_Income_Clean'].notna().sum()
change_success = df['Income_Change_Amount'].notna().sum()
new_income_success = df['New_Annual_Income'].notna().sum()

print(f"Annual_Income conversion success: {income_success}/{len(df)} ({income_success/len(df)*100:.1f}%)")
print(f"Income change conversion success: {change_success}/{len(df)} ({change_success/len(df)*100:.1f}%)")
print(f"New income calculation success: {new_income_success}/{len(df)} ({new_income_success/len(df)*100:.1f}%)")

# Show problematic rows
print("\nRows with conversion issues:")
problem_rows = df[df['New_Annual_Income'].isna()]
if not problem_rows.empty:
    for idx, row in problem_rows.iterrows():
        print(f"Row {idx}: Income='{row['Annual_Income']}', Change='{row['Change_In_Income_After_Divorce']}'")
else:
    print("All rows successfully processed!")

# Show sample of successful conversions
print("\nSample of successful conversions:")
success_rows = df[df['New_Annual_Income'].notna()].head(3)
for idx, row in success_rows.iterrows():
    print(f"Row {idx}: ${row['Annual_Income_Clean']:,.0f} -> {row['Change_In_Income_After_Divorce']} -> ${row['New_Annual_Income']:,.0f}")

# Summary statistics
print(f"\nSummary statistics:")
print(f"Original income range: ${df['Annual_Income_Clean'].min():,.0f} - ${df['Annual_Income_Clean'].max():,.0f}")
print(f"New income range: ${df['New_Annual_Income'].min():,.0f} - ${df['New_Annual_Income'].max():,.0f}")
print(f"Average change: ${(df['New_Annual_Income'] - df['Annual_Income_Clean']).mean():,.0f}")

# Display final dataframe with new columns
print(f"\nFinal dataframe shape: {df.shape}")
print("\nNew columns added:")
new_cols = ['Annual_Income_Clean', 'Income_Change_Amount', 'New_Annual_Income']
print(df[new_cols].head(10))