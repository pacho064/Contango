import random
import datetime

# This script simulates a "Live" update. 
# In the future, we can point this to a real API like OPEC or Bloomberg.

now = datetime.datetime.now(datetime.timezone.utc)
timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

# Base prices
brent = 82.45
arab_l = 84.15
murban = 83.90
oman = 81.20

# Add a tiny bit of random "Live" movement (+/- 0.50)
brent += round(random.uniform(-0.5, 0.5), 2)
arab_l += round(random.uniform(-0.5, 0.5), 2)
murban += round(random.uniform(-0.5, 0.5), 2)
oman += round(random.uniform(-0.5, 0.5), 2)

# This creates the text for your data.js file
data_content = f"""const CONTANGO_DATA = {{
  lastUpdated: "{timestamp}",
  prices: [
    {{sym: 'BRENT', name: 'ICE Brent', val: {brent}, chg: 1.2, origin: 'Global'}},
    {{sym: 'ARAB L', name: 'Arab Light', val: {arab_l}, chg: 0.8, origin: 'Saudi Arabia'}},
    {{sym: 'MURBAN', name: 'Murban', val: {murban}, chg: 1.1, origin: 'UAE'}},
    {{sym: 'OMAN', name: 'Oman/Dubai', val: {oman}, chg: -0.4, origin: 'DME'}}
  ],
  intel: [
    {{tag: 'LOGISTICS', hl: 'Suez Transit Risk Elevated', txt: 'Shipping volumes down 15% WoW.', time: 'Live'}}
  ],
  infrastructure: [
    {{name: 'Ras Tanura', status: 'Normal', desc: 'Operating at 88% utilization.'}}
  ],
  opec: [
    {{nation: 'Saudi Arabia', quota: 9.0, actual: 8.98}},
    {{nation: 'Iraq', quota: 4.0, actual: 4.25}}
  ]
}};"""

# Save the new notebook
with open("data.js", "w") as f:
    f.write(data_content)

print(f"Robot successfully updated data.js at {timestamp}")
