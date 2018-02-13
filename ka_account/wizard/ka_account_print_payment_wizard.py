from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import time
import pytz

class ka_account_print_payment_wizard(models.TransientModel):
    _name = "ka_account.print.payment.wizard"
    _description = "print selected Vendor Payments"
    
    text = fields.Char('Text', default='Click button Generate PDF below to continue print all selected documents')

    @api.multi
    def print_selected_payment(self):
        temp_po = temp_partner = False
        for payment in self.env['ka_account.payment'].browse(self._context.get('active_ids')):
            if temp_po == False:
                temp_po = payment.purchase_id.id
            else:
                if temp_po != payment.purchase_id.id:
                    raise UserError('Maaf, Nomor SP yang anda pilih tidak sama.')
                
            if temp_partner == False:
                temp_partner = payment.partner_id.id
            else:
                if temp_partner != payment.partner_id.id :
                    raise UserError('Maaf, Partner yang anda pilih tidak sama.')

        report_obj = self.env['report']
        template = "ka_account.template_report_proposed_payment"
        report = report_obj._get_report_from_name(template)
        data = {}
        datas = {
            'ids': self.env.context.get('active_ids'),
            'model': report.model,
            'form': data,
        }
        return report_obj.get_action(self, template, data=datas)


class print_payments(models.AbstractModel):
    _name = 'report.ka_account.template_report_proposed_payment'
    _template = 'ka_account.template_report_proposed_payment'
    
#     get one payment for general data. 'param' is a set of selected payments
    def get_general_data(self, param):
        payment = False
        for p in param:
            payment = p
            break
        return payment
    
    def get_po(self, param):
        res = 0.0
        for p in param:
            if p.purchase_id:
                res = p.purchase_id.amount_total
                break
        return res
    
    def get_penalty_details(self, param):
        res = list()
        for p in param:
            penalty = self.env['account.penalty'].search([('invoice_id','=',p.invoice_id.id)], limit=1)
            if penalty:
                data = {'no_sp': p.invoice_id.origin,
                        'tgl_sp': datetime.strftime(datetime.strptime(p.invoice_id.purchase_date_order, '%Y-%m-%d %H:%M:%S'),'%Y-%m-%d'),
                        'no_ntb': p.invoice_id.ka_number,
                        'tgl_ntb': p.invoice_id.date_invoice,
                        'tgl_serah': p.purchase_id.date_planned,
                        'tgl_terima': penalty.penalty_date,
                        'nilai_ntb': p.amount_dpp + p.amount_ppn - p.amount_bail,
                        'penalty': p.amount_penalty}
                res.append(data)
        return res
    
    def get_total_penalty(self, param):
        penalty = 0
        for p in param:
            penalty += p.amount_penalty
        return penalty
    
    def get_payment_history(self, param):
        res = list()
        po = False
        for p in param:
            if p.purchase_id:
                po = p.purchase_id
                break
        
        payments = self.env['ka_account.payment'].search([('purchase_id','=',po.id), 
                                                          ('state','!=','draft')], order='payment_date desc')
                
        for item in payments:
            user = self.env.user
            tz = pytz.timezone(user.tz) if user.tz else pytz.utc
            tax_date = datetime.strptime(item.vendor_invoice_date, '%Y-%m-%d')
            tax_date = pytz.utc.localize(tax_date).astimezone(tz)
            tax_date = datetime.strftime(tax_date, '%d-%m-%Y')
            
            sum1 = item.amount_dpp + item.amount_ppn - item.amount_bail
            sum2 = sum1 - item.amount_pph
            vals = {
                'tax_date': tax_date,
                'no_aju': item.proposed_number,
                'description': item.description,
                'amount_dpp': item.amount_dpp,
                'amount_ppn': item.amount_ppn,
                'sum1': sum1,
                'pph': item.amount_pph,
                'sum2': sum2,
                'garansi': item.amount_bail
            }
            res.append(vals)
        res.sort(key=lambda x: x['no_aju'],reverse=True)
        return res

    
    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        model = data['model']
        docs = self.env[model].browse(data['ids'])
        
        user = self.env.user
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        print_time = time.strftime('%H:%M:%S')
        print_time = datetime.strptime(print_time,'%H:%M:%S')
        print_time = pytz.utc.localize(print_time).astimezone(tz)
        print_time = datetime.strftime(print_time,'%H:%M:%S')
        
        docargs = {
            'data': data['form'],
            'get_general_data': self.get_general_data,
            'print_time': print_time,
            'payment_log': self.get_payment_history,
            'po': self.get_po,
            'penalty_details': self.get_penalty_details,
            'penalty':self.get_total_penalty,
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
        }
        return report_obj.render(self._template, docargs)
    
    