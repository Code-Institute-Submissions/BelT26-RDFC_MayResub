# Generated by Django 3.2 on 2022-01-05 17:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0006_auto_20220104_1249'),
    ]

    operations = [
        migrations.AlterField(
            model_name='member',
            name='email',
            field=models.EmailField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='member',
            name='username',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]