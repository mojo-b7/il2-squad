# Generated by Django 5.0 on 2024-06-04 10:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stats', '0002_alter_aircraft_options_alter_virtuallife_options_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='somepilotname',
            old_name='ul',
            new_name='url',
        ),
    ]
