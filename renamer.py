from exif import Image
from datetime import datetime
import os
import glob
import time
import pandas as pd


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

    files["timestamp_metadata"] = None

    for index, file in files.iterrows():

        with open(file.path, "rb") as src:
            img = Image(src)        
            files["timestamp_metadata"].iloc[index] = datetime.strptime(img.datetime, '%Y:%m:%d %H:%M:%S')

    files["time_diff"] = (abs(files["timestamp_filename"] - files["timestamp_metadata"]))
    files["rename"] = files["timestamp_filename"] != files["timestamp_metadata"]

    if files["rename"].any():
        print(f"Found files to rename: {files.groupby('rename').size()[True]} ...")
        files["new_path"] = files["path"].copy()
        files["new_name"] = files["file_name"].copy()

        for index, file in files[files["rename"]==True].iterrows():
            files["new_name"].iloc[index] = f"{file.prefix}_{file.timestamp_metadata.strftime('%Y%m%d_%H%M%S')}.{file.file_type}"
            files["new_path"].iloc[index] = f"{os.path.join(basepath, files['new_name'].iloc[index])}"
            os.rename(files["path"].iloc[index], files["new_path"].iloc[index])
        print("Renaming done!")

    files.to_csv(os.path.join(basepath, "Renamed_Files_Info.csv"), sep=";", decimal=",", index=False)
    print("Finished writing repord file!")
    print(files)

print("Window will close in 5 seconds...")
time.sleep(5)