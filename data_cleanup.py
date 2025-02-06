import pandas as pd

file_path = "Dataset_Dirty.csv"

with open(file_path, "r", encoding="utf-8") as file:
    lines = file.readlines()

fields = []
data_lines = []
reading_fields = False
reading_data = False

for line in lines:
    line = line.strip() 
    if line.startswith("START-OF-FIELDS"):
        reading_fields = True
        continue
    elif line.startswith("END-OF-FIELDS"):
        reading_fields = False
        continue
    elif line.startswith("START-OF-DATA"):
        reading_data = True
        continue
    elif line.startswith("END-OF-DATA"):
        reading_data = False
        continue

    if reading_fields:
        if line and not line.startswith("#"):
            field = line.split(",")[0]
            if field != '':
                fields.append(field) 

    if reading_data:
        data_lines.append(line.split(",")) 

trimmed_data_lines = []
for data_line in data_lines:
    trimmed_data_lines.append(data_line[3:len(fields)])

df = pd.DataFrame(trimmed_data_lines, columns=fields)
df.to_csv('Dataset_Clean.csv', index=False)
