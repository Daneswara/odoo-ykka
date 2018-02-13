from odoo import models, fields, api
from datetime import datetime
from docutils.nodes import field
import time
from odoo.exceptions import UserError

class StockMoveDailyMolasses(models.Model):
    _name = "stock.move.daily.molasses"
    _description = "Stock Move Daily Molasses for PT Kebon Agung"
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'
    _template_laporan_harian_tetes = 'ka_stock.template_laporan_harian_tetes'
    
    def _get_line_from_tank(self):
        line_items_kuantum = []
        tank_obj = self.env['stock.tank'].search([])
        for tank in tank_obj:
            vals_kuantum = {
                        'name' : tank.id,
                        'tank_qty' : 0.0,
                        'brix_qty' : 0.0}
            line_items_kuantum.append(vals_kuantum)
        return line_items_kuantum
    
    @api.multi
    @api.depends('line_ids.tank_qty', 'line_circulation_ids.tank_qty')
    def compute_total_qty(self):
        for this in self:
            molasses_qty = 0
            circulation_qty = 0
            for line in this.line_ids:
                molasses_qty += line.tank_qty
                this.total_qty = molasses_qty
            for line in this.line_circulation_ids:
                circulation_qty += line.tank_qty
                this.total_circulation_qty = circulation_qty


    name = fields.Char(string="Name", default="New", copy=False)
    date = fields.Date(string="Tanggal", default=fields.Datetime.now)
    state = fields.Selection([("draft", "Draft"),
                              ("proposed", "Proposed"),
                              ("done", "Done")],
                                string = "Status", default="draft", track_visibility="always", copy=False)
    product_id = fields.Many2one("product.product", string="Product", default=lambda self: self.env.user.company_id.product_molasses_id)
    product_uom = fields.Many2one("product.uom", string="Unit of Measure")
    move_ids = fields.One2many("stock.move", "move_daily_molasses_id", string="Stock Moves", copy=False)
    bagi_hasil = fields.Boolean("Bagi Hasil", copy=False)
    total_qty = fields.Float("Total", compute="compute_total_qty", copy=False)
    farmer_qty = fields.Float("Kuantum Petani", copy=False)
    factory_qty = fields.Float("Kuantum Pabrik", copy=False)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.user.company_id)
    total_circulation_qty = fields.Float("Total", compute="compute_total_qty", copy=False) 
    line_ids = fields.One2many("stock.move.daily.molasses.line", "move_daily_molasses_id", string="Daily Move Line", default=_get_line_from_tank, copy=False)
    line_circulation_ids = fields.One2many("stock.move.daily.molasses.circulation", "move_daily_molasses_id", string="Move Daily Molasses", default=_get_line_from_tank, copy=False)
    manufacture_daily_id_molasses = fields.Many2one("ka_manufacture.daily", string="Hari Giling")
    
    
    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        line_items_kuantum = []
        tank_obj = self.env['stock.tank'].search([])
        for tank in tank_obj:
            vals_kuantum = {
                        'name' : tank.id,
                        'tank_qty' : 0.0,
                        'brix_qty' : 0.0}
            line_items_kuantum.append((0,0,vals_kuantum))
        default.update(line_ids = line_items_kuantum, line_circulation_ids = line_items_kuantum)
        return super(StockMoveDailyMolasses, self).copy(default)
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom = self.product_id.uom_id.id
        
    @api.multi
    def unlink(self):
        for this in self:
            if this.state != 'draft':
                raise UserError('Sorry, you cannot delete non-draft transaction.')
        return super(StockMoveDailyMolasses, self).unlink()
    
    @api.multi
    def action_view_picking_molasses(self):
        for this in self:
            domain = [('id', 'in', [x.picking_id.id for x in self.env['stock.move'].search([('move_daily_molasses_id','=', this.id)])])]

            return {
                'name': 'Stock Picking',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain' : domain,
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'target': 'current',  
            }
    
    
    @api.multi
    def propose_daily_molasses_transaction(self):
        for this in self:
            this.write({'state' : 'proposed'})
        return True
    
    @api.multi
    def set_draft_daily_molasses_transaction(self):
        for this in self:
            this.write({'state': 'draft'})
        return True
    
    @api.multi
    def validate_daily_molasses_transaction(self):
        for this in self:
            line_items_stock = []
            line_items_pg = []
            line_items_tani = []
            vals = {'state': 'done'}
            if this.name == 'New':
                sequence_src = self.env['ir.sequence'].search([('name','=','Stock Move Daily Molasses'),('company_id','=',self.env.user.company_id.id)], limit=1)
                if not sequence_src:
                    raise UserError('Penomoran untuk produksi harian tetes belum ada. Silahkan hubungi Administrator.')
                vals['name'] = sequence_src.next_by_id()
            this.write(vals)
            data_entry = {}
            data_entry_pg = {}
            data_entry_tani = {}
            date_now = datetime.now().date()
            picking_type_id = self.env.user.company_id.picking_type_produce_id.id
            picking_type_factory_id = self.env.user.company_id.picking_type_factory_id.id
            picking_type_farmer_id = self.env.user.company_id.picking_type_farmer_id.id
            location_production_id = this.product_id.property_stock_production.id
            stock_picking_obj = self.env['stock.picking']
                 
            vals_stock = {
                'product_id' : this.product_id.id,
                'product_uom_qty' : this.total_qty,
                'product_uom' : this.product_id.uom_id.id,
                'name' : this.product_id.display_name,
                'picking_type_id' : picking_type_id, 
                'location_id' : location_production_id,
                'location_dest_id' : self.env.user.company_id.location_production_dest_id.id,
                'date_expected' : date_now,
                'move_daily_molasses_id' : this.id
            }
             
            line_items_stock.append((0, 0, vals_stock))
 
            data_entry = {
                'location_id' : location_production_id,
                'location_dest_id' : self.env.user.company_id.location_production_dest_id.id,
                'min_date': date_now,
                'date_transfer': date_now,
                'origin': this.name,
                'move_lines': line_items_stock,
                'picking_type_id': picking_type_id,
            }
 
            stock_picking_create = stock_picking_obj.create(data_entry)
            stock_picking_create.action_confirm()
            stock_picking_create.do_transfer()
             
            if this.bagi_hasil == True:
                 
                vals_stock_pg = {
                    'product_id' : this.product_id.id,
                    'product_uom_qty' : this.factory_qty,
                    'product_uom' : this.product_id.uom_id.id,
                    'name' : this.product_id.display_name,
                    'picking_type_id' : picking_type_factory_id, 
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_factory_id.id,
                    'date_expected' : date_now,
                    'move_daily_molasses_id' : this.id
                }
                line_items_pg.append((0, 0, vals_stock_pg))
     
                data_entry_pg = {
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_factory_id.id,
                    'min_date': date_now,
                    'date_transfer': date_now,
                    'origin': this.name,
                    'move_lines': line_items_pg,
                    'picking_type_id': picking_type_factory_id,
                }
     
                stock_picking_pg_create = stock_picking_obj.create(data_entry_pg)
                stock_picking_pg_create.action_confirm()
                stock_picking_pg_create.do_transfer()
                 
                vals_stock_tani = {
                    'product_id' : this.product_id.id,
                    'product_uom_qty' : this.farmer_qty,
                    'product_uom' : this.product_id.uom_id.id,
                    'name' : this.product_id.display_name,
                    'picking_type_id' : picking_type_farmer_id, 
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_farmer_id.id,
                    'date_expected' : date_now,
                    'move_daily_molasses_id' : this.id
                }
                line_items_tani.append((0, 0, vals_stock_tani))
     
                data_entry_tani = {
                    'location_id' : self.env.user.company_id.location_production_dest_id.id,
                    'location_dest_id' : self.env.user.company_id.location_farmer_id.id,
                    'min_date': date_now,
                    'date_transfer': date_now,
                    'origin': this.name,
                    'move_lines': line_items_tani,
                    'picking_type_id': picking_type_farmer_id,
                }
                stock_picking_tani_create = stock_picking_obj.create(data_entry_tani)
                stock_picking_tani_create.action_confirm()
                stock_picking_tani_create.do_transfer()
                 
        return True

    @api.multi
    def print_hasil_timbang(self):
        for this in self:
            report_obj = self.env['report']
            template = "ka_stock.template_hasil_timbang_tetes"
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
                }
        return report_obj.get_action(self, template, data=datas)
    
    def get_len_line(self):
        len_line = []
        for line in self.line_ids:
            if line.id not in len_line:
                len_line.append(line)
        return len(len_line)
    
    def total_td(self):
        len_line = self.get_len_line()
        total_td = 3 + len_line
        return total_td
    
        
            
    def get_qty_yesterday(self):
        qty_yesterday = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        limit_year = start_date.year
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        limit_date = datetime(limit_year,1,1,0,0,0)
        limit_date = datetime.strftime(limit_date,"%Y-%m-%d %H:%M:%S")
        stock_move_molasses_obj = self.env['stock.move.daily.molasses'].search([('product_id', '=', self.product_id.id),
                                                        ('date', '>=', limit_date),
                                                        ('date', '<', start_date),
                                                        ])
        for stock in stock_move_molasses_obj:
            qty_yesterday += stock.total_qty
        return qty_yesterday
       
    def get_qty_today(self):
        qty_today = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_molasses_obj = self.env['stock.move.daily.molasses'].search([('product_id', '=', self.product_id.id),
                                                        ('date', '>=', start_date),
                                                        ('date', '<=', end_date),
                                                        ])
        for stock in stock_move_molasses_obj:
            qty_today += stock.total_qty
        return qty_today
    
    def get_qty_production_tank_yesterday(self, tank_id):
        qty_yesterday_tank = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        limit_year = start_date.year
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        limit_date = datetime(limit_year,1,1,0,0,0)
        limit_date = datetime.strftime(limit_date,"%Y-%m-%d %H:%M:%S")
        stock_move_molasses_line_obj = self.env['stock.move.daily.molasses.line'].search([('move_daily_molasses_id.product_id', '=', self.product_id.id),
                                                        ('move_daily_molasses_id.date', '>=', limit_date),
                                                        ('move_daily_molasses_id.date', '<', start_date),
                                                        ('name','=',tank_id.id)
                                                        ])
        
        for line in stock_move_molasses_line_obj:
            qty_yesterday_tank += line.tank_qty
        
        return qty_yesterday_tank
    
    def get_qty_production_tank_today(self, tank_id):
        qty_today_tank = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_molasses_line_obj = self.env['stock.move.daily.molasses.line'].search([('move_daily_molasses_id.product_id', '=', self.product_id.id),
                                                        ('move_daily_molasses_id.date', '>=', start_date),
                                                        ('move_daily_molasses_id.date', '<=', end_date),
                                                        ('name', '=', tank_id.id)
                                                        ])
        for line in stock_move_molasses_line_obj:
            qty_today_tank += line.tank_qty
        
        return qty_today_tank
    
    def get_qty_production_tank_until_today(self, tank_id):
        qty_yesterday_tank = self.get_qty_production_tank_yesterday(tank_id)
        qty_today_tank = self.get_qty_production_tank_today(tank_id)
        qty_until_today_tank = qty_yesterday_tank + qty_today_tank
        return qty_until_today_tank
    
    def get_qty_production_yesterday(self):
        sum_qty_production_yesterday = 0
        for this in self:
            for tank in self.env['stock.tank'].search([]):
                sum_qty_production_yesterday += this.get_qty_production_tank_yesterday(tank)
        return sum_qty_production_yesterday
    
    def get_qty_production_today(self):
        sum_qty_production_today = 0
        for this in self:
            for tank in self.env['stock.tank'].search([]):
                sum_qty_production_today += this.get_qty_production_tank_today(tank)
        return sum_qty_production_today
    
    def get_qty_production_until_today(self):
        sum_qty_production_until_today = 0
        for this in self:
            for tank in self.env['stock.tank'].search([]):
                sum_qty_production_until_today += this.get_qty_production_tank_until_today(tank)
        return sum_qty_production_until_today
    
    
    def get_qty_sale_tank_yesterday(self, tank_id):
        qty_yesterday_tank = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        limit_year = start_date.year
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        limit_date = datetime(limit_year,1,1,0,0,0)
        limit_date = datetime.strftime(limit_date,"%Y-%m-%d %H:%M:%S")
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'), 
                                                        ('date', '>=', limit_date), 
                                                        ('date', '<', start_date),
                                                        ('picking_id.picking_type_code','=', 'outgoing'),
                                                        ('picking_id.timbangan_id.tank_id', '=', tank_id.id)
                                                        ])
        
        for stock in stock_move_obj:
            qty_yesterday_tank += stock.product_uom_qty
        return qty_yesterday_tank
    
    def get_qty_sale_tank_today(self, tank_id):
        qty_today_tank = 0
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', start_date),
                                                        ('date', '<=', end_date),
                                                        ('picking_id.picking_type_code','=', 'outgoing'),
                                                        ('picking_id.timbangan_id.tank_id', '=', tank_id.id)
                                                        ])
        for stock in stock_move_obj:
            qty_today_tank += stock.product_uom_qty
        return qty_today_tank
    
    def get_qty_sale_tank_until_today(self, tank_id):
        qty_yesterday_tank = self.get_qty_sale_tank_yesterday(tank_id)
        qty_today_tank = self.get_qty_sale_tank_today(tank_id)
        qty_until_today_tank = qty_yesterday_tank + qty_today_tank
        return qty_until_today_tank
    
    def get_qty_sale_yesterday(self):
        sum_qty_sale_yesterday = 0
        for this in self:
            for tank in self.env['stock.tank'].search([]):
                sum_qty_sale_yesterday += this.get_qty_sale_tank_yesterday(tank)
        return sum_qty_sale_yesterday
    
    def get_qty_sale_today(self):
        sum_qty_sale_today = 0
        for this in self:
            for tank in self.env['stock.tank'].search([]):
                sum_qty_sale_today += this.get_qty_sale_tank_today(tank)
        return sum_qty_sale_today
    
    def get_qty_sale_until_today(self):
        sum_qty_sale_until_today = 0
        for this in self:
            for tank in self.env['stock.tank'].search([]):
                sum_qty_sale_until_today += this.get_qty_sale_tank_until_today(tank)
        return sum_qty_sale_until_today
    
    def get_equity_qty(self):
        sum_qty_production_until_today = self.get_qty_production_until_today()
        sum_qty_sale_until_today = self.get_qty_sale_until_today()
        equity_qty = sum_qty_production_until_today - sum_qty_sale_until_today
        return equity_qty
    
    def get_equity_qty_tank(self, tank_id):
        sum_qty_production_until_today_tank = self.get_qty_production_tank_until_today(tank_id)
        sum_qty_sale_until_today_tank = self.get_qty_sale_tank_until_today(tank_id)
        equity_qty_tank = sum_qty_production_until_today_tank - sum_qty_sale_until_today_tank
        return equity_qty_tank
        
        
    def get_qty_in_ku(self, qty):
        qty_kg = qty * self.product_uom.factor_inv
        qty_ku = qty_kg / self.product_id.production_uom_id.factor_inv
        return qty_ku
    
    def get_brix(self):
        brix = 0
        for line in self.line_ids:
            if line.tank_qty > 0:
                brix = line.brix_qty
                break
        return brix
    
    def get_nama_tangki(self):
        name = False
        for line in self.line_ids:
            if line.tank_qty > 0:
                name = line.name.name
                break
        return name
    
    def get_brix_tangki(self):
        brix_tangki = 0
        for line in self.line_ids:
            if line.tank_qty > 0:
                brix_tangki = line.name.current_brix
                break
        return brix_tangki
    
    def get_sale_order(self):
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', start_date),
                                                        ('date', '<=', end_date),
                                                        ('picking_id.picking_type_code','=', 'outgoing')
                                                        ])
        res = []
        for move in stock_move_obj:
            if move.procurement_id.sale_line_id.order_id not in res:
                res.append(move.procurement_id.sale_line_id.order_id)
        return res
    
    def set_total_average_brix(self, total_avg_brix):
        so_num = len(self.get_sale_order())
        if so_num != 0:
            return total_avg_brix / so_num
        else:
            return 0
    
    def get_rincian_pengeluaran(self, sale_id):
        start_date = datetime.strptime(self.date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        start_date = datetime.strftime(start_date, '%Y-%m-%d %H:%M:%S')
        end_date = datetime.strptime(self.date, '%Y-%m-%d')
        end_date = end_date.replace(hour=23, minute=59, second=59)
        end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M:%S')
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', '=', 'done'),
                                                        ('date', '>=', start_date),
                                                        ('date', '<=', end_date),
                                                        ('picking_id.picking_type_code','=', 'outgoing'),
                                                        ('procurement_id.sale_line_id.order_id','=',sale_id)])
        return stock_move_obj
    
    def get_partner(self):
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', 'not in', ['done', 'draft', 'cancel']),
                                                        ('picking_id.picking_type_code','=', 'outgoing')
                                                        ])
        res = []
        for move in stock_move_obj:
            if move.partner_id not in res:
                res.append(move.partner_id)
        return res
    
    def get_qty_partner(self, partner_id):
        qty_partner = 0
        stock_move_obj = self.env['stock.move'].search([('product_id', '=', self.product_id.id),
                                                        ('state', 'not in', ['done', 'draft', 'cancel']),
                                                        ('picking_id.picking_type_code','=', 'outgoing'),
                                                        ('partner_id', '=', partner_id)
                                                        ])
        for move in stock_move_obj:
            qty_partner += move.product_uom_qty
        return qty_partner
    
    @api.multi
    def print_laporan_harian_tetes(self):
        for this in self:
            report_obj = self.env['report']
            template = self._template_laporan_harian_tetes
            report = report_obj._get_report_from_name(template)
            data = {}
            datas = {
                'ids': this.id,
                'model': report.model,
                'form': data,
                }
        return report_obj.get_action(self, template, data=datas)
                
    
class StockMoveDailyMolassesLine(models.Model):
    _name = "stock.move.daily.molasses.line"
    _description = "Stock Move Daily Molasses Line for PT Kebon Agung"  
    
    name = fields.Many2one("stock.tank", string="Tangki")
    tank_qty = fields.Float("Kuantum")
    move_daily_molasses_id = fields.Many2one("stock.move.daily.molasses")
    brix_qty = fields.Float("Brix (%)")
    
    
class StockMoveDailyMolassesCirculation(models.Model):
    _name = "stock.move.daily.molasses.circulation"
    _description = "Stock Move Daily Molasses Circulation for PT Kebon Agung"  
    
    name = fields.Many2one("stock.tank", string="Tangki")
    tank_qty = fields.Float("Kuantum")
    move_daily_molasses_id = fields.Many2one("stock.move.daily.molasses")
    brix_qty = fields.Float("Brix (%)")

  