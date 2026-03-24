import pdfplumber
import pandas as pd

pdf_path = r"d:\urbanblack-aiml\PricingNRevenue\LongTripOpt\dataset - Sheet1.pdf"

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            df = pd.DataFrame(table[1:], columns=table[0])  # Assuming first row is header
            print(df.head(10))  # Print first 10 rows
            df.to_csv("extracted_dataset.csv", index=False)
            break  # Assuming one table
        break  # First page