from __future__ import unicode_literals

import csv

from django.http import HttpResponse
from django.utils import six
from django.utils.encoding import force_bytes

from form_designer import settings
from form_designer.contrib.exporters import FormLogExporterBase


class CsvExporter(FormLogExporterBase):

    @staticmethod
    def export_format():
        return 'CSV'

    def init_writer(self):
        self.writer = csv.writer(self.response, delimiter=settings.CSV_EXPORT_DELIMITER)

    def init_response(self):
        self.response = HttpResponse(content_type='text/csv')
        self.response['Content-Disposition'] = (
            'attachment; filename=%s.csv' % self.model._meta.verbose_name_plural
        )

    def writerow(self, row):
        if six.PY2:
            row = [force_bytes(value, encoding=settings.CSV_EXPORT_ENCODING) for value in row]
        self.writer.writerow(row)

    def export(self, request, queryset=None):
        return super(CsvExporter, self).export(request, queryset)
