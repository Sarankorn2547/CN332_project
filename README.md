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

## Use Case/Scenario
1. Order & Assignment:

Resident places an order via the app;
system links the order to the Room ID.

2. Rider Arrival & Allocation

Rider inputs Room ID on the kiosk.
AI Engine validates access and allocates the optimal compartment (Hot / Cold / Ambient).

3. Secure Drop-off

Compartment opens for deposit, then auto-locks.
Transaction Hash is recorded in the Audit Log for security.
System generates a unique OTP and sends it to the resident’s app.

4. Verified Retrieval

Resident enters OTP at the locker.
System verifies, opens the specific box, records the pickup, 
and closes the ticket.

5. Data & Prediction

AI analyzes timing, usage density, and user behavior to 
predict future peak periods.



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