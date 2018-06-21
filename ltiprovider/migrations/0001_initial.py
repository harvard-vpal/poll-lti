# Generated by Django 2.0.5 on 2018-05-23 18:12

from django.db import migrations, models
import django.db.models.deletion
from ltiprovider.models import short_token


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LtiConsumer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consumer_name', models.CharField(max_length=255, unique=True)),
                ('consumer_key', models.CharField(default=short_token, max_length=32, unique=True)),
                ('consumer_secret', models.CharField(default=short_token, max_length=32, unique=True)),
                ('expiration_date', models.DateField(blank=True, null=True, verbose_name='Consumer key expiration date')),
                ('lms_metadata', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'LMS Platform',
                'verbose_name_plural': 'LMS Platforms',
            },
        ),
        migrations.CreateModel(
            name='LtiUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=255)),
                ('email', models.CharField(blank=True, max_length=255, null=True)),
                ('lti_consumer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ltiprovider.LtiConsumer')),
                ('tool_consumer_instance_guid', models.CharField(default='', max_length=255)),
            ],
            options={
                'verbose_name': 'LTI User',
                'verbose_name_plural': 'LTI Users',
            },
        ),
        migrations.AlterUniqueTogether(
            name='ltiuser',
            unique_together={('user_id', 'lti_consumer', 'tool_consumer_instance_guid')},
        ),
        migrations.AlterModelOptions(
            name='lticonsumer',
            options={'verbose_name': 'LTI Consumer', 'verbose_name_plural': 'LTI Consumers'},
        ),
        migrations.AddField(
            model_name='lticonsumer',
            name='default_tool_consumer_instance_guid',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.RemoveField(
            model_name='lticonsumer',
            name='lms_metadata',
        ),
    ]
