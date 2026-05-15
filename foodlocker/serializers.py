from rest_framework import serializers
from .models import Project, Building, Room, Locker, LineUser, LockerLog

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

class LockerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locker
        fields = '__all__'

class LockerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locker
        fields = '__all__'
        # id/building are structural and immutable; passcode/qr_data are managed by LockerService
        read_only_fields = ('id', 'building', 'passcode', 'qr_data')

class LineUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineUser
        fields = '__all__'

class LockerLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LockerLog
        fields = '__all__'