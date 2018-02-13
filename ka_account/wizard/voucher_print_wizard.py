from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class voucher_print_wizard(models.TransientModel):
    _name = "ka_account.voucher.print.wizard"
    _description = "generate Bukti Penerimaan / Pengeluaran Kas"
    _template_voucher = 'ka_account.template_slip_penerimaan_kas'
    
    next_act = fields.Char('Name', default='Click button print below to continue print all selected documents')
    
    @api.multi
    def do_print_selected_voucher(self):
        report_obj = self.env['report']
        template = self._template_voucher
        report = report_obj._get_report_from_name(template)
        data = {}
        datas = {
            'ids': self.env.context.get('active_ids'),
            'model': report.model,
            'form': data,
            }
        self.mark_printed_document()
        print('--------------ACTIVE IDS :: ',self.env.context.get('active_ids'))
        return report_obj.get_action(self, template, data=datas)
       
    @api.multi
    def mark_printed_document(self):
        doc_id = self.env.context.get('active_ids', False)
        doc_obj = self.env['ka_account.voucher'].search([('id','in',doc_id)])
        for doc in doc_obj:
            if doc.printed != True:
                vals = {'printed': True}
                doc.write(vals)