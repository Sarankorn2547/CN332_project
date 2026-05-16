import json
from django.shortcuts import render
from foodlocker.models import Locker, Building


def locker_wall(request):
    lockers_data = [
        {'id': '1', 'local_id': 'A-01', 'size': 'S', 'type': 'FOOD',
         'status': 'available', 'isOpen': False, 'has_object': False},
        {'id': '2', 'local_id': 'A-02', 'size': 'M', 'type': 'FOOD',
         'status': 'occupied',  'isOpen': False, 'has_object': True},
        {'id': '3', 'local_id': 'A-03', 'size': 'L', 'type': 'FOOD',
         'status': 'booked',    'isOpen': True,  'has_object': False},
        {'id': '4', 'local_id': 'A-04', 'size': 'S', 'type': 'ASSET',
         'status': 'available', 'isOpen': False, 'has_object': False},
        {'id': '5', 'local_id': 'B-01', 'size': 'M', 'type': 'LAUNDRY',
         'status': 'occupied',  'isOpen': False, 'has_object': True},
        {'id': '6', 'local_id': 'B-02', 'size': 'S', 'type': 'KEY',
         'status': 'available', 'isOpen': False, 'has_object': False},
    ]
    return render(request, 'locker_wall/wall.html', {
        'lockers_json': json.dumps(lockers_data),
        'buildings': [],
        'selected_building': None,
    })


def locker_wall_partial(request):
    """
    HTMX partial: คืน HTML แค่ grid ของตู้ (ใช้สำหรับ polling / filter)
    """
    building_id = request.GET.get('building_id', None)
    locker_type = request.GET.get('type', None)

    try:
        lockers_qs = Locker.objects.all()
        if building_id:
            lockers_qs = lockers_qs.filter(building_id=building_id)
        if locker_type:
            lockers_qs = lockers_qs.filter(type=locker_type)

        lockers_data = []
        for locker in lockers_qs:
            lockers_data.append({
                'id': str(locker.id),
                'local_id': locker.local_id or str(locker.id),
                'size': locker.size,
                'type': locker.type if hasattr(locker, 'type') else 'FOOD',
                'status': locker.status.lower() if locker.status else 'available',
                'isOpen': locker.is_door_open if hasattr(locker, 'is_door_open') else False,
                'has_object': locker.has_object if hasattr(locker, 'has_object') else False,
            })
    except Exception:
        lockers_data = []

    return render(request, 'locker_wall/partials/locker_grid.html', {
        'lockers_json': json.dumps(lockers_data),
    })
