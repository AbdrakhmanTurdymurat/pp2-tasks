name = {
    "Nurlan": 21,
    "Bekslan": 40, 
    "Ainur": 18,
    "Aibek": 16,
}
allowed = {"Nurlan", "Ainur"}

def checker(score):
    if score >= 18:
        return True
    else:
        return False
    
for name,score in name.items():
    if checker and name in allowed :
        print(f"{name}, {score} allowed")