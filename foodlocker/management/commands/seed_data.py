import csv
from django.core.management.base import BaseCommand
from foodlocker.models import Project, Building, Room, Locker, LineUser

class Command(BaseCommand):
    help = 'Seeds the database with data from CSV files'

    def handle(self, *args, **kwargs):
        self.seed_projects()
        self.seed_buildings()
        self.seed_rooms()
        self.seed_lockers()
        self.seed_line_users()

    def seed_projects(self):
        with open('data/projects.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Project.objects.create(
                    id=row['id'],
                    name=row['name'],
                    address=row['address']
                )
        self.stdout.write(self.style.SUCCESS('Successfully seeded projects.'))

    def seed_buildings(self):
        with open('data/buildings.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                project = Project.objects.get(id=row['project_id'])
                Building.objects.create(
                    id=row['id'],
                    project=project,
                    name=row['name']
                )
        self.stdout.write(self.style.SUCCESS('Successfully seeded buildings.'))

    def seed_rooms(self):
        with open('data/rooms.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                building = Building.objects.get(id=row['building_id'])
                Room.objects.create(
                    building=building,
                    unit_number=row['unit_number'],
                    floor=row['floor']
                )
        self.stdout.write(self.style.SUCCESS('Successfully seeded rooms.'))

    def seed_lockers(self):
        with open('data/lockers.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                building = Building.objects.get(id=row['building_id'])
                Locker.objects.create(
                    id=row['id'],
                    building=building,
                    local_id=row['local_id'],
                    size=row['size'],
                    status=row['status'],
                    type=row['type'],
                    passcode=row['passcode'],
                    qr_data=row['qr_data']
                )
        self.stdout.write(self.style.SUCCESS('Successfully seeded lockers.'))

    def seed_line_users(self):
        with open('data/line_users.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                project = Project.objects.get(id=row['project_id'])
                building = Building.objects.get(id=row['building_id'])
                LineUser.objects.create(
                    line_user_id=row['line_user_id'],
                    project=project,
                    building=building,
                    room_no=row['room_no'],
                    display_name=row['display_name']
                )
        self.stdout.write(self.style.SUCCESS('Successfully seeded line users.'))
