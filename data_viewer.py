import dtale
import pandas as pd

# Load your CSV file
df = pd.read_csv("cleaned_zoo_accreditations.csv")

# Launch D-Tale in your browser
d = dtale.show(df, open_browser=True)

print("D-Tale URL:", d._url)
input("Press Enter to stop the D-Tale server...")