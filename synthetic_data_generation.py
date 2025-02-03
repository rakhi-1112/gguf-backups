import datetime
import pandas as pd
from gpt4all import GPT4All
import json
import re
from openpyxl import load_workbook

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
            while data is None:
                response = self.__model.generate(prompt, max_tokens = n_rows * 1024)
                data = self.parse_json(response)

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

    synthetic_data_generator = SyntheticDataGenerator(input_df=input_df, n_synthetic_rows=10, bucket_size = 5)
    synthetic_data_generator.generate_synthetic_data()

    synthetic_df = synthetic_data_generator.generated_df
    save_dataframe_to_excel(synthetic_df)


if __name__ == '__main__':
    main()