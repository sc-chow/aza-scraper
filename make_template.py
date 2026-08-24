import pandas as pd

# Load your raw data
df = pd.read_csv('aza_accredited_facilities.csv')

# Clean up names
df['name'] = df['name'].astype(str).str.strip().str.rstrip(',')

# Get all unique zoo names
unique_names = df['name'].unique()

# Create the template DataFrame with a blank city column
template_df = pd.DataFrame({
    'name': unique_names,
    'city': ''
})

# Save it as zoo_cities.csv
template_df.to_csv('zoo_cities.csv', index=False)
print("SUCCESS: 'zoo_cities.csv' has been created with all your zoo names!")