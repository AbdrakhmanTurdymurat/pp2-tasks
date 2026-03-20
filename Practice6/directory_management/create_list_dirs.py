import os
from pathlib import Path

# CREATE DIRECTORIES
Path("test_dir/sub_dir").mkdir(parents=True, exist_ok=True)

print("Directories created")

# CURRENT DIRECTORY
print("Current directory:", os.getcwd())

# LIST FILES
print("Files and folders:")
print(os.listdir("."))

# FIND .txt FILES
txt_files = list(Path(".").rglob("*.txt"))
print("TXT files found:", txt_files)