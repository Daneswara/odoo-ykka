from openerp import models, fields, api, _
 

class SerahTerimaTetesHarian(models.AbstractModel):
    _name = 'report.ka_stock.template_hasil_timbang_tetes'
    _template = 'ka_stock.template_hasil_timbang_tetes'
    
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(data['ids'])
        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)

class SerahTerimaGulaHarian(models.AbstractModel):
    _name = 'report.ka_stock.template_hasil_timbang_gula'
    _template = 'ka_stock.template_hasil_timbang_gula'
    
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(data['ids'])
        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)

 
class LaporanHarianGula(models.AbstractModel):
    _name = 'report.ka_stock.template_laporan_harian_gula'
    _template = 'ka_stock.template_laporan_harian_gula'
    
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(data['ids'])
        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)


class LaporanHarianAmpas(models.AbstractModel):
    _name = 'report.ka_stock.template_laporan_harian_ampas'
    _template = 'ka_stock.template_laporan_harian_ampas'
    
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(data['ids'])
        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)