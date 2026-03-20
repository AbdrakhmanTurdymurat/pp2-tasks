import shutil
from pathlib import Path

source = Path("sample.txt")
backup = Path("sample_backup.txt")

# COPY
if source.exists():
    shutil.copy(source, backup)
    print("File copied")

# APPEND
with open(source, "a") as f:
    f.write("Appended line\n")

print("Line appended")

# DELETE
temp = Path("temp.txt")
temp.write_text("temporary file")

if temp.exists():
    temp.unlink()
    print("Temporary file deleted")