from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
import time

class ka_account_payment_confirm_wizard(models.TransientModel):
    _name = "ka_account.payment.confirm.wizard"
    
    name = fields.Char('Name', default='Untuk membuat bukti kas atas Permohonan Pembayaran ini, Klik Tranfer Bukti Kas ')
        
    @api.multi
    def action_generate_bukti_kas(self):
        active_ids = self._context.get('active_ids', False)
        if active_ids:
            line_items = []
            data_entry = {}
            journal_id = False
            date_now = datetime.datetime.now().date()
            partner_payment = False
            type_payment = False
            partner = False
            for payment in self.env['ka_account.payment'].browse(active_ids):
                if payment.state != 'validate':
                    raise UserError('Pembuatan Bukti Kas hanya Hanya berlaku untuk Pengajuan Pembayaran dengan status Validate')
                
                if partner == False:
                    partner = payment.partner_id.id
                else:
                    if partner != payment.partner_id.id:
                        raise UserError('Pembuatan Bukti Kas hanya untuk Rekanan yang sama')
                    
                if payment.journal_voucher_id:
                    raise UserError('Pengajuan Nomor ' + payment.name + ' Sudah dibuatkan Bukti Kas.')
                        
                journal_voucher_obj = self.env['account.journal'].search([('type','=','bank')], limit=1)
                partner_payment = payment.partner_id.id
                type_payment = payment.type
       
                for journal in journal_voucher_obj:
                    journal_id = journal.id
                
                if payment.amount_dpp == 0:
                    raise UserError('Sorry, amount DPP cannot be 0')
                
                # set account_id take from vendor bills or directly from tagihan supplier (if vendor bill empty)
                invoice_account = payment.account_id.id
                label_vals_one = (_('%s; %s') % (payment.description or '-', payment.vendor_invoice_date or '-'))
                if payment.invoice_id:
                    invoice_account = payment.invoice_id.purchase_category_id.property_account_payable_id.id
                    label_vals_one = (_('NTB: %s; %s') % (payment.invoice_id.ka_number or '-', payment.vendor_invoice_date or '-'))
                
                vals_one = {
                    'invoice_id' : payment.invoice_id.id or False,
                    'amount' : payment.amount_dpp,
                    'name' : label_vals_one,
                    'account_id' : invoice_account,
                    'ka_payment_id': payment.id,
                }
                
                # if bail vendor payment
                if payment.is_bail_payment:
                    vals_one = {
                        'invoice_id' : payment.invoice_id.id,
                        'amount' : payment.amount_dpp,
                        'name' : (_('NTB: %s') % (payment.invoice_id.ka_number or '-',)),
                        'account_id' : self.env.user.company_id.default_bail_account_id.id,
                        'ka_payment_id': payment.id,
                    }
                    
                line_items.append((0, 0, vals_one))
                
                if payment.amount_ppn > 0:
                    default_ppn = self.env['ir.values'].get_default('product.template', 'supplier_taxes_id', company_id = self.env.user.company_id.id)
                    account_ppn = False
                    for ppn in self.env['account.tax'].browse(default_ppn):
                        account_ppn = ppn.account_id.id 
                                            
                    vals_ppn = {
                        'amount' : payment.amount_ppn,
                        'name' : (_('PPN: %s; %s') % (payment.tax_number or '-', payment.tax_date or '-')),
                        'account_id' : account_ppn,
                        'ka_payment_id': payment.id,
                    }
                    line_items.append((0, 0, vals_ppn))
                    
                if payment.amount_pph > 0:
                    vals_pph = {
                        'amount' : (payment.amount_pph)*-1,
                        'name' : (_('PPH: %s; %s') % (payment.no_kwitansi, payment.vendor_invoice_date)),
                        'account_id' : self.env.user.company_id.default_pph_account_id.id,
                        'ka_payment_id': payment.id,
                    }
                    line_items.append((0, 0, vals_pph))
                    
                if payment.amount_penalty > 0:
                    vals_penalty = {
                        'amount' : (payment.amount_penalty)*-1,
                        'name' : (_('Denda: %s; %s') % (payment.no_kwitansi, payment.vendor_invoice_date)),
                        'account_id' :  self.env.user.company_id.penalty_account_id.id,
                        'ka_payment_id': payment.id,
                    }
                    line_items.append((0, 0, vals_penalty))
                
                if payment.amount_bail > 0:
                    vals_bail = {
                        'amount' : (payment.amount_bail)*-1,
                        'name' : (_('Garansi: %s') % (payment.invoice_id.ka_number or '-',)),
                        'account_id' :  self.env.user.company_id.default_bail_account_id.id,
                        'ka_payment_id': payment.id,
                    }
                    line_items.append((0, 0, vals_bail))
            
            bank = self.env['res.partner.bank'].search([('partner_id','=',partner_payment)], order='priority asc, id desc', limit=1)
                             
            data_entry = {
                'journal_id' : journal_id,
                'description': '-',
                'partner_id': partner_payment,
                'partner_name': payment.partner_id.name,
                'partner_bank_id': bank.id,
                'partner_bank_acc': bank.acc_number,
                'date' : date_now,
                'printed' : False,
                'state' : 'draft',
                'voucher_lines' : line_items,
                'type' : type_payment
            }
 
            account_voucher_create = self.env['ka_account.voucher'].create(data_entry)

            for payment in self.env['ka_account.payment'].browse(active_ids):
                payment.write({'journal_voucher_id': account_voucher_create.id})
            
            return {
                'name': 'Journal Voucher',
                'res_model': 'ka_account.voucher',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': account_voucher_create.id,
                'target': 'current'
            }
