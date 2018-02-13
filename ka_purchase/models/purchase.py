# -*- coding: utf-8 -*-

import time
import datetime
from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }	
    
    operating_unit_id = fields.Many2one('res.partner', string="Unit/PG", states=READONLY_STATES, domain=[('is_operating_unit', '=', True)])
    source_partner_id = fields.Many2one('res.partner', string="Vendor", readonly=True) 
    source_order_id = fields.Many2one('purchase.order', string="Source PO", help="Source PO Jika PO diterbitkan dari Unit lain", readonly=True, copy=False) 
    copy_order_id = fields.Many2one('purchase.order', string="Copy PO Unit", help="Copy PO Jika PO diterbitkan untuk Unit lain", readonly=True, copy=False) 
    order_type = fields.Selection([
        ('rkout', 'SP Untuk Unit'), 
        ('rkin', 'SP Dari Unit'), 
        ('lokal', 'SP Local')
        ], string='Jenis PO', default='lokal', readonly=True, copy=False)
    purchase_category_id = fields.Many2one('ka_account.payable.category', 'Purchase Category')
    is_direct_purchase = fields.Boolean(related='purchase_category_id.is_direct_purchase', string='Pembelian Langsung')
    spm_id = fields.Many2one('logistik.spm', string='Nomor SPM')
    golongan = fields.Selection([
        ('agen', 'Agen'),
        ('import', 'Import'),
        ('tender', 'Tender'),
        ('repeat', 'Repeate'),
        ('kontrak', 'Kontrak')
    ], string='Golongan', default='agen')
    ttd_dir = fields.Many2one('hr.employee', string='Tanda Tangan-1', default=lambda self: self.env.user.company_id.dept_dirut.manager_id)
    #error ttd_keu gak mau muncul jdi tak buat baru
    # ttd_keu = fields.Many2one('hr.employee', string='Tanda Tangan-2', default=lambda self: self.env.user.company_id.dept_log.manager_id)
    keu_ttd = fields.Many2one('hr.employee', string='Tanda Tangan-2', default=lambda self: self.env.user.company_id.dept_dirkeu.manager_id)
    ttd_div = fields.Many2one('hr.employee', string='Kadiv. Terkait')
    ttd_log = fields.Many2one('hr.employee', string='Kabag. Logistik', default=lambda self: self.env.user.company_id.dept_log.manager_id)
    ref_investasi = fields.Char(compute='_compute_investasi', string='No. Proyek')
    is_extended = fields.Boolean(string='Diperpanjang')
    alasan = fields.Char(string='Alasan', size=150, readonly=True, track_visibility='onchange')
    date_planned = fields.Datetime(string='Scheduled Date', compute=False, index=True, oldname='minimum_planned_date')    
    
    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrder,self).default_get(fields)
        res['notes'] = 'Harga belum termasuk PPN dan belum dipotong PPH'
        return res
    
    @api.multi
    def _compute_investasi(self):
        for s in self:
            ref_investasi = ''
            for line in s.order_line:
                ref_investasi += (line.account_analytic_id.code or '') + ', '
                ref_investasi = ref_investasi.strip(', ')
            s.ref_investasi = ref_investasi
    
    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for po in self:
            name = po.name
            result.append((po.id, name))
        return result
              
    @api.one
    def copy_order_to_ou(self):
        source_uid  =  self.env.user.company_id.intercompany_user_id.id
        ou_company = self.sudo(source_uid).operating_unit_id.get_company_ref()[0]
        
        default = {
            'name': self.name,
            'date_order': self.date_order,
            'company_id': ou_company.id,
            'source_partner_id':self.partner_id.id,
            'source_order_id':self.id,            
            'partner_id': self.company_id.partner_id.id,
            'partner_ref': self.partner_ref,
            'order_type': 'rkin',
            'picking_type_id': self.sudo(source_uid).with_context(company_id=ou_company.id)._default_picking_type().id,
            'order_line': None,
            }
        copy_order = self.sudo(source_uid).copy(default=default)
        #copy order line
        for line in self.order_line:
            default_line = {
                'order_id': copy_order.id,
                'source_order_line_id': line.id,
                'company_id': ou_company.id,
            }
            copy_line = line.sudo(source_uid).copy(default=default_line)
        copy_order.sudo(source_uid).button_confirm()
        return

    @api.multi
    def button_approve(self, force=False):
        if self.company_id.po_double_validation == 'two_step'\
          and self.amount_total >= self.env.user.company_id.currency_id.compute(self.company_id.po_double_validation_amount, self.currency_id)\
          and not self.user_has_groups('purchase.group_purchase_manager'):
            raise UserError(_('You need purchase manager access rights to validate an order above %.2f %s.') % (self.company_id.po_double_validation_amount, self.company_id.currency_id.name))
        self.write({'state': 'purchase'})
        
        #jika PO diterbitkan untuk Operating unit yang sama(SP Lokal)
        #maka buat picking, 
        #-----------------------
        #self._create_picking()
        #replace with :
        if self.operating_unit_id.id == self.company_id.partner_id.id:
            self._create_picking()
        #-----------------------
        if self.company_id.po_lock == 'lock':
            self.write({'state': 'done'})
        return {}


    @api.multi
    def button_confirm(self):
        for order in self:
            #jika Pembelian untuk operating unit yang lain
            #maka akan membuat copy PO atas operating unit bersangkutan
            super(PurchaseOrder, order).button_confirm()
            for l in order.order_line:
                if not l.product_id:
                    raise UserError("Kode barang harus diisi sebelum konfirmasi PO")
                if l.spm_line_id:
                    admin_uid = self.env.ref('base.user_root').id
                    l.sudo(admin_uid).spm_line_id.state='sp'
            if order.operating_unit_id.id <> order.company_id.partner_id.id:
                self.order_type = 'rkout'
                order.copy_order_to_ou()
    
    @api.one
    def button_draft(self):
        super(PurchaseOrder,self).button_draft()
        # back name to original name
        splitname = self.name.split('-B')
        self.write({'name': splitname[0]})
            
    # override purchase_order button_cancel()
    @api.one
    def action_cancel(self, back_tender, back_agen, alasan=''):
        # cari sequence untuk no batal
        listpo = self.search([('name', 'like', self.name + '-B%')], order="name desc")
        suffix = '-B'
        if len(listpo) <= 0:
            suffix += '01'
        else:
            splitname = listpo[0].name.split('-B')
            if len(splitname) <= 1 or splitname[1] == '':
                suffix += '01'
            else:
                last = int(splitname[1]) + 1
                if last < 10:
                    suffix += '0' + str(last)
                else:
                    suffix += str(last)
        # end of cari sequence untuk no batal

        if back_tender:
            tender_id = self.spp_id.tender_id.id
            tender = self.env['logistik.tender'].browse(tender_id)
            tender.write({'state': 'spp'})
            # spp = self.env['logistik.spp'].search([('tender_id', '=', tender_id)], limit=1)
            spp = self.env['logistik.spp'].search([('tender_id', '=', tender_id)])
            spp.write({'state': 'draft'})

        if back_agen:
            spp_id = self.spp_id.id
            spp = self.env['logistik.spp'].browse(spp_id)
            spp.write({'state': 'draft'})
            for line in self.order_line:
                line.spm_line_id.action_approve()
        
        notes = self.notes + '\n' if self.notes else ''
        notes += "ALASAN BATAL : " + alasan
        self.write({'name': (self.name + suffix), 'notes': notes})
        return super(PurchaseOrder, self).button_cancel()
    
    # @api.onchange('date_planned')
    # def onchange_date_planned(self):
        # for order in self:
            # for l in order.order_line:
                # l.date_planned = order.date_planned
        
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    source_order_line_id = fields.Many2one('purchase.order.line', string="Source Order Line") 
    qty_received_unit = fields.Float('Diterima', compute='compute_qty_received_unit')
    tanggal_sp = fields.Datetime(related='order_id.date_order', string='Order Date', store=True)
    lst_price = fields.Float(related='product_id.lst_price', string='HPS', track_visibility='onchange', readonly=True)
    spesifikasi = fields.Text(related='product_id.description', string='Spesifikasi', readonly=True)
    keterangan = fields.Text(string='Keterangan')
    order_type = fields.Selection(related='order_id.order_type', 
        selection=[
            ('rkout', 'SP Untuk Unit'), 
            ('rkin', 'SP Dari Unit'), 
            ('lokal', 'SP Local')], string='Jenis PO', readonly=True)
    pengadaan = fields.Selection([
        ('RD', 'Direksi'),
        ('RP', 'Pabrik')], string='Pengadaan', default='RD')
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True, required=False)
    
    
    @api.multi
    @api.depends('qty_received','source_order_line_id')
    def compute_qty_received_unit(self):
        for this in self:
            res = 0.0
            intercompany_user = this.order_id.company_id.intercompany_user_id.id
            if this.order_id.operating_unit_id.id != this.order_id.company_id.partner_id.id:
                order_line_src = self.env['purchase.order.line'].sudo(intercompany_user).search([('source_order_line_id','=',this.id)])
                res = sum(order_line.qty_received for order_line in order_line_src)
            else:
                res = this.qty_received
            this.qty_received_unit = res

    #ketika di unit terbit NTB(qty_invoiced) maka di PO induk dibaca sebagai penerimaan(qty_received)
    @api.depends('invoice_lines.invoice_id.state')
    def _compute_qty_invoiced(self):
        for line in self:
            super(PurchaseOrderLine, line)._compute_qty_invoiced()
            sol_id = line.source_order_line_id
            if sol_id:
                self._cr.execute("UPDATE purchase_order_line SET qty_received = %s WHERE id=%s", (line.qty_invoiced, sol_id.id,))
    
    # @api.onchange('date_planned')
    # def onchange_date_planned(self):
        # if self.date_planned:
            # purchase_date_planned = self._context.get('purchase_date_planned')
            # if purchase_date_planned != self.date_planned:
                # self.date_planned = purchase_date_planned

    #overide origin
    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        # Reset date, price and quantity since _onchange_quantity will provide default values
        # self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        # replace with :
        self.date_planned = self.order_id.date_planned
        
        self.price_unit = 0.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        product_lang = self.product_id.with_context({
            'lang': self.partner_id.lang,
            'partner_id': self.partner_id.id,
        })
        if product_lang.type != 'service':
            self.name = product_lang.display_name
            if product_lang.description_purchase:
                self.name += '\n' + product_lang.description_purchase

        fpos = self.order_id.fiscal_position_id
        if self.env.uid == SUPERUSER_ID:
            company_id = self.env.user.company_id.id
            self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id))
        else:
            self.taxes_id = fpos.map_tax(self.product_id.supplier_taxes_id)
        
        if self.product_qty <= 0:
            self._suggest_quantity()
            self._onchange_quantity()

        return result
        
    def get_last_sp(self, prod_id, date_order, order_id):
        order_line = self.env['purchase.order.line']
        sp_date = datetime.datetime.strptime(date_order, "%Y-%m-%d %H:%M:%S") - datetime.timedelta(days=1)
        res = order_line.search([('product_id', '=', prod_id), ('tanggal_sp', '<', date_order), ('order_id', '!=', order_id)], limit = 3, order = 'tanggal_sp desc')
        # res = order_line.search([('product_id', '=', prod_id), ('order_id', '!=', order_id)], limit = 3, order = 'tanggal_sp desc')
        return res
                
    @api.multi
    def _create_picking(self):
        if self.purchase_category_id.is_direct_purchase:
            return True
        else:
            super(PurchaseOrder, order)._create_picking()