from pathlib import Path

file_path = Path("sample.txt")

# WRITE
with open(file_path, "w") as f:
    f.write("Hello\n")
    f.write("This is Practice 6\n")

print("File created and written successfully")