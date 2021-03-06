# -*- coding: utf-8 -*-
# generated by django 1.11.6 on 2017-10-20 07:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def delete_user_accounts(apps, schema_editor):
    UserAccount = apps.get_model("pinax_stripe", "UserAccount")
    UserAccount.objects.all().delete()
    Customer = apps.get_model("pinax_stripe", "Customer")
    Customer.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pinax_stripe', '0016_remove-user-account-account'),
    ]

    operations = [
        migrations.RunPython(delete_user_accounts, reverse_code=migrations.RunPython.noop),
        migrations.AddField(
            model_name='useraccount',
            name='account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_accounts', related_query_name='user_account', to='pinax_stripe.Account'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='useraccount',
            unique_together=set([('user', 'account')]),
        ),
    ]
