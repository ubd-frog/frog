# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=128)),
                ('security', models.SmallIntegerField(default=0, choices=[(0, b'Public'), (1, b'Private'), (2, b'Personal')])),
                ('description', models.TextField(default=b'', blank=True)),
                ('uploads', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'Galleries',
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('updated', models.DateTimeField(null=True)),
                ('thumbnail', models.ImageField(max_length=255, null=True, upload_to=b'%Y/%m/%d', blank=True)),
                ('width', models.IntegerField(default=0)),
                ('height', models.IntegerField(default=0)),
                ('foreign_path', models.TextField(blank=True)),
                ('unique_id', models.CharField(max_length=255, blank=True)),
                ('guid', models.CharField(max_length=16, blank=True)),
                ('deleted', models.BooleanField(default=False)),
                ('hash', models.CharField(max_length=40, blank=True)),
                ('comment_count', models.IntegerField(default=0)),
                ('source', models.ImageField(upload_to=b'%Y/%m/%d', width_field=b'width', height_field=b'height', max_length=255, blank=True, null=True)),
                ('image', models.ImageField(max_length=255, null=True, upload_to=b'%Y/%m/%d', blank=True)),
                ('small', models.ImageField(max_length=255, null=True, upload_to=b'%Y/%m/%d', blank=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created', '-id'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RSSStorage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('interval', models.CharField(max_length=6)),
                ('data', models.TextField()),
                ('gallery', models.ForeignKey(related_name='rss_storage', to='frog.Gallery')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('artist', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(blank=True, to='frog.Tag', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserPref',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.TextField(default=b'{}')),
                ('user', models.ForeignKey(related_name='frog_prefs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('updated', models.DateTimeField(null=True)),
                ('thumbnail', models.ImageField(max_length=255, null=True, upload_to=b'%Y/%m/%d', blank=True)),
                ('width', models.IntegerField(default=0)),
                ('height', models.IntegerField(default=0)),
                ('foreign_path', models.TextField(blank=True)),
                ('unique_id', models.CharField(max_length=255, blank=True)),
                ('guid', models.CharField(max_length=16, blank=True)),
                ('deleted', models.BooleanField(default=False)),
                ('hash', models.CharField(max_length=40, blank=True)),
                ('comment_count', models.IntegerField(default=0)),
                ('source', models.FileField(max_length=255, null=True, upload_to=b'%Y/%m/%d', blank=True)),
                ('video', models.FileField(max_length=255, null=True, upload_to=b'%Y/%m/%d', blank=True)),
                ('video_thumbnail', models.FileField(max_length=255, null=True, upload_to=b'%Y/%m/%d', blank=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(to='frog.Tag', blank=True)),
            ],
            options={
                'ordering': ['-created', '-id'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VideoQueue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.SmallIntegerField(default=0, choices=[(0, b'Queued'), (1, b'Processing'), (2, b'Completed'), (3, b'Error')])),
                ('message', models.TextField(null=True, blank=True)),
                ('video', models.OneToOneField(related_name='queue', to='frog.Video')),
            ],
        ),
        migrations.AddField(
            model_name='image',
            name='tags',
            field=models.ManyToManyField(to='frog.Tag', blank=True),
        ),
        migrations.AddField(
            model_name='gallery',
            name='images',
            field=models.ManyToManyField(to='frog.Image', blank=True),
        ),
        migrations.AddField(
            model_name='gallery',
            name='owner',
            field=models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='gallery',
            name='parent',
            field=models.ForeignKey(blank=True, to='frog.Gallery', null=True),
        ),
        migrations.AddField(
            model_name='gallery',
            name='videos',
            field=models.ManyToManyField(to='frog.Video', blank=True),
        ),
    ]
