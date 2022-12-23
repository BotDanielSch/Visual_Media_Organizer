import pandas as pd
import os
from tqdm import tqdm

files = pd.read_csv("Renamed_Files_Info.csv", sep=";", decimal=",")

for index, file in tqdm(files.iterrows(), total=files.shape[0]):
    try:
        os.rename(files["new_path"].iloc[index], files["path"].iloc[index])
    except:
        print("### ERROR ###")
        print(file.file_name)
        print(file.new_path)
        print(file.path)
        print("#############")