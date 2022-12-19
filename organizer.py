import glob
import os
import pandas as pd
import time
from pathlib import Path

print("Enter the folder in which all jpg and mf4 files need to be checked. If you only press enter, current working directory will be used.")
basepath = input()
if basepath == "":
    basepath = os.getcwd()
print(f"Chosen base path: {basepath}")

file_types = ["jpg", "mp4"]

files = []
for file_type in file_types:
   files.extend(glob.glob(os.path.join(basepath, f"*.{file_type}"), recursive=False))
files = pd.DataFrame(files, columns=["path"])

if files.empty:
    print(f"No files found in {basepath}")
else:
    print(f"Found {files.shape[0]} files to move!")

    files["basepath"] = [os.path.dirname(file) for file in files["path"]]
    files["file_name"] = files.path.str.split("\\").str[-1] 
    files["file_type"] = files.file_name.str.split(".", expand=True)[1]
    files["prefix"] = files.file_name.str.split("_", expand=True)[0]
    files["timestamp_filename"] = files.file_name.str.split("_", expand=True)[1] + files.file_name.str.split("_", expand=True)[2].str.split(".", expand=True)[0]
    files["timestamp_filename"] = pd.to_datetime(files["timestamp_filename"], format='%Y%m%d%H%M%S')

    files["date"] = files.path.str.split("_", expand=True)[1]
    files["year"] = files.date.str[0:4]
    files["month"] = files.date.str[4:6]
    files["day"] = files.date.str[6:8]

    files["tag"] = files[["year", "month", "day"]].agg('_'.join, axis=1)
    
print(f"Need to create {len(files.tag.unique())} subfolders...")
for tag in files.tag.unique():
    Path(os.path.join(basepath, tag)).mkdir(parents=True, exist_ok=True)

print(f"Files to move: {files.shape[0]}...")
for _, file in files.iterrows():
    os.rename(file.path, os.path.join(basepath, file.tag, file.file_name))
print(f"Finished moving files!")

print("Window will close in 5 seconds...")
time.sleep(5)