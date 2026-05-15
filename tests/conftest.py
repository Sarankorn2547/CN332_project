import pytest
from foodlocker.models import Project, Building, LineUser, Locker


@pytest.fixture
def project(db):
    return Project.objects.create(id='prj-001', name='Test Project', address='123 Test St')


@pytest.fixture
def building(db, project):
    return Building.objects.create(id='bld-001', project=project, name='Building A')


@pytest.fixture
def line_user(db, project, building):
    return LineUser.objects.create(
        line_user_id='U_TEST_001',
        project=project,
        building=building,
        room_no='101',
        display_name='Test User',
    )


@pytest.fixture
def locker(db, building):
    return Locker.objects.create(
        id='lck-001',
        building=building,
        local_id='1',
        size='M',
        status='AVAILABLE',
        type='FOOD',
        passcode='',
        qr_data='',
        is_door_open=False,
        has_object=False,
        is_locked=True,
    )
