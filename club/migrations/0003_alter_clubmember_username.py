# Generated by Django 3.2 on 2022-01-10 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0002_alter_clubmember_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clubmember',
            name='username',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
