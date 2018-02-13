from openerp import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import time
import math

class account_invoice_merge(models.TransientModel):
    _name = "account.invoice.merge.wiz"

    def do_merge_ntb(self):
        invoice_obj = self.env['account.invoice']
        inv_oldest = invoice_obj.browse(min(self._context.get('active_ids')))
        for inv_id in self._context.get('active_ids'):
            invoice = invoice_obj.browse(inv_id)
            if invoice.state != 'draft':
                raise UserError('You can not merge NTB that is not a draft. Please set it to draft before you merge it.')
            elif invoice.origin != inv_oldest.origin:
                raise UserError('Please select NTB which has same source document.')
                
        for line in self.env['account.invoice.line'].search([('invoice_id','in',self._context.get('active_ids'))]) :
            if line.invoice_id.id != inv_oldest.id:
                line.write({'invoice_id': inv_oldest.id})
        
        for penalty in self.env['account.penalty'].search([('invoice_id','in',self._context.get('active_ids'))]) :
            if penalty.invoice_id.id != inv_oldest.id:
                penalty.write({'invoice_id': inv_oldest.id})
                
        for inv_id in self._context.get('active_ids'):
            invoice = invoice_obj.browse(inv_id)
            if len(invoice.invoice_line_ids) == 0 :
                invoice.unlink()