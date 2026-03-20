from pathlib import Path

file_path = Path("sample.txt")

# READ ALL
with open(file_path, "r") as f:
    print("Full content:")
    print(f.read())

# READ LINE BY LINE
with open(file_path, "r") as f:
    print("Line by line:")
    for line in f:
        print(line.strip())

# READLINES
with open(file_path, "r") as f:
    lines = f.readlines()
    print("Readlines:", lines)