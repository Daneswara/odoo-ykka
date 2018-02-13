from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    
    @api.multi
    def open_cashbox_start(self):
        for this in self:
            if not this.cashbox_start_id:
                starting_cashbox = self.env['account.bank.statement.cashbox'].create({})
                this.cashbox_start_id = starting_cashbox
                
            nominal_obj = self.env["account.cash.nominal"].search([], order="sequence asc")
            for nominal in nominal_obj:
                if this.cashbox_start_id.cashbox_lines_ids == []:
                    self.env['account.cashbox.line'].create({'cashbox_id' : this.cashbox_start_id.id,
                                                             'cash_nominal_id' : nominal.id,
                                                             'coin_value' : nominal.value})
                    
                else:
                    cashbox_lines = self.env['account.cashbox.line'].search([('cashbox_id','=', this.cashbox_start_id.id),
                                                                             ('cash_nominal_id', '=', nominal.id)])
                    
                    if not cashbox_lines:
                        self.env['account.cashbox.line'].create({'cashbox_id' : this.cashbox_start_id.id,
                                                                 'cash_nominal_id' : nominal.id,
                                                                 'coin_value' : nominal.value})
                        
            add_context = {'balance': 'start',
                           'bank_statement_id': this.id,
                           'cashbox_id': this.cashbox_start_id.id}
            
            return {
                'name':'Statement Cashbox Start',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.bank.statement.cashbox',
                'type': 'ir.actions.act_window',
                'res_id': this.cashbox_start_id.id,
                'context': add_context,
                'target': 'new'
                    }

    @api.multi
    def open_cashbox_end(self):
        for this in self:
            if not this.cashbox_end_id:
                ending_cashbox = self.env['account.bank.statement.cashbox'].create({})
                this.cashbox_end_id = ending_cashbox
                
            nominal_obj = self.env["account.cash.nominal"].search([], order="sequence asc")
            for nominal in nominal_obj:
                if this.cashbox_end_id.cashbox_lines_ids == []:
                    self.env['account.cashbox.line'].create({'cashbox_id' : this.cashbox_end_id.id,
                                                             'cash_nominal_id' : nominal.id,
                                                             'coin_value' : nominal.value})
                    
                else:
                    cashbox_lines = self.env['account.cashbox.line'].search([('cashbox_id','=', this.cashbox_end_id.id),
                                                                             ('cash_nominal_id', '=', nominal.id)])
                    
                    if not cashbox_lines:
                        self.env['account.cashbox.line'].create({'cashbox_id' : this.cashbox_end_id.id,
                                                                 'cash_nominal_id' : nominal.id,
                                                                 'coin_value' : nominal.value})
                        
            add_context = {'balance': 'end',
                           'bank_statement_id': this.id,
                           'cashbox_id': this.cashbox_end_id.id}
            
            return {
                'name':'Statement Cashbox End',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.bank.statement.cashbox',
                'type': 'ir.actions.act_window',
                'res_id': this.cashbox_end_id.id,
                'context': add_context,
                'target': 'new'
            }
    
    @api.multi
    def action_pull_bukti_kas(self):
        for this in self:
            statement_line_src = self.env['account.bank.statement.line'].search([('statement_id.journal_id','=',this.journal_id.id),
                                                                                 ('journal_voucher_id','!=',False)])
            voucher_src = []
            start_date = this.date + ' 00:00:00'
            end_date = this.date + ' 23:59:59'
            if statement_line_src:
                voucher_ids = [line.journal_voucher_id.id for line in statement_line_src]
                voucher_src = self.env['ka_account.voucher'].search([('state','=','approved'),
                                                                     ('date_approve','>=',start_date),
                                                                     ('date_approve','<=',end_date),
                                                                     ('id','not in',voucher_ids),
                                                                     ('journal_id','=',this.journal_id.id)], order='date_approve asc')
            else:
                voucher_src = self.env['ka_account.voucher'].search([('state','=','approved'),
                                                                     ('date_approve','>=',start_date),
                                                                     ('date_approve','<=',end_date),
                                                                     ('journal_id','=',this.journal_id.id)], order='date_approve asc')
            sequence = 0
            lines_seq = [line.sequence for line in this.line_ids]
            if lines_seq != []:
                sequence = max(lines_seq)
                
            for voucher in voucher_src:
                sequence += 1
                amount = voucher.total_amount
                if voucher.type != 'inbound':
                    amount = amount * -1
                self.env['account.bank.statement.line'].create({'sequence': sequence,
                                                                'statement_id': this.id,
                                                                'date': this.date,
                                                                'name': voucher.description,
                                                                'journal_voucher_id': voucher.id,
                                                                'partner_id': voucher.partner_id.id,
                                                                'amount': amount})
                
    @api.multi
    def action_reconcile_all_statement_lines(self):
        for this in self:
            for line in this.line_ids:
                if not line.journal_entry_ids:
                    if line.journal_voucher_id:
                        line.process_reconcile_bukti_kas([line.journal_voucher_id.id])
                    elif line.payment_confirm_id:
                        line.reconcile_proposed_payment()
                    

class AccountMoveLine(models.Model):
    _inherit = "account.bank.statement.line"
    
    journal_entry_ids = fields.One2many('account.move', 'statement_line_id', 'Journal Entries', copy=False, readonly=False)
    journal_voucher_id = fields.Many2one("ka_account.voucher", string="Bukti Kas")
    payment_confirm_id = fields.Many2one('ka_account.payment.confirm', 'No. Pengajuan Bank')
        
    @api.multi
    def get_data_for_reconciliation_widget(self, excluded_ids=None):
        """ Returns the data required to display a reconciliation widget, for each statement line in self """
        excluded_ids = excluded_ids or []
        ret = []

        for st_line in self:
            aml_recs = st_line.get_reconciliation_proposition(excluded_ids=excluded_ids)
            target_currency = st_line.currency_id or st_line.journal_id.currency_id or st_line.journal_id.company_id.currency_id
            rp = aml_recs.prepare_move_lines_for_reconciliation_widget(target_currency=target_currency, target_date=st_line.date)
            excluded_ids += [move_line['id'] for move_line in rp]
            if st_line.journal_voucher_id:
                rp_voucher = st_line.journal_voucher_id.voucher_lines.prepare_voucher_lines_for_reconciliation_widget(target_currency=target_currency, target_date=st_line.date)
                rp.append(rp_voucher)
                
                idx = len(rp) - 1
                ret.append({
                    'st_line': st_line.get_statement_line_for_reconciliation_widget(),
                    'reconciliation_proposition': rp[idx]
                })
            else:
                if not st_line.payment_confirm_id:
                    ret.append({
                        'st_line': st_line.get_statement_line_for_reconciliation_widget(),
                        'reconciliation_proposition': rp
                    })            
        return ret
    
    @api.multi
    def process_reconcile_bukti_kas(self, journal_voucher_ids):
        for voucher in self.env['ka_account.voucher'].search([('id','in',journal_voucher_ids)], order='date_approve asc'):
            for this in self:
                voucher.process_voucher_reconciliation_move_link(this, this.date)
            # find paid invoice after reconcile
            invoice_ids = []
            for payment in voucher.ka_payment_ids:
                if payment.invoice_id.state == 'paid' and payment.invoice_id.id not in invoice_ids:
                    invoice_ids.append(payment.invoice_id.id)
            # create draft payment for bail (garansi)
            if invoice_ids != []:
                for invoice in self.env['account.invoice'].browse(invoice_ids):
                    amount_bail = sum(payment.amount_bail for payment in invoice.ka_payment_ids)
                    # search bail payment that already created for related invoice
                    payment_bail_src = self.env['ka_account.payment'].search([('invoice_id','=',invoice.id),('is_bail_payment','=',True)])
                    amount_payment_bail = sum(payment_bail.amount_dpp for payment_bail in payment_bail_src)
                    amount_bail_rest = amount_bail - amount_payment_bail
                    # if payment bail is not created yet
                    if amount_bail_rest > 0:
                        purchase_id = False
                        for invoice_line in invoice.invoice_line_ids:
                            if invoice_line.purchase_id:
                                purchase_id = invoice_line.purchase_id
                                break
                        # get the latest paid date in payment with garansi > 0
                        date_due = False
                        payment_src = self.env['ka_account.payment'].search([('invoice_id','=',invoice.id),
                                                                             ('state','=','paid'),
                                                                             ('amount_bail','>',0)],
                                                                            order='date_paid asc', limit=1)
                        if payment_src:
                            date_paid = datetime.strptime(payment_src.date_bail_end, '%Y-%m-%d')
                            date_due = date_paid + timedelta(6*365/12)
                            date_due = datetime.strftime(date_due, '%Y-%m-%d')
                            
                        self.env['ka_account.payment'].create({'partner_id': invoice.partner_id.id,
                                                               'purchase_id': purchase_id.id,
                                                               'invoice_id': invoice.id,
                                                               'amount': invoice.amount_total,
                                                               'type': 'outbound',
                                                               'description': 'Pembayaran Garansi ' + purchase_id.name,
                                                               'amount_dpp': amount_bail_rest,
                                                               'amount_invoice': amount_bail_rest,
                                                               'date_due': date_due,
                                                               'is_bail_payment': True})        

    @api.multi
    def process_reconciliations(self, data):
        """ Handles data sent from the bank statement reconciliation widget (and can otherwise serve as an old-API bridge)

            :param list of dicts data: must contains the keys 'counterpart_aml_dicts', 'payment_aml_ids' and 'new_aml_dicts',
                whose value is the same as described in process_reconciliation except that ids are used instead of recordsets.
        """
        AccountMoveLine = self.env['account.move.line']
        for st_line, datum in zip(self, data):
            if not st_line.journal_voucher_id:
                payment_aml_rec = AccountMoveLine.browse(datum.get('payment_aml_ids', []))
                for aml_dict in datum.get('counterpart_aml_dicts', []):
                    aml_dict['move_line'] = AccountMoveLine.browse(aml_dict['counterpart_aml_id'])
                    del aml_dict['counterpart_aml_id']
                st_line.process_reconciliation(datum.get('counterpart_aml_dicts', []), payment_aml_rec, datum.get('new_aml_dicts', []))
            else:
                balance = abs(st_line.amount) - abs(st_line.journal_voucher_id.total_amount)
                if balance <> 0:
                    raise UserError('Jumlah Bukti Kas : ' + st_line.journal_voucher_id.name + ' dan Rekening koran harus sama')
                st_line.process_reconcile_bukti_kas([st_line.journal_voucher_id.id])       
    
    @api.multi
    def reconcile_proposed_payment(self):
        for this in self:
            if abs(this.amount) != abs(this.payment_confirm_id.amount_total):
                raise UserError('Jumlah amount harus sama dengan jumlah amount di pengajuan bank!')
            voucher_ids = [voucher.id for voucher in this.payment_confirm_id.journal_voucher_ids]
            this.process_reconcile_bukti_kas(voucher_ids)
                
    @api.multi
    def button_cancel_reconciliation(self):
        moves_to_unbind = self.env['account.move']
        moves_to_cancel = self.env['account.move']
        related_payments = []
        related_vouchers = []
        for st_line in self:
            moves_to_unbind |= st_line.journal_entry_ids
            moves_to_cancel |= st_line.journal_entry_ids
            # if journal voucher is exist
            if st_line.journal_voucher_id:
                if st_line.journal_voucher_id.id not in related_vouchers:
                    related_vouchers.append(st_line.journal_voucher_id.id)
                for payment in st_line.journal_voucher_id.ka_payment_ids:
                    if payment.id not in related_payments:
                        related_payments.append(payment.id)
            #if use proposed to bank
            if st_line.payment_confirm_id:
                for voucher in st_line.payment_confirm_id.journal_voucher_ids:
                    if voucher.id not in related_vouchers:
                        related_vouchers.append(voucher.id)
                    for payment in voucher.ka_payment_ids:
                        if payment.id not in related_payments:
                            related_payments.append(payment.id)
        moves_to_unbind = moves_to_unbind - moves_to_cancel

        if moves_to_unbind:
            moves_to_unbind.write({'statement_line_id': False})
            for move in moves_to_unbind:
                move.line_ids.filtered(lambda x:x.statement_id == st_line.statement_id).write({'statement_id': False})

        if moves_to_cancel:
            for move in moves_to_cancel:
                move.line_ids.remove_move_reconcile()
            moves_to_cancel.button_cancel()
            moves_to_cancel.unlink()
            
        if related_payments != []:
            for payment in self.env['ka_account.payment'].browse(related_payments):
                payment.write({'state': 'confirmed'})
        
        if related_vouchers != []:
            for voucher in self.env['ka_account.voucher'].browse(related_vouchers):
                voucher.write({'state': 'approved'})
    
    
    @api.onchange('journal_voucher_id')
    def _onchange_journal_voucher_id(self):
        self.partner_id = self.journal_voucher_id.partner_id
        

class AccountBankStmtCashWizard(models.Model):
    _inherit = 'account.bank.statement.cashbox'

    unbooked_bill = fields.Float(string="Bon yang belum Diperhitungkan", digits=0, readonly=False)
    
    @api.multi
    def validate(self):
        bnk_stmt_id = self.env.context.get('bank_statement_id', False) or self.env.context.get('active_id', False)
        bnk_stmt = self.env['account.bank.statement'].browse(bnk_stmt_id)
        total = 0.0
        for this in self:
            for lines in this.cashbox_lines_ids:
                total += lines.subtotal
            total = total + this.unbooked_bill
          
        if self.env.context.get('balance', False) == 'start':
            #starting balance
            bnk_stmt.write({'balance_start': total, 'cashbox_start_id': self.id})
        else:
            #closing balance
            bnk_stmt.write({'balance_end_real': total, 'cashbox_end_id': self.id})
        return {'type': 'ir.actions.act_window_close'}
    
    