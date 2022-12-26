from exif import Image
from datetime import datetime
import os
import glob
import time
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import subprocess
import json

print("Enter the folder in which all jpg and mf4 files need to be checked. If you only press enter, current working directory will be used.")
basepath = input()
if basepath == "":
    basepath = os.getcwd()
print(f"Chosen base path: {basepath}")

class ExifTool(object):

    sentinel = "{ready}\r\n"

    def __init__(self, executable=os.path.join(os.getcwd(), 'exiftool.exe')):
        self.executable = executable

    def __enter__(self):
        self.process = subprocess.Popen(
            [self.executable, "-stay_open", "True",  "-@", "-"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        return self

    def  __exit__(self, exc_type, exc_value, traceback):
        self.process.stdin.write("-stay_open\nFalse\n")
        self.process.stdin.flush()

    def execute(self, *args):
        args = args + ("-execute\n",)

        self.process = subprocess.Popen(
                [self.executable, "-stay_open", "True",  "-@", "-"],
                universal_newlines=True,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.process.stdin.write(str.join("\n", args))
        self.process.stdin.flush()
        output = ""
        fd = self.process.stdout.fileno()
        while not output.endswith(self.sentinel):
            output += os.read(fd, 4096).decode('utf-8')
        return output[:-len(self.sentinel)]

    def get_metadata(self, *filenames):
        return json.loads(self.execute("-G", "-j", "-n", *filenames))

file_types = ["jpg", "mp4"]

files = []
for file_type in file_types:
   files.extend(glob.glob(os.path.join(basepath, f"*.{file_type}"), recursive=False))
files = pd.DataFrame(files, columns=["path"])

if files.empty:
    print(f"No files found in {basepath}")
else:
    print(f"Found {files.shape[0]} files!")

    files["basepath"] = [os.path.dirname(file) for file in files["path"]]

    files["file_name"] = files.path.str.split("\\").str[-1]
    files["file_type"] = files.file_name.str.split(".", expand=True)[1]
    files["prefix"] = files.file_name.str.split("_", expand=True)[0]

    files["suffix"] = None
    for index, file in tqdm(files.iterrows(), total=files.shape[0]):
        if "BURST" in file.file_name:
            files["suffix"].iloc[index] = file.file_name.split("_")[-1].split(".")[0]

    files["timestamp_filename"] = files.file_name.str.split("_", expand=True)[1] + files.file_name.str.split("_", expand=True)[2].str.split(".", expand=True)[0]
    files["timestamp_filename"] = pd.to_datetime(files["timestamp_filename"], format='%Y%m%d%H%M%S')

    files["timestamp_metadata"] = None
    files["error"] = False

    for index, file in tqdm(files[files["file_type"]=="jpg"].iterrows(), total=files[files["file_type"]=="jpg"].shape[0]):
        try:
            with open(file.path, "rb") as src:
                img = Image(src)        
                files["timestamp_metadata"].iloc[index] = datetime.strptime(img.datetime, '%Y:%m:%d %H:%M:%S')
        except Exception as error:
            print("Error occured:", str(file.path), str(error))
            files["timestamp_metadata"].iloc[index] = files["timestamp_filename"].iloc[index]
            files["error"].iloc[index] = True

    for index, file in tqdm(files[files["file_type"]=="mp4"].iterrows(), total=files[files["file_type"]=="mp4"].shape[0]):
        try:
            with ExifTool() as e:
                metadata = e.get_metadata(file.path)
                files["timestamp_metadata"].iloc[index] = datetime.strptime(metadata[0]["File:FileModifyDate"], "%Y:%m:%d %H:%M:%S%z").replace(tzinfo=None)
        except Exception as error:
            print("Error occured:", str(file.path), str(error))
            files["timestamp_metadata"].iloc[index] = files["timestamp_filename"].iloc[index]
            files["error"].iloc[index] = True

    files["time_diff"] = (abs(files["timestamp_filename"] - files["timestamp_metadata"]))
    files["rename"] = files["timestamp_filename"] != files["timestamp_metadata"]

    if files["rename"].any():
        print(f"Found files to rename: {files.groupby('rename').size()[True]} ...")
        Path(os.path.join(basepath, "renamed")).mkdir(parents=True, exist_ok=True)
        files["new_basepath"] = os.path.join(basepath, "renamed")
        files["new_path"] = files["new_basepath"] + "\\" + files["file_name"].copy()
        files["new_name"] = files["file_name"].copy()

        for index, file in tqdm(files[files["rename"]==True].iterrows(), total=files[files["rename"]==True].shape[0]):
            if files["suffix"].iloc[index]:
                files["new_name"].iloc[index] = f"{file.prefix}_{file.timestamp_metadata.strftime('%Y%m%d_%H%M%S')}_{files['suffix'].iloc[index]}.{file.file_type}"
            else:
                files["new_name"].iloc[index] = f"{file.prefix}_{file.timestamp_metadata.strftime('%Y%m%d_%H%M%S')}.{file.file_type}"
            files["new_path"].iloc[index] = f"{os.path.join(files['new_basepath'].iloc[index], files['new_name'].iloc[index])}"

        for index, file in tqdm(files[files["rename"]==True].iterrows(), total=files[files["rename"]==True].shape[0]):
            suffix = 1
            while files['new_name'].value_counts()[files["new_name"].iloc[index]] > 1:
                files["new_name"].iloc[index] = f"{file.prefix}_{file.timestamp_metadata.strftime('%Y%m%d_%H%M%S')}_{suffix}.{file.file_type}"
                files["new_path"].iloc[index] = f"{os.path.join(files['new_basepath'].iloc[index], files['new_name'].iloc[index])}"
                suffix += 1

        # for index, file in tqdm(files[(files["rename"]==True)&(files["error"]==False)].iterrows(), total=files[(files["rename"]==True)&(files["error"]==False)].shape[0]):
        for index, file in tqdm(files[files["error"]==False].iterrows(), total=files[files["error"]==False].shape[0]):
            os.rename(files["path"].iloc[index], files["new_path"].iloc[index])

        print("Renaming done!")

    files.to_csv(os.path.join(basepath, "Renamed_Files_Info.csv"), sep=";", decimal=",", index=False)
    print("Finished writing repord file!")
    print(files)

print("Window will close in 5 seconds...")
time.sleep(5)