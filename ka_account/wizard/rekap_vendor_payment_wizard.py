from openerp import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import time
import pytz

class rekap_vendor_payment_wizard(models.TransientModel):
    _name = "rekap.vendor.payment.wizard"
    
    date_from = fields.Date('Dari Tanggal')
    date_to = fields.Date('Sampai Tanggal')
    
    @api.onchange('date_from')
    def onchange_date_from(self):
        self.date_to = self.date_from

    def get_print_date(self):
        return datetime.datetime.now().strftime ("%d-%m-%Y")

    def get_print_time(self):
        return time.strftime("%H:%M:%S")
    
    @api.multi
    def generate_pdf_rekap_vendor_payment(self):     
        report_obj = self.env['report']
        template = 'ka_account.template_report_rekap_vendor_payment'
        report = report_obj._get_report_from_name(template)
        domain = {
            'date_from': self.date_from,
            'date_to': self.date_to
        }
        values = {
            'ids': self.ids,
            'model': report.model,
            'form': domain
        }
        return report_obj.get_action(self, template, data=values)
        

class rekap_vendor_payment_qweb(models.AbstractModel):
    _name = 'report.ka_account.template_report_rekap_vendor_payment'
    _template = 'ka_account.template_report_rekap_vendor_payment'
    
    def get_time(self):
        user = self.env.user
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        today = pytz.utc.localize(datetime.now()).astimezone(tz)
        return today.strftime('%H:%M:%S')
    
    def get_rekap_vendor_payments(self, date_from, date_to):
        payment_obj = self.env['ka_account.payment']
        res = payment_obj.search([('payment_date','>=',date_from),
                                  ('payment_date','<=',date_to),
                                  ('state','!=','draft')], order='proposed_number asc')
        return res    
    
    def get_proposed_number_str(self, date_from, date_to):
        payment_obj = self.env['ka_account.payment']
        payment_data_asc = payment_obj.search([('payment_date','>=',date_from),('payment_date','<=',date_to)], order='proposed_number asc', limit=1)
        payment_data_desc = payment_obj.search([('payment_date','>=',date_from),('payment_date','<=',date_to)], order='proposed_number desc', limit=1)
        number_from = number_to = '-'
        if payment_data_asc:
            number_from = payment_data_asc.proposed_number
        if payment_data_desc:
            number_to = payment_data_desc.proposed_number
        res = number_from + ' s/d ' + number_to
        return res
    
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        docargs = {
            'data': data['form'],
            'get_proposed_number_str': self.get_proposed_number_str,
            'get_rekap_vendor_payments': self.get_rekap_vendor_payments,
            'get_time': self.get_time,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)
