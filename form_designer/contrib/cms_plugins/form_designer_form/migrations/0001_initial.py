# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial'),
        ('form_designer', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CMSFormDefinition',
            fields=[
                ('cmsplugin_ptr', models.OneToOneField(serialize=False, auto_created=True, primary_key=True, to='cms.CMSPlugin', parent_link=True)),
                ('form_definition', models.ForeignKey(verbose_name='form', to='form_designer.FormDefinition')),
            ],
            options={
                'abstract': False,
            },
            bases=('cms.cmsplugin',),
        ),
    ]
