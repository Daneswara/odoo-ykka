from openerp import models, fields, api, _
import datetime
import time
import math

class rekap_sp_wizard(models.TransientModel):
    _name = "rekap.sp.wizard"

    operating_unit_id = fields.Many2one('res.partner', string="Unit/PG", domain=[('is_operating_unit', '=', True)], 
        default=lambda self: self.env.user.company_id.partner_id.id)
    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')

    def get_print_date(self):
    	return datetime.datetime.now().strftime ("%d-%m-%Y")

    def get_print_time(self):
    	return time.strftime("%H:%M:%S")

    @api.multi
    def generate_pdf_rekap_sp(self):
    	report_obj = self.env['report']
        template = 'ka_purchase.template_report_rekap_sp'
        report = report_obj._get_report_from_name(template)
        domain = {
            'operating_unit_id': self.operating_unit_id.id,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
        }

        return report_obj.get_action(self, template, data=values)
    	

class rekap_sp_qweb(models.AbstractModel):
    _name = 'report.ka_purchase.template_report_rekap_sp'
    _template = 'ka_purchase.template_report_rekap_sp'

    def get_rekap_sp(self, unit_id, date_start, date_end):
    	start_date = datetime.datetime.strptime(date_start,'%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.datetime.strftime(start_date,'%Y-%m-%d %H:%M:%S')
        end_date = datetime.datetime.strptime(date_end,'%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.datetime.strftime(end_date,'%Y-%m-%d %H:%M:%S')
    	po_obj = self.env['purchase.order']
    	p_orders = po_obj.search([('operating_unit_id','=',unit_id.id),
    							('date_order','>=', start_date),
    							('date_order','<=', end_date)])
    	return p_orders

    @api.multi
    def render_html(self, docids, data=None):
    	report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_rekap_sp': self.get_rekap_sp,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)