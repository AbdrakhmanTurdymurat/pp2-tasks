import json
import math

with open("data.json") as f:
    data = json.load(f)

S = math.pi * data["Radius"] ** 2

print(S)