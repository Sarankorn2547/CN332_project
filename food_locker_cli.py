import uuid
import random
import time
from datetime import datetime, timedelta

# Locker Data Model

class Locker:
    def __init__(self, locker_id, size):
        self.locker_id = locker_id
        self.size = size
        self.is_occupied = False
        self.qr_code = None
        self.pin_code = None
        self.created_at = None
        self.timeout_minutes = 30

    def generate_access_codes(self):
        self.qr_code = str(uuid.uuid4())[:8]
        self.pin_code = random.randint(1000, 9999)
        self.created_at = datetime.now()

    def is_expired(self):
        if not self.created_at:
            return False
        return datetime.now() > self.created_at + timedelta(minutes=self.timeout_minutes)

    def reset(self):
        self.is_occupied = False
        self.qr_code = None
        self.pin_code = None
        self.created_at = None



# Locker System Controller

class FoodLockerSystem:
    def __init__(self):
        NUM_SMALL_LOCKERS = 10
        NUM_MEDIUM_LOCKERS = 5
        NUM_LARGE_LOCKERS = 5

        self.lockers = []
        locker_id_counter = 1
        for _ in range(NUM_SMALL_LOCKERS):
            self.lockers.append(Locker(locker_id_counter, "Small"))
            locker_id_counter += 1
        for _ in range(NUM_MEDIUM_LOCKERS):
            self.lockers.append(Locker(locker_id_counter, "Medium"))
            locker_id_counter += 1
        for _ in range(NUM_LARGE_LOCKERS):
            self.lockers.append(Locker(locker_id_counter, "Large"))
            locker_id_counter += 1

    def show_available_lockers(self):
        print("\nAvailable Lockers:")
        for locker in self.lockers:
            status = "Occupied" if locker.is_occupied else "Available"
            print(f"Locker {locker.locker_id} ({locker.size}) - {status}")

    def select_locker(self, size):
        available_lockers = [
            locker for locker in self.lockers
            if locker.size.lower() == size.lower() and not locker.is_occupied
        ]
        if not available_lockers:
            return None
        return random.choice(available_lockers)



    # Rider Flow

    def rider_deposit(self):
        print("\nSelect locker size:")
        print("1. Small")
        print("2. Medium")
        print("3. Large")
        size_choice = input("Select option: ")

        size_map = {
            "1": "Small",
            "2": "Medium",
            "3": "Large"
        }
        size = size_map.get(size_choice)

        if not size:
            print("X Invalid option.")
            return

        locker = self.select_locker(size)
        if not locker:
            print(f"X No available {size} lockers.")
            return

        locker.generate_access_codes()

        print("\nQR Code generated:")
        print(f"QR: {locker.qr_code}")
        print(f"PIN: {locker.pin_code}")

        confirm = input("\nHave you sent the QR/PIN to the customer? (yes/no): ")
        if confirm.lower() != "yes":
            print("X Cannot open locker without confirmation.")
            return

        print(f"Locker {locker.locker_id} opened. Please place food inside.")
        input("Press Enter after placing food...")

        locker.is_occupied = True
        print("Food deposited successfully.")
        print("Delivery photo recorded.")



    # Customer Flow

    def customer_pickup(self):
        code = input("\nEnter QR code or PIN: ")

        if code == "master123" or code == "adminqr":
            self.admin_override()
            return

        for locker in self.lockers:
            if not locker.is_occupied:
                continue

            if locker.is_expired():
                continue

            if code == locker.qr_code or code == str(locker.pin_code):
                print(f"Locker {locker.locker_id} unlocked.")
                input("Press Enter after collecting food...")
                locker.reset()
                print("Locker reset. Enjoy your meal!")
                return

        print("X Invalid or expired code.")



    # Admin / Security Flow

    def admin_override(self):
        print("\nAdmin Override Mode")

        for locker in self.lockers:
            if locker.is_occupied:
                print(f"Locker {locker.locker_id} ({locker.size}) - OCCUPIED")

        choice = input("\nEnter locker ID to open or 'cleanup': ")

        if choice == "cleanup":
            self.cleanup_expired()
            return

        for locker in self.lockers:
            if str(locker.locker_id) == choice and locker.is_occupied:
                print(f"Locker {locker.locker_id} opened by admin.")
                input("Press Enter after handling food...")
                locker.reset()
                print("Locker cleared.")
                return

        print("X Invalid selection.")



    # Auto Cleanup

    def cleanup_expired(self):
        cleaned = False
        for locker in self.lockers:
            if locker.is_occupied and locker.is_expired():
                locker.reset()
                cleaned = True
                print(f"Locker {locker.locker_id} cleaned (timeout).")

        if not cleaned:
            print("No expired lockers.")



# CLI Menu

def main():
    system = FoodLockerSystem()

    while True:
        print("\n=== FOOD DELIVERY LOCKER ===")
        print("1. Rider: Deposit Food")
        print("2. Customer: Pick Up Food")
        print("3. Exit")

        choice = input("Select option: ")

        if choice == "1":
            system.rider_deposit()
        elif choice == "2":
            system.customer_pickup()
        elif choice == "3":
            print("Goodbye")
            break
        else:
            print("X Invalid option.")

if __name__ == "__main__":
    main()
