# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('form_designer', ' 0002_reply_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='formdefinition',
            name='html_default_template',
            field=models.BooleanField(default=False, help_text='If enabled, the default email template will be in HTML instead of plain format.', verbose_name='default email template in HTML'),
        ),
    ]
