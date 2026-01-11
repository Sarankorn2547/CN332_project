# Food Delivery Locker

## Overview
Food Box is a smart locker system for condos and dorms that lets food deliveries be dropped, stored, and picked up without waiting, meeting riders, or creating lobby chaos.

### Problem We Want to Solve
- Food left on tables gets stolen, spilled, or cold
- Riders and residents waste time finding each other
- Lobby becomes crowded, messy, and unsafe
- Staff are forced to manage food deliveries

### Why We Built It
We wanted to turn food delivery into a clean, automatic, and secure process, like how ATMs handle money or parcel lockers handle packages  but optimized for hot, time-sensitive food.

## Scenario
1. Resident orders food via app.
2. Food Box system linked to Room ID.
3. Rider arrives → Enters main room number.
4. AI selects permissions + chooses appropriate slot (Hot/Cold/Empty).
5. Rider opens slot to place food.
6. Box records and saves hash to Audit Log.
7. OTP system generates together with that box and sent to the resident's app
8. Resident arrives and enters main OTP.
9. System verifies,  The box opens.
10. System records delivery + closes order.

AI in normal and typical timeframes.
To predict peak periods of long-term food ordering 📊


## Features
### Smart access
Only you will receive an otp and the delivery person cannot open it again

### Clean & hygienic
No food on tables

No ants, no smell

Some lockers are heated or cooled

### App & screen
Shows:
- “Food arrived”
- “Locker number”
- “Time left before cleaning”

### Auto-timeout
If food is not picked up in 2 hours:
- Warning sent
- Locker frees itself
- Staff cleans it

### Building dashboard
Management can see:
- How many deliveries per day
- Which time is busiest
- Which lockers are always full

## Technology
### Smart Locker
storage system integrated with technology to manage access securely without traditional keys
Users access the locker using a OTP as a pin code

### LINE OA
a specialized account type on the LINE messaging application designed for businesses, organizations, or developers to interact with users.

### Load Cell
sensor that converts a physical force specifically weight or pressure into an electrical signal.


## Team Member
- ณัฐรวี ช่วยวัง 6610525013
- ศรัญย์กร พงศ์อัศวชัย 6610545011
- ชุติกาญจน์ กีดคำ 6610625011
- รัชชานนท์ ม่วงวิเชียร 6610685304

# HW1
- slide: https://www.canva.com/design/DAG-G7xf0UI/oEBJj4-rOHqiSAmjnN85eQ/edit