from openerp import models, fields, api, _

class ReportProposalPembayaran(models.AbstractModel):
    _name = 'report.ka_account.template_report_proposed_payment'
    _template = 'ka_account.template_report_proposed_payment'
    
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