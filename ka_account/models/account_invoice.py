from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    def get_invoice_line_account(self, type, product, fpos, company):
        operating_unit_id = self._context.get('operating_unit_id')
        if operating_unit_id and operating_unit_id != self.env.user.company_id.partner_id.id:
            account_id = self.env['res.partner'].browse(operating_unit_id).property_account_receivable_id
            return account_id
        return super(AccountInvoiceLine, self).get_invoice_line_account(type, product, fpos, company)
    

class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    @api.multi
    def name_get(self):
        TYPES = {
            'out_invoice': _('Invoice'),
            'in_invoice': _('Vendor Bill'),
            'out_refund': _('Refund'),
            'in_refund': _('Vendor Refund'),
        }
        result = []
        for inv in self:
            if inv.type in ('in_invoice','in_refund'):
                result.append((inv.id, "%s %s" % (inv.ka_number or TYPES[inv.type], inv.name or '')))
            elif inv.type in ('out_invoice','out_refund'):
                result.append((inv.id, "%s %s" % (inv.number or TYPES[inv.type], inv.name or '')))
        return result

    @api.model
    def default_get(self, fields):
        res = super(AccountInvoice, self).default_get(fields)
        res['intercompany_invoice_type'] = 'lokal'
        res['source_partner_id'] = res.get('partner_id',False)
        return res
    
    @api.multi
    @api.depends('penalty_ids', 'penalty_ids.amount')
    def get_amount_penalty(self):
        for this in self:
            this.amount_penalty = sum(penalty.amount for penalty in this.penalty_ids)
 
    ka_number = fields.Char('Bill Number')
    purchase_category_id = fields.Many2one('ka_account.payable.category', 'Kategori Pembelian')
    intercompany_invoice_type = fields.Selection([
                        ('rkout', 'Tagihan Untuk Unit'), 
                        ('rkin', 'Tagihan Dari Unit'), 
                        ('lokal', 'Tagihan Lokal')
                        ],string="Jenis Tagihan", readonly=True)
    source_partner_id = fields.Many2one('res.partner', string="Vendor", readonly=True)
    operating_unit_id = fields.Many2one('res.partner', string="Unit/PG", domain=[('is_operating_unit', '=', True)])
    source_invoice_id = fields.Many2one('account.invoice', 'Source Invoice')
    dest_invoice_id = fields.Many2one('account.invoice', 'Destination Invoice')
    penalty_ids = fields.One2many('account.penalty', 'invoice_id', string='Penalty', copy=True)
    amount_penalty = fields.Monetary(string='Amount Penalty', readonly=True, compute='get_amount_penalty')
    ka_payment_ids = fields.One2many('ka_account.payment', 'invoice_id', 'Vendor Payments')
    payment_count = fields.Integer('# Payments', compute='get_count_payments')
    amount_paid = fields.Monetary('Paid', compute='get_amount_paid')
    
    
    @api.multi
    @api.depends('amount_total','residual')
    def get_amount_paid(self):
        for this in self:
            this.amount_paid = this.amount_total - this.residual
    
    @api.multi
    @api.depends('ka_payment_ids')
    def get_count_payments(self):
        for this in self:
            this.payment_count = len(this.ka_payment_ids)
    
    @api.multi
    def view_related_payments(self):
        for this in self:
            payment_ids = [payment.id for payment in this.ka_payment_ids]
            if len(payment_ids) == 1:
                return {
                    'name': 'Vendor Payment',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id' : payment_ids[0],
                    'type': 'ir.actions.act_window',
                    'res_model': 'ka_account.payment',
                    'target': 'current',  
                }
            else:
                return {
                    'name': 'Vendor Payments',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'domain' : [('id','in',payment_ids)],
                    'type': 'ir.actions.act_window',
                    'res_model': 'ka_account.payment',
                    'target': 'current',  
                }
    
    @api.multi
    def action_invoice_open(self):
        for this in self:
            active_model = self._context.get('active_model',False)
            is_manual_invoice = True
            for inv_line in this.invoice_line_ids:
                if inv_line.purchase_line_id:
                    is_manual_invoice = False
                    break
                
            if this.operating_unit_id and this.operating_unit_id.id != this.company_id.partner_id.id and is_manual_invoice == True and active_model != 'purchase.order' and active_model != 'sale.order':
                this.intercompany_invoice_type = 'rkout'
                inv_user = self.env.user.company_id.intercompany_user_id.id
                company_ctx = this.sudo(inv_user).operating_unit_id.get_company_ref()[0]

                inv_user2 = False
                for inv_company in self.env['res.company'].sudo(inv_user).search([('partner_id','=',this.operating_unit_id.id)], limit=1):
                    inv_user2 = inv_company.internal_user_id.id
                inv_type = self._context.get('type',False)
                inv_context = {'type': inv_type, 
                               'company_id': company_ctx.id}
                inv_model = self.env['account.invoice'].sudo(inv_user).with_context(inv_context)
                inv_account_id = False
                for inv_account in self.env['ka_account.payable.category'].sudo(inv_user2).with_context(inv_context).search([('code','=',this.purchase_category_id.code)]):
                    inv_account_id = inv_account.property_account_payable_id.id
                inv_vals = {'partner_id': this.company_id.partner_id.id,
                            'source_partner_id': this.partner_id.id,
                            'origin': this.origin,
                            'journal_id': inv_model._default_journal().id,
                            'user_id': inv_user,
                            'account_id': inv_account_id,
                            'company_id': company_ctx.id,
                            'purchase_category_id': this.purchase_category_id.id,
                            'intercompany_invoice_type': 'rkin',
                            'operating_unit_id': this.operating_unit_id.id,
                            'source_invoice_id': this.id,
                            'date_invoice': this.date_invoice,
                            'date_due': this.date_due}
                inv_create = inv_model.create(inv_vals)
                
                this.dest_invoice_id = inv_create.id
                inv_line_account = inv_create.sudo(inv_user2).with_context(company_id=company_ctx.id).operating_unit_id.property_account_receivable_id
                for line in this.invoice_line_ids:
                    data = {
                        'invoice_id': inv_create.id,
                        'purchase_line_id': line.purchase_line_id.source_order_line_id.id,
                        'name': line.name,
                        'origin': line.origin,
                        'uom_id': line.uom_id.id,
                        'product_id': line.product_id.id,
                        'account_id': inv_line_account.id,
                        'price_unit': line.price_unit,
                        'quantity': line.quantity,
                        'account_analytic_id': line.account_analytic_id.id,
                        'invoice_line_tax_ids': line.invoice_line_tax_ids.ids
                    }
                    self.env['account.invoice.line'].sudo(inv_user).with_context(inv_context).create(data)
                
                for penalty in this.penalty_ids:
                    data = {
                        'invoice_id': inv_create.id,
                        'product_id': penalty.product_id.id,
                        'amount': penalty.amount,
                        'due_date' : penalty.due_date,
                        'penalty_date': penalty.penalty_date,
                        'currency_id': penalty.currency_id.id,
                    }
                    self.env['account.penalty'].sudo(inv_user).with_context(inv_context).create(data)

                inv_create.sudo(inv_user).with_context(inv_context).action_invoice_open()
        return super(AccountInvoice,self).action_invoice_open()
    