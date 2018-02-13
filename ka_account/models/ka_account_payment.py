from odoo import models, fields, api, _
from odoo.exceptions import UserError
import urllib2 
import pytz
from datetime import datetime

class ka_account_payment(models.Model):
    _name = "ka_account.payment"        
    _description = "Account Payment for Kebon Agung"
    _inherit = ['mail.thread']
    _order = "payment_date desc, id desc"
    _template_proposal = "ka_account.template_report_proposed_payment"
    _template_bukti = "ka_account.report_buktipph"

    name = fields.Char('Name', default="Draft Payment", copy=False)
    proposed_number = fields.Char('No. Pengajuan : ', copy=False, default="/")
    type = fields.Selection([("outbound", "Send Money"),
    						 ("inbound", "Receive Money"),
                             ("internal", "Internal Transfer")], string = "Payment Type")
    no_npwp = fields.Char('NPWP')
    partner_id = fields.Many2one('res.partner', string="Partner")
    purchase_id = fields.Many2one('purchase.order', string="Nomor SP")
    invoice_id = fields.Many2one('account.invoice', string="No. NTB/Invoice")
    account_id = fields.Many2one('account.account', string="Acc Hutang/Biaya")
    no_kwitansi = fields.Char('No. Kwitansi')
    vendor_invoice_date = fields.Date("Tanggal Kwitansi")
    amount = fields.Monetary("Nilai NTB")
    payment_date = fields.Date("Tgl. Pengajuan", default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    efaktur_url = fields.Char('URL Barcode')
    tax_number = fields.Char('No. Faktur')
    tax_date = fields.Date("Tanggal Faktur")
    amount_dpp = fields.Monetary("DPP")
    amount_ppn = fields.Monetary("PPN")
    amount_invoice = fields.Monetary("Total")
    percent_pph = fields.Selection([('0.0025','0.25%'),
                                    ('0.02','2%'),
                                    ('0.03','3%'),
                                    ('0.04','4%'),
                                    ('0.05','5%'),
                                    ('0.06','6%'),
                                    ('0.10','10%'),
                                    ('0.15','15%')], 'PPH (%)')
    amount_pph = fields.Monetary('PPH')
    amount_penalty = fields.Monetary("Denda")
    amount_bail = fields.Monetary("Garansi")
    description = fields.Text('Description')
    state = fields.Selection([("draft", "Draft"),
                              ("proposed", "Proposed"),
                              ("validate", "Validate"),
                              ("confirmed", "Confirmed"),
                              ("paid", "Paid")],
                                string = "Status", default="draft", track_visibility="always", copy=False)
    journal_voucher_id = fields.Many2one("ka_account.voucher", string="Journal Voucher", copy=False)
    printed = fields.Boolean("Printed", copy=False)
    is_bail_payment = fields.Boolean('Pembayaran Garansi', default=False)
    date_paid = fields.Date('Terbayar Pada')
    date_due = fields.Date('Jatuh Tempo')
    date_bail_end = fields.Date('Tgl Garansi Habis')
    # information about related PO
    purchase_order_date = fields.Date('Tanggal SP', compute='get_purchase_information')
    purchase_date_planned = fields.Date('Tanggal Batas', compute='get_purchase_information')
    purchase_amount_total = fields.Monetary('Nilai SP', compute='get_purchase_information')
    purchase_amount_paid = fields.Monetary('Sudah Terbayar', compute='get_purchase_information')
    purchase_amount_unpaid = fields.Monetary('Sisa', compute='get_purchase_information')
    ntb_number = fields.Char(string='Nomor NTB', related='invoice_id.ka_number')
    
    @api.model
    def create(self, vals):
        if 'name' in vals:
            new_name = vals.get('name')
            if new_name != 'Draft Payment':
                new_name = new_name.split('/')
                vals.update({'proposed_number': new_name[len(new_name)-1]})
        return super(ka_account_payment,self).create(vals)
    
    @api.multi
    def write(self, vals):
        if 'name' in vals:
            new_name = vals.get('name')
            new_name = new_name.split('/')
            vals.update({'proposed_number': new_name[len(new_name)-1]})
        return super(ka_account_payment,self).write(vals)
    
    @api.multi
    @api.depends('purchase_id','amount_dpp')
    def get_purchase_information(self):
        for this in self:
            this.purchase_order_date = False
            this.purchase_date_planned = False
            if this.purchase_id:
                user = self.env.user
                tz = pytz.timezone(user.tz) if user.tz else pytz.utc
                
                po_date = datetime.strptime(this.purchase_id.date_order, '%Y-%m-%d %H:%M:%S')
                po_date = pytz.utc.localize(po_date).astimezone(tz)
                this.purchase_order_date = datetime.strftime(po_date, '%Y-%m-%d')
                 
                sch_date = datetime.strptime(this.purchase_id.date_planned, '%Y-%m-%d %H:%M:%S')
                sch_date = pytz.utc.localize(sch_date).astimezone(tz)
                this.purchase_date_planned = datetime.strftime(sch_date, '%Y-%m-%d')
                
            this.purchase_amount_total = this.purchase_id.amount_total
            payment_src = self.env['ka_account.payment'].search([('purchase_id','=',this.purchase_id.id),
                                                                 ('state','!=','draft')])
            this.purchase_amount_paid = sum((payment.amount_dpp - payment.amount_bail) for payment in payment_src)
            this.purchase_amount_unpaid = this.purchase_amount_total - this.purchase_amount_paid
            
    @api.onchange('efaktur_url')
    def _onchange_url(self):
        if not self.efaktur_url or self.efaktur_url == '' or self.efaktur_url[0:7] != 'http://':
            self.tax_number = ''
            self.tax_date = ''
            self.amount_dpp = ''
            self.amount_ppn = ''
            return

        self.result = ''

        try:
            urllib2.urlopen(self.efaktur_url)
        except urllib2.HTTPError as err:
            if err.code == 404:
                self.tax_number = ''
                self.tax_date = ''
                self.amount_dpp = ''
                self.amount_ppn = ''
                return
            else:
                raise

        self.result = urllib2.urlopen(self.efaktur_url).read()

        if self.result == '' or not self.result:
            return

        self.tax_number = self.find_between(self.result,"<nomorFaktur>","</nomorFaktur>")
        self.no_npwp = self.find_between(self.result,"<npwpPenjual>","</npwpPenjual>")
        self.tax_date = datetime.strftime(datetime.strptime(self.find_between(self.result,"<tanggalFaktur>","</tanggalFaktur>"), "%d/%m/%Y"), "%Y-%m-%d")
        self.amount_dpp = float(self.find_between(self.result,"<jumlahDpp>","</jumlahDpp>"))
        self.amount_ppn = float(self.find_between(self.result,"<jumlahPpn>","</jumlahPpn>"))
    
    @api.onchange('percent_pph')
    def onchange_percent_pph(self):
        if not self.is_bail_payment:
            self.amount_pph = self.amount_dpp * float(self.percent_pph)
    
    @api.onchange('amount_dpp','amount_ppn')
    def onchange_amount(self):
        self.amount_invoice = self.amount_dpp + self.amount_ppn

    @api.onchange('no_npwp')
    def _onchange_get_partner_id(self):
        if self.no_npwp:
            cari_npwp = self.env['res.partner'].search([('no_npwp', '=', self.no_npwp)],limit=1)
            self.partner_id = cari_npwp
    
    @api.onchange('purchase_id')
    def _onchange_purchase_id(self):
        domain = {}
        invoice_ids = [invoice.id for invoice in self.purchase_id.invoice_ids]
        domain['invoice_id'] = [('id','in',invoice_ids),
                                ('type','=',self._context.get('invoice_type')),
                                ('state','=','open'), 
                                '|', ('partner_id', '=',self.partner_id.id), 
                                ('source_partner_id', '=',self.partner_id.id)]
        return {'domain': domain}
    
    @api.multi
    def unlink(self):
        for this in self:
            if this.state != 'draft':
                raise UserError('PERHATIAN, Selain draft pengajuan tidak di-hapus')
        return super(ka_account_payment, self).unlink()

    def find_between( self,s, first, last ):
        try:
            start = s.index( first ) + len( first )
            end = s.index( last, start )
            return s[start:end]
        except ValueError:
            return ""
        
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id:
            self.amount = self.invoice_id.residual
            self.amount_penalty = self.invoice_id.amount_penalty
            self.account_id = self.invoice_id.purchase_category_id.property_account_payable_id.id
        else:
            self.amount = 0
            self.amount_penalty = 0
            self.account_id = False

    @api.multi
    def action_view_journal_voucher(self):
        for this in self:
            return {
                'name': 'Journal Voucher',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id' : this.journal_voucher_id.id,
                'type': 'ir.actions.act_window',
                'res_model': 'ka_account.voucher',
                'target': 'current',  
            }

    @api.multi
    def propose_payment(self):
        for this in self:
            vals = {'state': 'proposed'}
            if this.name == 'Draft Payment':
                vals['name'] = self.env['ir.sequence'].next_by_code("ka_account.payment")
            this.write(vals)
        return True
    
    @api.multi
    def action_validate_payment(self):
        for this in self:
            if not self.is_bail_payment:
                if not this.invoice_id:
                    if not this.account_id:
                        raise UserError('Sebelum di-Validate, Perkiraan / NTB harus diisi')
            this.state='validate'
        return True
    
    @api.multi
    def set_draft_payment(self):
        for this in self:
            vals = {'state': 'draft', 'printed': False}
            if this.journal_voucher_id:
                vals['journal_voucher_id'] = False
            this.write(vals)
        return True

    @api.multi
    def do_print_selected_document(self):
        for this in self:
            report_obj = self.env['report']
            template = self._template_proposal
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

    @api.multi
    def get_po_number(self):
        po_number = False
        for this in self:
            po_number = this.purchase_id.name
        return po_number + ' ' 
    
    @api.multi
    def get_po_date(self):
        po_date = False
        for this in self:
            po_date = this.purchase_order_date
        return po_date
                