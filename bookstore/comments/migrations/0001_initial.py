# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20180124_0640'),
        ('books', '0002_auto_20180125_0914'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comments',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('is_delete', models.BooleanField(default=False, verbose_name='删除标记')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('disabled', models.BooleanField(default=False, verbose_name='禁用评论')),
                ('content', models.CharField(max_length=1000, verbose_name='评论内容')),
                ('book', models.ForeignKey(to='books.Books', verbose_name='书籍ID')),
                ('user', models.ForeignKey(to='users.Passport', verbose_name='用户ID')),
            ],
            options={
                'db_table': 's_comment_table',
            },
        ),
    ]
