# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-16 15:18
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pinax_stripe', '0011_subscription_connect'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_accounts', related_query_name='user_account', to='pinax_stripe.Account')),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_accounts', related_query_name='user_account', to='pinax_stripe.Customer')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_accounts', related_query_name='user_account', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='customer',
            name='users',
            field=models.ManyToManyField(related_name='customers', related_query_name='customers', through='pinax_stripe.UserAccount', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='useraccount',
            unique_together=set([('user', 'account', 'customer')]),
        ),
    ]
