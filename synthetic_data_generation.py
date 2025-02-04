import datetime
import pandas as pd
from gpt4all import GPT4All
import json
import re
from openpyxl import load_workbook
import math

class DataPreprocessor:
    def __init__(self):
        self.tokens = 0
        self.__original_df = None
        self.__columns = []
        self.__base_prompt = '''
I will provide you with the headers and 1 row of a dataset. I will give them to you as two lists. 
For example: Columns = ["Column1", "Column2", "Column3"], and Row = ["Value1", "Value2", "Value3"]

From here, I want some specific column types to be discarded:
    1. Columns which are IDs, for example ISIN, CUSIP, etc
    2. Columns which have Yes/No or Y/N values

I want to mostly keep columns which have dates, times and free text (names, descriptions, etc)


So, please mention the column names which should be retained. Also, make sure that the retained column names are displayed as a json list. For example: ["Column1", "Column2", "Column3"]
        '''
        self.__model = GPT4All(model_name='Meta-Llama-3-8B-Instruct.Q4_0.gguf', model_path='./', allow_download=False, n_ctx=8192)

    # Performs a very rough calculation of the number of tokens in header and first row of given df
    def __calculate_tokens(self, df):
        header_text = "".join(df.columns)
        tokens_in_header = len(header_text) // 4
        
        if not df.empty:
            first_row_text = "".join(map(str, df.iloc[0]))
            tokens_in_first_row = len(first_row_text) // 4
        else:
            tokens_in_first_row = 0
        
        return tokens_in_header, tokens_in_first_row

    def __parse_json(self, response):
        try:
            start = response.find("```") + len("```")
            end = response.rfind("```")
            if start == -1 or end == -1:
                return None
            
            response_section = response[start:end].strip()
            json_start = response_section.find("[")
            json_end = response_section.rfind("]") + 1
            
            if json_start == -1 or json_end == -1:
                return None
            
            json_content = response_section[json_start:json_end]
            parsed_json = json.loads(json_content)
            
            if isinstance(parsed_json, list) and all(isinstance(row, str) for row in parsed_json):
                return parsed_json
            else:
                return None
        except (json.JSONDecodeError, AttributeError):
            return None

    def __keep_relevant_rows(self, df):
        column_names = json.dumps(df.columns.tolist(), indent=4)
        row = json.dumps(df.values.tolist()[0], indent=4)

        prompt = self.__base_prompt + f'\nColumn Names: {column_names}\nRow {row}\n'
        
        data = None
        with self.__model.chat_session():
            iterations = 0
            while data is None:
                if iterations > 6:
                    raise SystemExit("Stuck in loop. Please run again.")
                response = self.__model.generate(prompt, max_tokens = 1024)
                data = self.__parse_json(response)
                iterations += 1
        
        for col in data:
            self.__columns.append(col)


    def __split_dataframe(self, df, n_buckets):
        if n_buckets <= 0:
            raise ValueError("Number of buckets must be greater than 0")
        
        num_cols = len(df.columns)
        split_size = num_cols // n_buckets
        remainder = num_cols % n_buckets
        
        split_indices = []
        start_idx = 0
        for i in range(n_buckets):
            extra = 1 if i < remainder else 0
            end_idx = start_idx + split_size + extra
            split_indices.append((start_idx, end_idx))
            start_idx = end_idx
        
        # Sometimes the last dataframe is empty except for an index. This removes that last df.
        split_dfs = [df.iloc[:, start:end] for start, end in split_indices]
        if len(split_dfs[-1].columns.tolist()) == 0:
            split_dfs = split_dfs[:-1]

        return split_dfs

    def preprocess_data(self, df):
        self.__original_df = df

        df = df.sample(1)

        header_tokens, row_tokens = self.__calculate_tokens(df)
        tokens = header_tokens + row_tokens

        # I have a token limit of 8192. This will also include my base prompt.
        # After subtracting the base prompt, I'm assuming (conservatively) we will have 7000 tokens left.
        # If the total tokens in header + 1 row in df exceeds 7000, I will query the LLM multiple times.
        # For example, if total tokens = 15000, I will query the LLM three times. 7000 + 7000 + 1000
        n_buckets = math.ceil(tokens / 7000)

        split_dataframes = self.__split_dataframe(df, n_buckets)

        for split_df in split_dataframes:
            self.__keep_relevant_rows(split_df)

        condensed_df = self.__original_df[self.__columns]
        return condensed_df


class SyntheticDataGenerator:
    def __init__(self, input_df, n_synthetic_rows = 2, custom_prompt = '', bucket_size = 5):
        self.__model = GPT4All(model_name='Meta-Llama-3-8B-Instruct.Q4_0.gguf', model_path='./', allow_download=False, n_ctx=8192)
        self.__input_df = input_df
        self.__n_synthetic_rows = n_synthetic_rows
        self.__custom_prompt = custom_prompt
        self.__bucket_size = bucket_size

        self.__base_prompt = '''
You are a synthetic data generator. You will be given a JSON dataset. You will have to generate a new JSON dataset which is similar to the given dataset. Please be creative while generating the data. Make sure that the newly generated values are unique.

I'll first provide a list with the columns of the dataset. For example, ["Col1", "Col2", "Col3"]
Then I'll provide a list of list where each inner list represents a row. For example:
[["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]]

Make sure that your output is generated as a json, in the same format as the input is given. The output should only contain the generated rows as a list of lists. Don't include the column names again. Make sure that the output json is clearly marked. 
        '''

        # If we only try to generate 
        if self.__n_synthetic_rows < 2:
            self.__n_synthetic_rows = 2

        self.generated_df = None

    def parse_json(self, response):
        try:
            start = response.find("```") + len("```")
            end = response.rfind("```")
            if start == -1 or end == -1:
                return None
            
            response_section = response[start:end].strip()
            json_start = response_section.find("[")
            json_end = response_section.rfind("]") + 1
            
            if json_start == -1 or json_end == -1:
                return None
            
            json_content = response_section[json_start:json_end]
            parsed_json = json.loads(json_content)
            
            if isinstance(parsed_json, list) and all(isinstance(row, list) for row in parsed_json):
                return parsed_json
            else:
                return None
        except (json.JSONDecodeError, AttributeError):
            return None
        
    def generate_rows(self, n_rows):
        df = self.__input_df.sample(min(n_rows, len(self.__input_df)))

        column_names = json.dumps(self.__input_df.columns.tolist(), indent=4)
        rows = json.dumps(df.values.tolist(), indent=4)

        prompt = ''
        prompt = self.__base_prompt + f'\nColumn Names: {column_names}\nRows: {rows}\n'
        prompt = prompt + '\n' + self.__custom_prompt
        prompt = prompt + '\n' + f'Please generate {n_rows} rows'

        data = None
        with self.__model.chat_session():
            iterations = 0
            while data is None:
                if iterations > 6:
                    raise SystemExit("Stuck in loop. Please run again.")
                response = self.__model.generate(prompt, max_tokens = n_rows * 1024)
                data = self.parse_json(response)
                iterations += 1

        return data

    def generate_synthetic_data(self):
        n_remaining_rows = self.__n_synthetic_rows
        generated_rows = []
        while n_remaining_rows > 0:
            for row in self.generate_rows(min(n_remaining_rows, self.__bucket_size)):
                generated_rows.append(row)
            n_remaining_rows = n_remaining_rows - self.__bucket_size
            print(f'Generated {self.__n_synthetic_rows - n_remaining_rows} rows out of {self.__n_synthetic_rows} rows')

        self.generated_df = pd.DataFrame(generated_rows, columns=self.__input_df.columns)


def save_dataframe_to_excel(df):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"synthetic_data_{timestamp}.xlsx"
    df.to_excel(filename, index=False)
    return filename


def main():
    input_df = pd.read_excel("Dataset.xlsx", sheet_name="Sheet1")

    processor = DataPreprocessor()
    condensed_df = processor.preprocess_data(input_df)

    synthetic_data_generator = SyntheticDataGenerator(input_df=condensed_df, n_synthetic_rows=10, bucket_size = 5)
    synthetic_data_generator.generate_synthetic_data()

    synthetic_df = synthetic_data_generator.generated_df
    save_dataframe_to_excel(synthetic_df)


if __name__ == '__main__':
    main()