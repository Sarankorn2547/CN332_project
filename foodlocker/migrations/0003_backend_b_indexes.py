from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodlocker', '0002_alter_locker_status'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='locker',
            index=models.Index(fields=['building', 'status'], name='locker_bldg_status_idx'),
        ),
        migrations.AddIndex(
            model_name='locker',
            index=models.Index(fields=['type', 'status'], name='locker_type_status_idx'),
        ),
        migrations.AddIndex(
            model_name='locker',
            index=models.Index(fields=['deposit_start_time'], name='locker_deposit_idx'),
        ),
        migrations.AddIndex(
            model_name='locker',
            index=models.Index(fields=['qr_data'], name='locker_qr_idx'),
        ),
        migrations.AddIndex(
            model_name='locker',
            index=models.Index(fields=['passcode'], name='locker_pin_idx'),
        ),
        migrations.AddIndex(
            model_name='lockerlog',
            index=models.Index(fields=['locker', 'action'], name='llog_locker_action_idx'),
        ),
        migrations.AddIndex(
            model_name='lockerlog',
            index=models.Index(fields=['actor_id'], name='llog_actor_idx'),
        ),
        migrations.AddIndex(
            model_name='lockerlog',
            index=models.Index(fields=['created_at'], name='llog_created_idx'),
        ),
    ]
