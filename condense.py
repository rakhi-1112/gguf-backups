import datetime
import pandas as pd
import re

class CondenseDataset:
    def __init__(self, input_df, sample_size=10):
        self.__input_df = input_df
        self.sample_size = min(sample_size, len(input_df))  # Limit sample size
        self.condensed_df = None

    def preprocess_data(self):
        """ Analyzes sample rows and removes unnecessary columns. """
        df_cleaned = self.__input_df.copy()

        # Take a sample to analyze patterns
        sample_df = df_cleaned.sample(self.sample_size, random_state=42)

        # Drop columns that are completely empty
        df_cleaned = df_cleaned.dropna(axis=1, how='all')

        def is_primary_key(col):
            """ Identifies if a column is an ID or a primary key based on sample analysis. """
            if sample_df[col].nunique() == len(sample_df):  # Each row has a unique value
                return True  
            if re.search(r'\b(id|uuid|code|identifier|ric|isin)\b', col, re.IGNORECASE):
                return True  
            return False

        def is_binary_column(col):
            """ Checks if a column contains only 'Y' or 'N' values in the sample. """
            return sample_df[col].dropna().astype(str).str.match(r'^[YNyn]$').all()

        # Identify columns to remove
        remove_columns = [col for col in sample_df.columns if is_primary_key(col) or is_binary_column(col)]

        # Keep only relevant columns (dates, free-text, and non-ID numerical columns)
        kept_columns = [col for col in df_cleaned.columns if col not in remove_columns]

        # Save the condensed DataFrame
        self.condensed_df = df_cleaned[kept_columns]

    def save_to_excel(self):
        """ Saves the condensed dataset to an Excel file. """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"condensed_dataset_{timestamp}.xlsx"
        self.condensed_df.to_excel(filename, index=False)
        return filename

def main():
    """ Main function to process and save the condensed dataset. """
    input_df = pd.read_excel("Dataset.xlsx", sheet_name="Sheet1")

    processor = CondenseDataset(input_df=input_df, sample_size=10)
    processor.preprocess_data()
    filename = processor.save_to_excel()

    print(f"Condensed dataset saved as: {filename}")

if __name__ == '__main__':
    main()
