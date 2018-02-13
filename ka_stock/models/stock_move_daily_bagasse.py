from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError

class StockMoveDailyBagasse(models.Model):
    _name = "stock.move.daily.bagasse"
    _description = "Stock Move Daily Bagasse for PT Kebon Agung"
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(string="Name", default="New", copy=False)
    state = fields.Selection([("draft", "Draft"),
                              ("proposed", "Proposed"),
                              ("done", "Done")],
                                string = "Status", default="draft", track_visibility="always", copy=False)
    date = fields.Date(string="Tanggal", default=fields.Datetime.now)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    move_ids = fields.One2many("stock.move", "move_daily_bagasse_id", string="Stock Moves", copy=False)
    product_id = fields.Many2one("product.product", string="Product", default=lambda self: self.env.user.company_id.product_bagasse_id)
    product_uom = fields.Many2one("product.uom", string="Unit of Measure")
    product_qty = fields.Float("Kuantum", copy=False)
    manufacture_daily_id_bagasse = fields.Many2one("ka_manufacture.daily", string="Hari Giling")

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom = self.product_id.uom_id.id

    @api.multi
    def propose_daily_bagasse_transaction(self):
        for this in self:
            if self.product_qty != 0:
                this.write({'state' : 'proposed'})
            else:
                raise UserError('Sorry, the value of "Kuantum Kawur" cannot be 0.')
        return True
    
    @api.multi
    def set_draft_daily_bagasse_transaction(self):
        for this in self:
            this.write({'state': 'draft'})
        return True

    @api.multi
    def validate_daily_bagasse_transaction(self):
        for this in self:
            line_item_stock = []
            vals = {'state': 'done'}
            if this.name == 'New':
                sequence_src = self.env['ir.sequence'].search([('name','=','Stock Move Daily Bagasse'),('company_id','=',self.env.user.company_id.id)], limit=1)
                if not sequence_src:
                    raise UserError('Penomoran untuk produksi harian ampas belum ada. Silahkan hubungi Administrator.')
                vals['name'] = sequence_src.next_by_id()
            this.write(vals)
            
            data_entry = {}
            date_now = datetime.now().date()
            picking_type_id = self.env.user.company_id.picking_type_produce_id.id
            location_production_id = this.product_id.property_stock_production.id
            stock_picking = self.env['stock.picking']
            
            vals_stock = {
                'product_id' : this.product_id.id,
                'product_uom_qty' : this.product_uom.factor_inv * this.product_qty,
                'product_uom' : this.product_id.uom_id.id,
                'name' : this.product_id.display_name,
                'picking_type_id' : picking_type_id, 
                'location_id' : location_production_id,
                'location_dest_id' : self.env.user.company_id.location_factory_id.id,
                'date_expected' : date_now,
                'move_daily_bagasse_id' : this.id
            }
            line_item_stock.append((0, 0, vals_stock))

            data_entry = {
                'location_id' : location_production_id,
                'location_dest_id' : self.env.user.company_id.location_factory_id.id,
                'min_date': date_now,
                'date_transfer': date_now,
                'origin': this.name,
                'move_lines': line_item_stock,
                'picking_type_id': picking_type_id,
            }
            stock_picking_create = stock_picking.create(data_entry)
            stock_picking_create.action_confirm()
            stock_picking_create.do_transfer()

        return True
    
    @api.multi
    def unlink(self):
        for this in self:
            if this.state != 'draft':
                raise UserError('Sorry, you cannot delete non-draft transaction.')
        return super(StockMoveDailyBagasse, self).unlink()

    @api.multi
    def action_view_stock_picking(self):
        for this in self:
            move_lines = self.env['stock.move'].search([('move_daily_bagasse_id','=',this.id)])
            for m in move_lines:
                domain = [('id', 'in', [x.id for x in self.env['stock.picking'].browse(m.picking_id.id)])]

                return {
                    'name': 'Stock Picking',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'domain' : domain,
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking',
                    'target': 'current',  
                }

    def production_to_yesterday(self):
        total = 0
        bagasse_obj = self.env['stock.move.daily.bagasse'].search([('date', '<', self.date),('product_id','=',self.product_id.id)])
        for b in bagasse_obj:
            production_year = fields.Date.from_string(b.date)
            fiscalyear = b.manufacture_daily_id_bagasse.session_id.fiscalyear_id.name
            if str(production_year.year) == fiscalyear :
                total += b.product_qty
        return total

    def expense_to_yesterday(self):
        total = 0
        moves = self.env['stock.move'].search([('date','<', self.date),
                        ('product_id','=',self.product_id.id),
                        ('picking_id.picking_type_id.code','=','outgoing')])
        for m in moves:
            total += m.product_uom_qty
        return total

    def expense_today(self):
        total = 0
        moves = self.env['stock.move'].search([('date','=', self.date),
                        ('product_id','=',self.product_id.id),
                        ('picking_id.picking_type_id.code','=','outgoing')])
        for m in moves:
            total += m.product_uom_qty
        return total

    def get_expense_details(self):
        end_date = fields.Date.from_string(self.date)
        start_date = fields.Date.from_string(str(end_date.year)+'-01-01')
        
        m_all = self.env['stock.move'].search([('date','<=', self.date),
                ('date', '>=', str(start_date)),
                ('product_id','=',self.product_id.id),
                ('picking_id.picking_type_id.code','=','outgoing'),
                ('state', '=', 'done')])

        customers = list()
        for move in m_all:
            customers.append(move.picking_id.partner_id)

        total = 0
        items = list()

        for c in set(customers):
            vals = { 'customer': c.name, 'qty_tod': 0 }
            for move in m_all:
                move_date = fields.Date.from_string(move.date)
                if move_date == end_date:
                    print('Quantity Today >>', move.product_uom_qty)
                    vals['qty_tod'] = move.product_uom_qty
                else:
                    total += move.product_uom_qty
            vals['qty_yes'] = total
            items.append(vals)
        return items

    def get_do_remaining(self):
        end_date = fields.Date.from_string(self.date)
        start_date = fields.Date.from_string(str(end_date.year)+'-01-01')
        
        m_all = self.env['stock.move'].search([('date','<=', self.date),
                ('date', '>=', str(start_date)),
                ('product_id','=',self.product_id.id),
                ('picking_id.picking_type_id.code','=','outgoing'),
                ('state', '!=', 'done')])

        customers = list()
        for move in m_all:
            customers.append(move.picking_id.partner_id)

        total = 0
        items = list()

        for c in set(customers):
            vals = { 'customer': c.name, 'qty': 0 }
            for move in m_all:
                total += move.product_uom_qty
            vals['qty'] = total
            items.append(vals)
        return items

    @api.multi
    def print_laporan_harian_ampas(self):
        for this in self:
            report_obj = self.env['report']
            template = "ka_stock.template_laporan_harian_ampas"
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
                }
        return report_obj.get_action(self, template, data=datas)
