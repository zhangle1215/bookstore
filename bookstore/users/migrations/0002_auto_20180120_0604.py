# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='passport',
            name='password',
            field=models.CharField(verbose_name='用户密码', max_length=60),
        ),
    ]
