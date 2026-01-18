# Food Delivery Locker

## Overview
Food Box is an automated smart locker system designed to streamline the food delivery process in residential buildings. By using a secure QR and random code system, it eliminates the need for direct contact between riders and residents while ensuring food safety.

### Problem We Want to Solve
- **The "Waiting Game":** Riders and residents often waste time coordinating hand-offs.
- **Theft and Hygiene:** Food left in open areas is prone to being stolen, confused with other orders, or exposed to pests.
- **Security Issues:** Minimizes the need for external delivery personnel to wander through private building floors.

### Why We Built It
We created this system to provide a secure, traceable "middle-man" for deliveries. Unlike standard parcel lockers, this workflow is optimized for the speed and verification requirements of food delivery, providing backup solutions for technical issues and abandoned orders.

## Use Case/Scenario (Workflow)

1.  **Rider Arrival & Setup:**
    *   The rider arrives at the locker station and selects the appropriate **Locker Size** on the screen.
2.  **Code Generation:**
    *   The system generates a unique **QR Code + Random Pin Code**.
3.  **Customer Notification:**
    *   The rider takes a photo of the QR/Code on the screen and sends it to the customer via their delivery app.
4.  **Secure Deposit:**
    *   The rider confirms on the screen that the photo has been sent. The locker door opens.
    *   The rider places the food inside and takes a final "delivered" photo of the food within the locker for proof of service.
5.  **Verified Retrieval:**
    *   The resident arrives at the locker and scans the **QR Code** or enters the **Random Pin Code** to unlock the compartment.
6.  **Completion:**
    *   The resident retrieves their food and closes the locker door, resetting the locker for the next use.

## Exception Handling & Features

### Smart Access & Recovery
*   **QR/Technical Issue:** If the QR code fails to scan, a Security Guard (รปภ.) holds a **Master QR**. They can open the locker for the customer after verifying the delivery using the rider's food photo.
*   **Secure Validation:** The door only opens for the rider *after* they confirm they have sent the access credentials to the customer.

### Auto-Cleanup (Timeout Policy)
*   **Abandoned Food:** If food is not picked up within the maximum allowed time, the system triggers a timeout.
*   **Staff Intervention:** Building security or staff will be notified to remove the food and clear the locker to maintain hygiene and availability.

### Clean & Secure
*   **No Contact:** Eliminates the "lobby chaos" of food bags piled on tables.
*   **Traceability:** Every step, from deposit to pickup (including photo evidence), is recorded.

## Technology

### Smart Kiosk Interface
A centralized touchscreen where riders select locker sizes and customers input codes. It manages the logic for generating unique session-based QR codes.

### Master Access System
A secondary override system (Master QR) provided to building management to handle technical malfunctions or lost access codes.

### Photo-Verification Logic
Integrated workflow that requires "proof of photo" before and after the locker door operates, ensuring a digital paper trail for both the rider and the resident.

## Team Member
- ณัฐรวี ช่วยวัง 6610525013
- ศรัญย์กร พงศ์อัศวชัย 6610545011
- ชุติกาญจน์ กีดคำ 6610625011
- รัชชานนท์ ม่วงวิเชียร 6610685304

# HW1
- slide: https://www.canva.com/design/DAG-G7xf0UI/oEBJj4-rOHqiSAmjnN85eQ/edit

# Sentence Breakdown
| Subject          | Verb        | Object             | Full Sentence                                             |
| ---------------- | ----------- | ------------------ | --------------------------------------------------------- |
| Rider            | Selects     | Locker Size        | The rider selects a locker size.                          |
| Locker System    | Generates   | QR Code & Passcode | The locker system generates a QR code and a passcode.     |
| Screen           | Displays    | QR Code & Passcode | The screen displays the QR code and passcode.             |
| Rider            | Photographs | Screen             | The rider photographs the screen.                         |
| Rider            | Presses     | Confirm Button     | The rider presses the confirm button.                     |
| Locker System    | Unlocks     | Door               | The locker system unlocks the door.                       |
| Rider            | Places      | Food               | The rider places the food inside the locker.              |
| Rider            | Closes      | Door               | The rider closes the door.                                |
| Sensor           | Detects     | Door Status        | The sensor detects the door status.                       |
| Sensor           | Detects     | Object             | The sensor detects an object inside the locker.           |
| Locker System    | Updates     | Status (Occupied)  | The locker system updates the locker status to occupied.  |
| Customer         | Scans       | QR Code            | The customer scans the QR code.                           |
| Customer         | Enters      | Passcode           | The customer enters the passcode.                         |
| Locker System    | Validates   | QR Code / Passcode | The locker system validates the QR code and passcode.     |
| Admin (Security) | Scans       | Master QR          | The admin scans the master QR code.                       |
| Locker System    | Checks      | Time Duration      | The locker system checks the storage time duration.       |
| Locker System    | Alerts      | Admin              | The locker system alerts the admin when the time expires. |
