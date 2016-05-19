from django.http import HttpResponse
from django.utils.encoding import smart_text

from form_designer import settings
from form_designer.contrib.exporters import FormLogExporterBase

try:
    import xlwt
except ImportError:
    XLWT_INSTALLED = False
else:
    XLWT_INSTALLED = True


class XlsExporter(FormLogExporterBase):

    @staticmethod
    def export_format():
        return 'XLS'

    @staticmethod
    def is_enabled():
        return XLWT_INSTALLED

    def init_writer(self):
        self.wb = xlwt.Workbook()
        self.ws = self.wb.add_sheet(smart_text(self.model._meta.verbose_name_plural))
        self.rownum = 0

    def init_response(self):
        self.response = HttpResponse(content_type='application/ms-excel')
        self.response['Content-Disposition'] = 'attachment; filename=%s.xls' % (
            self.model._meta.verbose_name_plural
        )

    def writerow(self, row):
        for i, f in enumerate(row):
            self.ws.write(self.rownum, i, smart_text(f, encoding=settings.CSV_EXPORT_ENCODING))
        self.rownum += 1

    def close(self):
        self.wb.save(self.response)

    def export(self, request, queryset=None):
        return super(XlsExporter, self).export(request, queryset)
