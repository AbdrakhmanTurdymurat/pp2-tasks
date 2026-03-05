import re

with open("raw.txt", "r", encoding="utf-8") as f:
    text = f.read()

#Extract prices
prices = re.findall(r"\d+\s?\d*,\d{2}", text)

#Extract product names
products = re.findall(r"\d+\.\n(.+)", text)

#Extract total
total = re.search(r"ИТОГО:\n([\d\s,]+)", text)

#Extract date and time
datetime = re.search(r"\d{2}\.\d{2}\.\d{4}\s\d{2}:\d{2}:\d{2}", text)

#Payment method
payment = re.search(r"Банковская карта", text)

print("Products:")
for p in products:
    print("-", p)

print("\nPrices:")
for price in prices[:20]:
    print(price)

print("\nTotal:")
if total:
    print(total.group(1))

print("\nDate and Time:")
if datetime:
    print(datetime.group())

print("\nPayment Method:")
if payment:
    print("Bank Card")