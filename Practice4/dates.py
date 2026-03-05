#1
from datetime import date, timedelta

today = date.today()
ago5 = today - timedelta(days=5)

print("Today:", today)
print("5 days ago:", ago5)
#2
from datetime import date, timedelta

today = date.today()
tomor = today + timedelta(days=1)
yester = today - timedelta(days=1)

print("Today:", today)
print("Tomorrow:", tomor)
print("Yesterday:", yester)
#3
from datetime import datetime

nomicro = now.replace(microsecond=0)
print("Datetime without microseconds: ", nomicro)
#4
from datetime import datetime

date1 = datetime(2026, 2, 16, 12, 0, 0)
date2 = datetime(2026, 2, 16, 14, 30, 0)

seconds = (date2 - date1).total_seconds()

print("Difference in seconds:", seconds)