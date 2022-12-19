import pandas as pd
import glob
import os
import time
from pathlib import Path

print("Enter the base path where you want to gather all jpg and mp4 files. If you only press enter, current working directory will be used.")
basepath = input()
if basepath == "":
    basepath = os.getcwd()
print(f"Chosen base path: {basepath}")

file_types = ["jpg", "mp4"]

files = []
for file_type in file_types:
   files.extend(glob.glob(os.path.join(basepath, f"**/*.{file_type}"), recursive=True))
files = pd.DataFrame(files, columns=["path"])

if files.empty:
    print(f"No files found in {basepath}")
else:
    print(f"Found {files.shape[0]} files to move!")
    files["basepath"] = [os.path.dirname(file) for file in files["path"]]
    files["file_name"] = files.path.str.split("\\").str[-1]
    files["file_type"] = files.file_name.str.split(".", expand=True)[1]

    print("Enter the output path you want to move all jpg and mp4 files to. If you only press enter, a subfulder called 'output' in current working directory will be used.")
    output_path = input()
    if output_path == "":
        output_path = f"{os.getcwd()}\\output"
        Path(output_path).mkdir(parents=True, exist_ok=True)
    print(f"Chosen output path: {output_path}")

    print(f"Starting moving files from {basepath} to {output_path}...")
    for index, file in files.iterrows():
        os.rename(file.path, os.path.join(output_path, file.file_name))
    print(f"Finished moving files from {basepath} to {output_path}!")

    print(f"Start deleting empty folders at {basepath}...")
    for entry in os.scandir(basepath):
        if os.path.isdir(entry.path) and not os.listdir(entry.path) :
            os.rmdir(entry.path)
    print(f"Finished deleting empty folders at {basepath}!")

print("Window will close in 5 seconds...")
time.sleep(5)