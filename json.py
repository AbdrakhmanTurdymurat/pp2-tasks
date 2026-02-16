import json

with open("sample-data.json") as f:
    data = json.load(f)

print("Interface Status")
print("=" * 80)
print(f"{'DN':<50} {'Description':<20}  {'Speed':>6}  {'MTU':>6}")
print(f"{'-' * 50} {'-' * 20}  {'-' * 6}  {'-' * 6}")

for item in data["imdata"]:
    attrs = item["l1PhysIf"]["attributes"]
    dn    = attrs["dn"]
    descr = attrs["descr"]
    speed = attrs["speed"]
    mtu   = attrs["mtu"]

    print(f"{dn:<50} {descr:<20}  {speed:>6}  {mtu:>6}")