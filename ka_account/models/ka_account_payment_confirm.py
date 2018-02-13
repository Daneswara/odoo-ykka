from odoo import models, fields, api, _
from odoo.exceptions import UserError
from openerp.addons.amount_to_text_id.amount_to_text import Terbilang

class ka_account_payment_confirm(models.Model):
    _name = "ka_account.payment.confirm"  
    _order = "confirm_date desc, id desc"
    _inherit = ['mail.thread']
    _template_voucher = 'ka_account.template_report_confirmed_payment'
    _template_slip_setoran= 'ka_account.template_slip_setoran_bank'
    
    @api.depends('journal_voucher_ids.total_amount')
    def compute_amount(self):
        for rec in self:
            amount_total = 0.0
            for line in rec.journal_voucher_ids:
                amount_total += line.total_amount
            rec.amount_total = amount_total
    
    name = fields.Char('Name', copy=False, default='New')
    confirm_date = fields.Date('Tanggal', copy=False, default=fields.Datetime.now)
    state = fields.Selection([('draft', 'Draft'),('confirm', 'Confirmed')], string='State', default='draft', track_visibility="always", copy=False)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    amount_total = fields.Monetary('Total Amount', compute='compute_amount', copy=False)
    printed = fields.Boolean('Printed', default=False, copy=False)
    journal_id = fields.Many2one('account.journal', 'Journal')
    journal_voucher_ids = fields.One2many('ka_account.voucher','confirmed_payment_id', 'Bukti Kas')
    ttd_dir = fields.Many2one('hr.employee', string='Tanda Tangan-1', default=lambda self: self.env.user.company_id.dept_dirut.manager_id)
    ttd_tuk = fields.Many2one('hr.employee', string='Tanda Tangan-2', default=lambda self: self.env.user.company_id.dept_dirprod.manager_id)
    
    @api.multi
    def action_confirm(self):
        for rec in self:
            vals = {'state': 'confirm'}
            if rec.name == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code("ka_account.payment.confirm")
            rec.write(vals)
            
            for voucher in rec.journal_voucher_ids:
                for payment in voucher.ka_payment_ids:
                    payment.write({'state': 'confirmed'})
            
#                 if voucher.type == 'internal':
#                     if voucher.journal_id.id == voucher.destination_journal_id.id:
#                         raise UserError('Sorry, The Journal and Destination Journal cannot be same.')
#                     bank_statement_obj_1=self.env['account.bank.statement'].search([('journal_id','=',voucher.journal_id.id), ('state','=','open')])
#                     
#                     if len(bank_statement_obj_1) > 1:
#                         raise UserError(_('You have more than 1 bank statements of journal %s with status New. Please make sure that you only have only 1.') % (voucher.journal_id.name,))
#                     elif len(bank_statement_obj_1) == 0:
#                         raise UserError(_('You have no bank statement of journal %s with status New. Please create the new one.') % (voucher.journal_id.name,))
#         
#                     for statement in bank_statement_obj_1:
#                         amount =  voucher.total_amount*-1
#                         vals = {
#                                 'date':voucher.date,
#                                 'name': voucher.description,
#                                 'partner_id':voucher.partner_id.id,
#                                 'amount' : amount,
#                                 'statement_id' : statement.id,
#                                 'journal_voucher_id' : voucher.id
#                                 }
#                         bank_statement_line_create = self.env['account.bank.statement.line'].create(vals)
#                     
#                     
#                     bank_statement_obj_2=self.env['account.bank.statement'].search([('journal_id','=',voucher.destination_journal_id.id), ('state','=','open')])
#                     
#                     if len(bank_statement_obj_2) > 1:
#                         raise UserError(_('You have more than 1 bank statements of journal %s with status New. Please make sure that you only have only 1.') % (voucher.destination_journal_id.name,))
#                     elif len(bank_statement_obj_2) == 0:
#                         raise UserError(_('You have no bank statement of journal %s with status New. Please create the new one.') % (voucher.destination_journal_id.name,))
#         
#                     for statement in bank_statement_obj_2:
#                         amount =  voucher.total_amount
#                         vals = {
#                                 'date':voucher.date,
#                                 'name': voucher.description,
#                                 'partner_id':voucher.partner_id.id,
#                                 'amount' : amount,
#                                 'statement_id' : statement.id,
#                                 'journal_voucher_id' : voucher.id
#                                 }
#                         bank_statement_line_create = self.env['account.bank.statement.line'].create(vals)
#                 else:     
#                     bank_statement_obj=self.env['account.bank.statement'].search([('journal_id','=',voucher.journal_id.id), ('state','=','open')])   
#                     
#                     if len(bank_statement_obj) > 1:
#                         raise UserError(_('You have more than 1 bank statements of journal %s with status New. Please make sure that you only have only 1.') % (voucher.journal_id.name,))
#                     elif len(bank_statement_obj) == 0:
#                         raise UserError(_('You have no bank statement of journal %s with status New. Please create the new one.') % (voucher.journal_id.name,))
#         
#                     for statement in bank_statement_obj:
#                         amount = 0.0
#                         if voucher.type == "inbound":
#                             amount =  voucher.total_amount
#                         elif voucher.type == "outbound":
#                             amount =  voucher.total_amount*-1  
#                         vals = {
#                                 'date':voucher.date,
#                                 'name': voucher.description,
#                                 'partner_id':voucher.partner_id.id,
#                                 'amount' : amount,
#                                 'statement_id' : statement.id,
#                                 'journal_voucher_id' : voucher.id
#                                 }
#                         bank_statement_line_create = self.env['account.bank.statement.line'].create(vals)
    
    @api.multi
    def action_set_draft(self):
        for rec in self:
            rec.write({'state': 'draft', 'printed': False})
            for voucher in rec.journal_voucher_ids:
                for payment in voucher.ka_payment_ids:
                    payment.write({'state': 'proposed'})
                    
                bank_statement_lines = self.env['account.bank.statement.line'].search([('journal_voucher_id','=',voucher.id)])
                if bank_statement_lines:
                    for stline in bank_statement_lines:
                        if stline.journal_entry_ids == []:
                            stline.unlink()
                        else:
                            raise UserError('Sorry, you cannot set status to draft because the bank statement line already reconciled.')
    
    @api.multi
    def unlink(self):
        for this in self:
            if this.state == 'confirm':
                raise UserError('Sorry, you can not delete confirmed payments. Please set to draft first.')
        return super(ka_account_payment_confirm, self).unlink()

    @api.multi
    def get_partners(self):
        partner_array = []
        for this in self:
            voucher_obj = this.journal_voucher_ids
            for voucher in voucher_obj:
                if voucher.partner_id not in partner_array:
                    partner_array.append(voucher.partner_id)
        return partner_array
    
    @api.multi
    def get_vouchers(self,partner):
        payment_array = []
        for this in self:
            voucher_obj = this.journal_voucher_ids
            for voucher in voucher_obj:
                if voucher.partner_id.id == partner.id:
                    payment_array.append(voucher)
        return payment_array
    
    @api.multi
    def do_print_selected_payment(self):
        # return
        for this in self:
            report_obj = self.env['report']
            template = self._template_voucher
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
                }
            self.mark_printed_document()
        return report_obj.get_action(self, template, data=datas)

    @api.multi
    def print_slip_setoran_bank(self):
        for this in self:
            report_obj = self.env['report']
            template = self._template_slip_setoran
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
                }
            self.mark_printed_document()
        return report_obj.get_action(self, template, data=datas)

    @api.multi
    def mark_printed_document(self):
        for this in self:
            if this.printed != True:
                vals = {'printed': True}
                this.write(vals)
            
    def amount_to_text_id(self, amount):
        return Terbilang(amount) + " Rupiah"

    