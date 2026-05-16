import json
import requests
from django.shortcuts import render
from foodlocker.models import Locker, Building

_STATUS_MAP = {
    'Available': 'available',
    'In Use': 'occupied',
    'Booked': 'booked',
}


def locker_wall(request):
    try:
        resp = requests.get('http://127.0.0.1:8000/api/lockers/', timeout=5)
        resp.raise_for_status()
        api_lockers = resp.json()
        lockers_data = [
            {
                'id': str(locker.get('id', '')),
                'local_id': locker.get('local_id', str(locker.get('id', ''))),
                'size': locker.get('size', ''),
                'type': locker.get('type', 'FOOD'),
                'status': _STATUS_MAP.get(locker.get('status', ''), locker.get('status', 'available').lower()),
                'isOpen': locker.get('is_door_open', False),
                'has_object': locker.get('has_object', False),
            }
            for locker in api_lockers
        ]
    except Exception:
        lockers_data = []

    return render(request, 'locker_wall/wall.html', {
        'lockers_json': json.dumps(lockers_data),
        'buildings': [],
        'selected_building': None,
    })


def test_door(request):
    return render(request, 'locker_wall/test_door.html')


def locker_wall_partial(request):
    """
    HTMX partial: คืน HTML แค่ grid ของตู้ (ใช้สำหรับ polling / filter)
    """
    building_id = request.GET.get('building_id')
    locker_type = request.GET.get('type')

    try:
        params = {}
        if building_id:
            params['building_id'] = building_id
        if locker_type:
            params['type'] = locker_type

        resp = requests.get('http://127.0.0.1:8000/api/lockers/', params=params, timeout=5)
        resp.raise_for_status()
        api_lockers = resp.json()
        lockers_data = [
            {
                'id': str(locker.get('id', '')),
                'local_id': locker.get('local_id', str(locker.get('id', ''))),
                'size': locker.get('size', ''),
                'type': locker.get('type', ''),
                'status': _STATUS_MAP.get(locker.get('status', ''), locker.get('status', 'available').lower()),
                'isOpen': locker.get('is_door_open', False),
                'has_object': locker.get('has_object', False),
            }
            for locker in api_lockers
        ]
    except Exception:
        lockers_data = []

    return render(request, 'locker_wall/partials/locker_grid.html', {
        'lockers_json': json.dumps(lockers_data),
    })
