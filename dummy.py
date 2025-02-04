import datetime
import pandas as pd
import json
from gpt4all import GPT4All

class CondenseDataset:
    def __init__(self, input_file, sheet_name="Sheet1", model_name="Meta-Llama-3-8B-Instruct.Q4_0.gguf", sample_size=10, max_tokens=8192):
        self.__model = GPT4All(model_name=model_name, model_path="./", allow_download=False, n_ctx=max_tokens)
        self.input_file = input_file
        self.sheet_name = sheet_name
        self.sample_size = sample_size
        self.max_tokens = max_tokens
        self.condensed_df = None

    def load_data(self):
        """ Loads the dataset from an Excel file. """
        return pd.read_excel(self.input_file, sheet_name=self.sheet_name)

    def analyze_columns_with_gpt(self, sample_df):
        """ Uses GPT-4All to decide which columns to keep/drop based on sample data patterns. """
        
        # Convert sample data to JSON
        sample_json = json.dumps(sample_df.to_dict(orient="records"), indent=4)
        
        # Check if the sample size exceeds the token limit and slice it if needed
        if len(sample_json.split()) > self.max_tokens:
            rows_to_send = sample_json.splitlines()[:self.max_tokens // 100]  # Approximate chunk size
            sample_json = "\n".join(rows_to_send)

        prompt = f"""
        You are an expert data analyst. I will give you a JSON sample of a dataset.
        Your task is to analyze patterns in the data and decide:
        - Which columns should be removed (IDs, primary keys, columns with only 'Y' or 'N', empty columns, and unnecessary fields)
        - Which columns should be kept (date columns, free-text, and relevant numerical columns)
        - Respond with a JSON object with two keys: "remove_columns" (list of columns to remove) and "keep_columns" (list of columns to keep).
        
        Sample Data:
        {sample_json}
        
        Please provide only the JSON response.
        """
        
        # Generate the response
        response = None
        with self.__model.chat_session():
            while response is None:
                gpt_response = self.__model.generate(prompt, max_tokens=1024)
                try:
                    response = json.loads(gpt_response)
                except json.JSONDecodeError:
                    response = None  # Retry if parsing fails

        return response.get("keep_columns", [])

    def preprocess_data(self, df):
        """ Extracts sample rows, uses GPT to decide on columns, and removes unnecessary ones. """

        # Drop completely empty columns
        df_cleaned = df.dropna(axis=1, how='all')

        # Take a sample to analyze patterns (Limit to small sample size to avoid large token generation)
        sample_df = df_cleaned.sample(min(self.sample_size, len(df_cleaned)), random_state=42)

        # Use GPT4All to analyze and determine columns to keep
        kept_columns = self.analyze_columns_with_gpt(sample_df)

        # Condense the DataFrame with the kept columns
        self.condensed_df = df_cleaned[kept_columns]

    def save_to_excel(self):
        """ Saves the condensed dataset to a new Excel file. """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_filename = f"condensed_dataset_{timestamp}.xlsx"
        self.condensed_df.to_excel(output_filename, index=False)
        return output_filename

def main():
    """ Main function to process and save the condensed dataset. """
    input_file = "Dataset.xlsx"  # Input dataset in Excel format
    sheet_name = "Sheet1"

    processor = CondenseDataset(input_file=input_file, sheet_name=sheet_name, sample_size=10)
    
    # Load data
    df = processor.load_data()

    # Process and clean data
    processor.preprocess_data(df)

    # Save to new Excel file
    output_file = processor.save_to_excel()
    
    print(f"Condensed dataset saved as: {output_file}")

if __name__ == '__main__':
    main()
