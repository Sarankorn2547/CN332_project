from django.contrib import admin
from .models import Project, Building, Room, Locker, LineUser, LockerLog

admin.site.register(Project)
admin.site.register(Building)
admin.site.register(Room)
admin.site.register(Locker)
admin.site.register(LineUser)
admin.site.register(LockerLog)