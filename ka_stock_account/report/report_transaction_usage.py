from openerp import models, fields, api, _
from datetime import datetime

class ReportTransactionReceive(models.AbstractModel):
    _name = 'report.ka_stock_account.report_stock_product_receive'
    _template = 'ka_stock_account.report_stock_product_receive'
    
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = 'stock.picking'
        docs = self.env[model].browse(data['ids'])
        
        for picking in docs:
            write_vals = {'date_printed': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            if picking.date_printed:
                if picking.note:
                    write_vals['note'] = picking.note + '\nCETAK ULANG'
                else:
                    write_vals['note'] = 'CETAK ULANG'
            picking.write(write_vals)
            
        docargs = {
            'data': data['form'],
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)