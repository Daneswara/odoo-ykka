from odoo import api, fields, models, _
import time, datetime, calendar
import csv
import base64
import pytz

class KaAccountPPh(models.Model):
    _name = "ka_account.pph.periode"        
    _description = "Header PPh"
        
    @api.model      
    def _get_year_in_move(self):
        res = []
        self.env.cr.execute("select date_part('year', date) from account_move_line group by 1")
        row = self.env.cr.fetchall()
        if row:
            res = [(str(int(y[0])), str(int(y[0]))) for y in row]
        return res
        
    name = fields.Char(string='Periode', size=7, compute='_compute_all', store=True)
    sequence = fields.Integer('No Urut Mulai', help='Urutan yang akan dijadikan sebagai nomor bukti potong, mis:051/XI/PPh/2017  Maka No Urut adalah 51')
    suffix = fields.Char('Akhiran', help='Akhiran dari nomor bukti potong, mis:002/XI/PPh/2017 maka Akhiran adalah /XI/PPh/2017')
    month = fields.Selection([
        ('01', "Januari"),
        ('02', "Pebruari"),
        ('03', "Maret"),
        ('04', "April"),
        ('05', 'Mei'),
        ('06', "Juni"),
        ('07', "Juli"),
        ('08', "Agustus"),
        ('09', "September"),
        ('10', "Oktober"),
        ('11', "Nopember"),
        ('12', "Desember"),
    ], string="Bulan")
    year = fields.Selection(selection=_get_year_in_move, string="Tahun", default = str(datetime.datetime.now().year))
    tax_id = fields.Many2one('account.tax', string='Jenis Pajak')
    count = fields.Integer('Jumlah', compute='_compute_all')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    amount_total = fields.Monetary('Nilai', compute='_compute_all')
    type = fields.Selection([('sale', 'Penjualan'), ('purchase','Pembelian')], string='Type')
    buktipotong_ids = fields.One2many('ka_account.pph.buktipotong', 'periode_id', string='Bukti Potong')
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate')], string='Status', default='draft')
    
    def _get_periode(self):
        year = int(self.year)
        month = int(self.month)
        date_from = datetime.date(year, month, 1)
        date_to = datetime.date(year, month, calendar.monthrange(year, month)[1])            
        return (date_from, date_to)

    @api.multi
    @api.depends('month', 'year')
    def _compute_all(self):
        for rec in self:
            rec.name = "%s-%s" % (rec.year, rec.month)
            rec.count = len(rec.buktipotong_ids)
            rec.amount_total = sum([b.amount for b in rec.buktipotong_ids])
                
    def action_validate(self):     
        user = self.env.user
        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
        now = pytz.utc.localize(datetime.datetime.now()).astimezone(tz)
        download_time = datetime.datetime.strftime(now, "%d-%m-%Y_%H:%M")

        filename = self.tax_id.name + download_time + ".csv"
    
        #Prepare for CSV Format ouput
        filename = self.tax_id.name + download_time + ".csv"
        my_utf8 = self._prepare_csv_output()
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(my_utf8),
            'datas_fname': filename + ".csv",
            'store_fname': filename,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'text/csv',
        })
        self._cr.commit()
        self.state='validate'

    def action_draft(self):
        #Unlink existing Data
        aml = self.env['account.move.line']
        if self.buktipotong_ids:
            self.buktipotong_ids.unlink()
        
        #Unlink Attachment
        attachments = self.env['ir.attachment'].search([('res_model', '=', self._name), ('res_id', '=', self.id)])
        if attachments:
            attachments.unlink()

        self.state='draft'
        
    def action_download_csv(self):
        # filename = self.filename + ".csv",
        attachment = self.env['ir.attachment'].search([('res_model', '=', self._name), ('res_id', '=', self.id)])
        if attachment:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s/%s' % (attachment.id, 'PPh22_'+self.name+'.csv'),
                'target': 'new',
                'nodestroy': False,
}    
    def generate_pph(self):
        aml = self.env['account.move.line']
        date_start, date_end = self._get_periode()
        tax_account_id = self.tax_id.account_id.id
        buktipotong = self.env['ka_account.pph.buktipotong']
        journal_ids = self.env['account.journal'].search([('type', 'in', ('cash', 'bank'))])
        acc_ids = self.env['account.account'].search([('user_type_id.type','=','payable')])._ids + (tax_account_id,)
        seq = self.sequence
        move_line = aml.search([('account_id', 'in', acc_ids), ('journal_id', 'in', journal_ids._ids),('date', '>=', date_start.strftime("%Y-%m-%d")), ('date', '<=', date_end.strftime("%Y-%m-%d"))])

        dpp = 0
        pph = 0
        move_id = 0
        reconcile_invoice_id = 0
        for r in move_line:
            vals = {}
            amount_dpp = 0.0
            payment_id = None
            partner_ref = None
            if move_id != r.move_id:
                dpp = 0
                pph = 0 
                reconcile_invoice_id = 0
            if r.account_id.user_type_id.type=='payable':
                dpp = r.debit
                reconcile_invoice_id = r.reconcile_invoice_id
            else:
                if r.account_id.id == tax_account_id:
                    pph = r.credit
            move_id = r.move_id

            if (dpp * pph) > 0:
                if reconcile_invoice_id:
                    acc_payment = self.env['ka_account.payment'].search([('invoice_id', '=', reconcile_invoice_id.id)])[0]
                    if acc_payment:
                        payment_id = acc_payment.id
                        partner_ref = acc_payment.no_kwitansi
                    
                vals = {
                    'name': '%03d/%s' % (seq, self.suffix),
                    'periode_id': self.id,
                    'move_id': r.move_id.id,
                    'payment_id': payment_id,
                    'partner_ref': partner_ref,
                    'partner_id': r.partner_id.id,
                    'amount_dpp': dpp,
                    'amount': pph,}
                    
                buktipotong.create(vals) 
                seq=seq+1
                dpp = 0
                pph = 0
        return

    @api.multi
    def action_open_buktipotong(self):
        action = self.env.ref('ka_account_tax.action_ka_account_pph_buktipotong_open')
        result = action.read()[0]
        result['domain'] = [('periode_id', '=', self.id)]
        result['context'] = {'default_periode_id': self.id}
        return result            
    
    @api.one
    def get_list_number(self, partner_id):
        numbers = ''
        for rec in self.buktipotong_ids.search([('partner_id','=', partner_id)]):
            numbers = numbers  + rec.name + ' '
        print numbers
        print "<<<<<<<<<<<<<<<<<<<<<<<"
        return numbers
            
        
    @api.multi
    def _prepare_csv_output(self):
        delimiter = ','
        output_head = ''     
        for rec in self.buktipotong_ids:
            tgl_bayar = rec.date_paid[-2:]+"/"+rec.date_paid[5:-3]+"/"+rec.date_paid[:4]
            output_head += '"F113304"' + delimiter + '"'+ rec.date_paid[5:-3] +'"' + delimiter + '"'+ rec.date_paid[:4] +'"' + delimiter + '"0"' + delimiter + '"' + str(rec.partner_id.no_npwp) + '"' + delimiter + '"' + rec.partner_id.name + '"' + delimiter
            output_head += '"' + rec.partner_id.street + '"' + delimiter + '"'+ str(rec.name) +'"' + delimiter + '"' + tgl_bayar +'"' + delimiter
            output_head += '"0"' + delimiter + '"0,25"' + delimiter + '"0"' + delimiter
            output_head += '"0"' + delimiter + '"0,1"' + delimiter + '"0"' + delimiter
            output_head += '"0"' + delimiter + '"0,3"' + delimiter + '"0"' + delimiter
            output_head += '"0"' + delimiter + '"0,45"' + delimiter + '"0"' + delimiter
            output_head += '"Farmasi"' + delimiter + '"0"' + delimiter + '"0,25"' + delimiter + '"0"' + delimiter
            output_head += '""' + delimiter
            output_head += '"0"' + delimiter + '"0"' + delimiter + '"0"' + delimiter
            output_head += '""' + delimiter
            output_head += '"0"' + delimiter + '"0"' + delimiter + '"0"' + delimiter
            output_head += '"PERKEBUNAN"' + delimiter + '"' + str(int(rec.amount_dpp)) + '"' + delimiter + '"0,25"' + delimiter + '"' + str(int(rec.amount)) + '"' + delimiter
            output_head += '""' + delimiter
            output_head += '"0"' + delimiter + '"0,25"' + delimiter + '"0"' + delimiter
            output_head += '""' + delimiter
            output_head += '"0"' + delimiter + '"0"' + delimiter + '"0"' + delimiter
            output_head += '""' + delimiter
            output_head += '"0"' + delimiter + '"0"' + delimiter + '"0"' + delimiter
            output_head += '"' + str(int(rec.amount_dpp)) + '"' + delimiter + '"' + str(int(rec.amount)) + '"' + '\n'      
                
        my_utf8 = output_head.encode("utf-8")
        return my_utf8

class KaAccountPPhBuktiPotong(models.Model):
    _name = "ka_account.pph.buktipotong"        
    _description = "Bukti Potong PPh"
    
    
    @api.multi
    @api.depends('amount_dpp')
    def _compute_pph(self):
        for rec in self:
            rec.rate = (rec.amount / rec.amount_dpp) * 100
            
    name = fields.Char('Nomor', size=32)
    periode_id = fields.Many2one('ka_account.pph.periode', string='Periode', ondelete='cascade', required=True)
    move_id = fields.Many2one('account.move', string='Sumber Jurnal')
    date_paid = fields.Date(string='Tgl. Bayar', related='move_id.date')
    no_npwp = fields.Char(string='NPWP', related='partner_id.no_npwp')
    payment_id = fields.Many2one('ka_account.payment', string='No. Pengajuan')
    partner_ref = fields.Char(string='Ref. Rekanan', size=32)
    partner_id = fields.Many2one('res.partner', string='Rekanan')
    amount_dpp = fields.Monetary('DPP')
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id)
    amount = fields.Monetary('Nilai')
    rate = fields.Float('Rate %', digits=(4, 2), compute='_compute_pph')
    company_id = fields.Many2one('res.company', string='Perusahaan', required=True, 
        states={'draft': [('readonly', False)]}, 
        default=lambda self: self.env['res.company']._company_default_get('ka_account.pph.buktipotong'))
    state=fields.Selection([('draft', 'Draft'), ('validate', 'Validate')], string='Status', related='periode_id.state')