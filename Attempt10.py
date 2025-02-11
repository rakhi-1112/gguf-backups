import datetime
import pandas as pd
from gpt4all import GPT4All
import json
import math

class DataClassifier:
    def __init__(self):
        self.__model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", model_path='./', allow_download=False, n_ctx=8192)

    def classify_dataset(self, df):
        columns = df.columns.tolist()
        sample_data = df.sample(min(5, len(df)), random_state=42).to_dict(orient="records")

        prompt = f"""
        Classify the following dataset based on its content:
        - Financial Data (transactions, account balances, revenues, invoices)
        - Customer Data (names, emails, phone numbers, addresses)
        - Other Data (if it doesn’t fit the above)

        Dataset details:
        Columns: {columns}
        Sample Data: {sample_data}

        Return only the category name.
        """

        response = self.__model.generate(prompt)
        return response.strip()


class FinancialDataPreprocessor:
    def __init__(self):
        self.__columns = []
        self.__model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", model_path='./', allow_download=False, n_ctx=8192)
        self.__base_prompt = '''
        Given dataset headers and one row, identify financial columns to keep while discarding:
        - IDs (e.g., transaction IDs, CUSIP)
        - Binary columns (Yes/No, Y/N)
        - Redundant or irrelevant fields

        Keep columns containing:
        - Dates and timestamps
        - Monetary values
        - Descriptions of financial transactions

        Return a JSON list of relevant column names.
        '''

    def preprocess_data(self, df):
        column_names = json.dumps(df.columns.tolist(), indent=4)
        row = json.dumps(df.sample(1, random_state=42).values.tolist()[0], indent=4)

        prompt = f"{self.__base_prompt}\nColumns: {column_names}\nSample Row: {row}\n"
        
        with self.__model.chat_session():
            response = self.__model.generate(prompt, max_tokens=512)
        
        try:
            retained_columns = json.loads(response)
            if isinstance(retained_columns, list):
                return df[retained_columns]
        except json.JSONDecodeError:
            return df  # Fallback: return original data if parsing fails


class FinancialSyntheticDataGenerator:
    def __init__(self, input_df, n_synthetic_rows=10):
        self.__model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", model_path='./', allow_download=False, n_ctx=8192)
        self.__input_df = input_df
        self.__n_synthetic_rows = n_synthetic_rows
        self.generated_df = None

    def generate_synthetic_data(self):
        column_names = json.dumps(self.__input_df.columns.tolist(), indent=4)
        sample_data = json.dumps(self.__input_df.sample(5, random_state=42).values.tolist(), indent=4)

        prompt = f"""
        Generate {self.__n_synthetic_rows} new rows of financial data.
        - Ensure values are **not present** in the original dataset.
        - Retain the **format, meaning, and patterns** of existing data.

        Columns: {column_names}
        Sample Data: {sample_data}

        Return only the new rows in JSON format.
        """

        with self.__model.chat_session():
            response = self.__model.generate(prompt, max_tokens=self.__n_synthetic_rows * 1024)

        try:
            synthetic_rows = json.loads(response)
            if isinstance(synthetic_rows, list):
                self.generated_df = pd.DataFrame(synthetic_rows, columns=self.__input_df.columns)
        except json.JSONDecodeError:
            self.generated_df = self.__input_df.sample(self.__n_synthetic_rows, replace=True)  # Fallback


def save_dataframe_to_excel(df):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"synthetic_financial_data_{timestamp}.xlsx"
    df.to_excel(filename, index=False)
    return filename


def main():
    df = pd.read_excel("Dataset.xlsx", sheet_name="Sheet1")

    classifier = DataClassifier()
    dataset_type = classifier.classify_dataset(df)
    print(f"Dataset Type: {dataset_type}")

    if "Financial" not in dataset_type:
        print("Dataset is not financial. Exiting.")
        return

    processor = FinancialDataPreprocessor()
    processed_df = processor.preprocess_data(df)

    generator = FinancialSyntheticDataGenerator(processed_df, n_synthetic_rows=10)
    generator.generate_synthetic_data()

    synthetic_df = generator.generated_df
    if synthetic_df is not None:
        save_dataframe_to_excel(synthetic_df)
        print("Synthetic financial data saved.")

if __name__ == '__main__':
    main()
