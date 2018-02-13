from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class ka_account_account_periodic(models.Model):
    _name = "ka_account.account.periodic"
    _description = "Model to store master data of periodic processing in accounting"
    
    name = fields.Char('Name')
    account_src_id = fields.Many2one('account.account', 'Source Account')
    account_dest_id = fields.Many2one('account.account', 'Destination Account')
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True,
        default=lambda self: self.env['res.company']._company_default_get('ka_account.periodic.entry'))
    
    @api.one
    @api.constrains('account_src_id','account_dest_id')
    def _check_account_id(self):
        if self.account_src_id.id == self.account_dest_id.id:
            raise ValidationError(_('Source Account dan Destination Account tidak boleh sama!'))
    

class ka_account_move_periodic(models.Model):
    _name = "ka_account.move.periodic"
    _description = "Model to store queue of periodic accounting entries"
    _order = "state asc, date_planned asc"
    
    name = fields.Char('Name')
    journal_id = fields.Many2one('account.journal', 'Journal')
    date_planned = fields.Date('Scheduled Date', help='Date when journal entry will be posted')
    state = fields.Selection([('draft','Draft'),('post','Posted')], string='State', default='draft')
    move_src_id = fields.Many2one('account.move','Source Journal Entry')
    move_dest_id = fields.Many2one('account.move','Destination Journal Entry')
    account_periodic_id = fields.Many2one('ka_account.account.periodic','Periodic Account')
    move_line_periodic_ids = fields.One2many('ka_account.move.line.periodic', 'move_periodic_id', 'Journal Items Periodic')
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True,
        default=lambda self: self.env['res.company']._company_default_get('ka_account.periodic.entry'))
    
    @api.multi
    def post_entry(self):
        for move in self:
            internal_user_id = move.company_id.internal_user_id.id
            move_lines = []
            move_id = self.env['account.move'].sudo(internal_user_id).create({'journal_id': move.journal_id.id,
                                                                              'date': move.date_planned,
                                                                              'line_ids': move_lines})
            for line in move.move_line_periodic_ids:
                vals = {'name': line.name,
                        'account_id': line.account_id.id,
                        'partner_id': line.partner_id.id,
                        'analytic_account_id': line.analytic_account_id.id,
                        'credit': line.credit,
                        'debit': line.debit}
                move_lines.append((0,0,vals))
            move_id.line_ids = move_lines
            move_id.with_context({'no_check_periodic': True}).post()
            move.write({'move_dest_id': move_id.id, 'state': 'post'})
    
    @api.model
    def post_periodic_entries(self):
        _logger.info('========================== Starting Check Data Periodic Entries ==========================')
        date_today = datetime.strftime(datetime.now(),'%Y-%m-%d')
        move_periodic_src = self.env['ka_account.move.periodic'].search([('date_planned','=',date_today),('state','=','draft')])
        for move in move_periodic_src:
            move.post_entry()
            
    @api.model
    def create(self, vals):
        res = super(ka_account_move_periodic,self).create(vals)
        account_periodic = vals.get('account_periodic_id',False)
        if account_periodic:
            prev_account_periodic = self.env['ka_account.account.periodic'].browse(account_periodic)
            account_periodic_src = self.env['ka_account.account.periodic'].search([('account_src_id','=',prev_account_periodic.account_dest_id.id)])
            for next_account_periodic in account_periodic_src:
                prev_move_line = vals.get('move_line_periodic_ids')
                prev_debit_line = prev_move_line[0][2]
                prev_credit_line = prev_move_line[1][2]
                new_debit_account_id = new_credit_account_id = False
                if prev_debit_line.get('account_id') == next_account_periodic.account_src_id.id:
                    new_debit_account_id = next_account_periodic.account_dest_id.id
                    new_credit_account_id = next_account_periodic.account_src_id.id
                elif prev_credit_line.get('account_id') == next_account_periodic.account_src_id.id:
                    new_debit_account_id = next_account_periodic.account_src_id.id
                    new_credit_account_id = next_account_periodic.account_dest_id.id
                prev_date = datetime.strptime(vals.get('date_planned'), '%Y-%m-%d')
                new_date = datetime.strftime(datetime(prev_date.year + 1, prev_date.month, prev_date.day), '%Y-%m-%d')
                new_name = self.env['ir.sequence'].next_by_code("ka_account.move.periodic")
                new_debit_line  = (0,0,{'name': prev_debit_line.get('name'),
                                        'account_id': new_debit_account_id,
                                        'partner_id': prev_debit_line.get('partner_id',False),
                                        'analytic_account_id': prev_debit_line.get('analytic_account_id',False),
                                        'debit': prev_debit_line.get('debit')})
                new_credit_line = (0,0,{'name': prev_credit_line.get('name'),
                                        'account_id': new_credit_account_id,
                                        'partner_id': prev_credit_line.get('partner_id',False),
                                        'analytic_account_id': prev_credit_line.get('analytic_account_id',False),
                                        'credit': prev_credit_line.get('credit')})
                self.env['ka_account.move.periodic'].create({'name': new_name,
                                                             'journal_id': vals.get('journal_id'),
                                                             'date_planned': new_date,
                                                             'account_periodic_id': next_account_periodic.id,
                                                             'move_src_id': vals.get('move_src_id'),
                                                             'move_line_periodic_ids': [new_debit_line,new_credit_line]})
        return res


class ka_account_move_line_periodic(models.Model):
    _name = "ka_account.move.line.periodic"
    
    name = fields.Char('Label')
    move_periodic_id = fields.Many2one('ka_account.move.periodic', 'Journal Entry Periodic')
    account_id = fields.Many2one('account.account', 'Account')
    partner_id = fields.Many2one('res.partner', 'Partner')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True,
        default=lambda self: self.env['res.company']._company_default_get('ka_account.periodic.entry'))
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')
    
    