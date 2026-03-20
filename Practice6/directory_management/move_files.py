import shutil
from pathlib import Path

source = Path("../file_handling/sample.txt")
destination = Path("moved_sample.txt")

if source.exists():
    shutil.copy(source, destination)
    print("File moved/copied successfully")
else:
    print("Source file not found")