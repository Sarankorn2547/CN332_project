from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodlocker', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='locker',
            name='status',
            field=models.CharField(choices=[('AVAILABLE', 'Available'), ('BOOKED', 'Booked'), ('OCCUPIED', 'Occupied')], default='AVAILABLE', max_length=20),
        ),
    ]
