import pandas as pd
import dtale
import os

# 1. Load the raw data
df = pd.read_csv('aza_accredited_facilities.csv')

# 2. String Cleaning across all text columns
text_cols = ['name', 'location', 'website', 'accredited_through', 'section']
df[text_cols] = df[text_cols].apply(lambda col: col.astype(str).str.strip())
df['name'] = df['name'].str.rstrip(',')

# 3. Comprehensive US State Mapping
us_states = {
    'Alabama': 'AL', 'Ala.': 'AL', 'AL': 'AL',
    'Alaska': 'AK', 'AK': 'AK',
    'Arizona': 'AZ', 'Ariz.': 'AZ', 'AZ': 'AZ',
    'Arkansas': 'AR', 'Ark.': 'AR', 'AR': 'AR',
    'California': 'CA', 'Calif.': 'CA', 'CA': 'CA',
    'Colorado': 'CO', 'Colo.': 'CO', 'CO': 'CO',
    'Connecticut': 'CT', 'Conn.': 'CT', 'CT': 'CT',
    'Delaware': 'DE', 'Del.': 'DE', 'DE': 'DE',
    'District of Columbia': 'DC', 'D.C.': 'DC', 'DC': 'DC',
    'Florida': 'FL', 'Fla.': 'FL', 'FL': 'FL',
    'Georgia': 'GA', 'Ga.': 'GA', 'GA': 'GA',
    'Hawaii': 'HI', 'HI': 'HI',
    'Idaho': 'ID', 'ID': 'ID',
    'Illinois': 'IL', 'Ill.': 'IL', 'IL': 'IL',
    'Indiana': 'IN', 'Ind.': 'IN', 'IN': 'IN',
    'Iowa': 'IA', 'IA': 'IA',
    'Kansas': 'KS', 'Kan.': 'KS', 'KS': 'KS',
    'Kentucky': 'KY', 'Ky.': 'KY', 'KY': 'KY',
    'Louisiana': 'LA', 'La.': 'LA', 'LA': 'LA',
    'Maine': 'ME', 'ME': 'ME',
    'Maryland': 'MD', 'Md.': 'MD', 'MD': 'MD',
    'Massachusetts': 'MA', 'Mass.': 'MA', 'MA': 'MA',
    'Michigan': 'MI', 'Mich.': 'MI', 'MI': 'MI',
    'Minnesota': 'MN', 'Minn.': 'MN', 'MN': 'MN',
    'Mississippi': 'MS', 'Miss.': 'MS', 'MS': 'MS',
    'Missouri': 'MO', 'Mo.': 'MO', 'MO': 'MO',
    'Montana': 'MT', 'Mont.': 'MT', 'MT': 'MT',
    'Nebraska': 'NE', 'Neb.': 'NE', 'NE': 'NE',
    'Nevada': 'NV', 'Nev.': 'NV', 'NV': 'NV',
    'New Hampshire': 'NH', 'N.H.': 'NH', 'NH': 'NH',
    'New Jersey': 'NJ', 'N.J.': 'NJ', 'NJ': 'NJ',
    'New Mexico': 'NM', 'N.M.': 'NM', 'NM': 'NM',
    'New York': 'NY', 'N.Y.': 'NY', 'NY': 'NY',
    'North Carolina': 'NC', 'N.C.': 'NC', 'NC': 'NC',
    'North Dakota': 'ND', 'N.D.': 'ND', 'ND': 'ND',
    'Ohio': 'OH', 'OH': 'OH',
    'Oklahoma': 'OK', 'Okla.': 'OK', 'OK': 'OK',
    'Oregon': 'OR', 'Ore.': 'OR', 'OR': 'OR',
    'Pennsylvania': 'PA', 'Pa.': 'PA', 'Penn.': 'PA', 'PA': 'PA',
    'Rhode Island': 'RI', 'R.I.': 'RI', 'RI': 'RI',
    'South Carolina': 'SC', 'S.C.': 'SC', 'SC': 'SC',
    'South Dakota': 'SD', 'S.D.': 'SD', 'SD': 'SD',
    'Tennessee': 'TN', 'Tenn.': 'TN', 'TN': 'TN',
    'Texas': 'TX', 'TX': 'TX', 'Inc. Texas': 'TX',
    'Utah': 'UT', 'UT': 'UT',
    'Vermont': 'VT', 'VT': 'VT',
    'Virginia': 'VA', 'Va.': 'VA', 'VA': 'VA',
    'Washington': 'WA', 'Wash.': 'WA', 'WA': 'WA',
    'West Virginia': 'WV', 'W.Va.': 'WV', 'WV': 'WV',
    'Wisconsin': 'WI', 'Wis.': 'WI', 'WI': 'WI',
    'Wyoming': 'WY', 'Wyo.': 'WY', 'WY': 'WY',
}

# Map US state codes first
df['state_province'] = df['location'].map(us_states)

# Determine Country
df['country'] = df['state_province'].apply(lambda x: 'USA' if pd.notna(x) else None).fillna(df['location'])

# 4. Automatically load city mapping from a separate CSV file if it exists
if os.path.exists('zoo_cities.csv'):
    city_df = pd.read_csv('zoo_cities.csv')
    city_df['name'] = city_df['name'].str.strip()
    city_df['city'] = city_df['city'].str.strip()
    # Merge the city data based on the zoo name
    df = df.merge(city_df[['name', 'city']], on='name', how='left')
    df['city'] = df['city'].fillna("")
else:
    df['city'] = ""
    print("⚠️ Notice: 'zoo_cities.csv' not found. City column initialized as blank.")

# 5. Parse Dates to Standard Datetime (End of Month)
df['accreditation_expiry_date'] = pd.to_datetime(
    df['accredited_through'], format='%B %Y'
) + pd.offsets.MonthEnd(1)

# 6. Reorder and Select Final Clean Columns
df_clean = df[[
    'name',
    'city',
    'state_province',
    'country',
    'website',
    'accreditation_expiry_date',
    'also_aam_accredited',
    'section',
]]

# 7. Export Cleaned Dataset
output_file = 'cleaned_zoo_accreditations.csv'
df_clean.to_csv(output_file, index=False)
print(f"Pipeline complete! Saved cleaned data to {output_file}")

# 8. Launch D-Tale viewer
print("Launching D-Tale interactive viewer...")
d = dtale.show(df_clean, open_browser=True)
print("D-Tale URL:", d._url)

input("Press Enter to stop the D-Tale server...")