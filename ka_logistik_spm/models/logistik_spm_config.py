from openerp import models, fields, api, _

class logistik_spm_config(models.TransientModel):
    _name = "logistik.spm.config"
    _inherit = "res.config.settings"
    
    @api.one
    @api.depends('company_id')
    def compute_logistik_spm_config(self):
        self.verifikasi_kode_barang_partners_ids = self.company_id.verifikasi_kode_barang_partners_ids
        self.notif_kode_barang_baru_partners_ids = self.company_id.notif_kode_barang_baru_partners_ids
        self.notif_spm_lokal_partners_ids = self.company_id.notif_spm_lokal_partners_ids
        self.notif_spm_direksi_partners_ids = self.company_id.notif_spm_direksi_partners_ids
        self.logistik_user_ids = self.company_id.logistik_user_ids
        
    @api.one
    def set_logistik_spm_config(self):
        if self.verifikasi_kode_barang_partners_ids != self.company_id.verifikasi_kode_barang_partners_ids:
            self.company_id.verifikasi_kode_barang_partners_ids = self.verifikasi_kode_barang_partners_ids
        if self.notif_kode_barang_baru_partners_ids != self.company_id.notif_kode_barang_baru_partners_ids:
            self.company_id.notif_kode_barang_baru_partners_ids = self.notif_kode_barang_baru_partners_ids
        if self.notif_spm_lokal_partners_ids != self.company_id.notif_spm_lokal_partners_ids:
            self.company_id.notif_spm_lokal_partners_ids = self.notif_spm_lokal_partners_ids
        if self.notif_spm_direksi_partners_ids != self.company_id.notif_spm_direksi_partners_ids:
            self.company_id.notif_spm_direksi_partners_ids = self.notif_spm_direksi_partners_ids
        if self.logistik_user_ids != self.company_id.logistik_user_ids:
            self.company_id.logistik_user_ids = self.logistik_user_ids
        
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    verifikasi_kode_barang_partners_ids = fields.Many2many('res.partner', 'verifikasi_kode_barang_partners_rel', 'config_id', 'partner_id', 'Partner Verifikasi Kode Barang',
                                                       compute='compute_logistik_spm_config', inverse='set_logistik_spm_config')
    notif_kode_barang_baru_partners_ids = fields.Many2many('res.partner', 'notif_kode_barang_baru_partners_rel', 'config_id', 'partner_id', 'Partner Notifikasi Kode Barang Baru',
                                                       compute='compute_logistik_spm_config', inverse='set_logistik_spm_config')
    notif_spm_lokal_partners_ids = fields.Many2many('res.partner', 'notif_spm_lokal_partners_rel', 'config_id', 'partner_id', 'Partner Notifikasi SPM Lokal',
                                                compute='compute_logistik_spm_config', inverse='set_logistik_spm_config')
    notif_spm_direksi_partners_ids = fields.Many2many('res.partner', 'notif_spm_direksi_partners_rel', 'config_id', 'partner_id', 'Partner Notifikasi SPM Direksi',
                                                  compute='compute_logistik_spm_config', inverse='set_logistik_spm_config')
    logistik_user_ids = fields.Many2many('res.users', 'logistik_users_config_rel', 'config_id', 'user_id', 'Logistik User',
                                         compute='compute_logistik_spm_config', inverse='set_logistik_spm_config')
    
    
class res_company(models.Model):
    _inherit = 'res.company'
    
    verifikasi_kode_barang_partners_ids = fields.Many2many('res.partner', 'verifikasi_kode_barang_partners_rel', 'config_id', 'partner_id', 'Partner Verifikasi Kode Barang')
    notif_kode_barang_baru_partners_ids = fields.Many2many('res.partner', 'notif_kode_barang_baru_partners_rel', 'config_id', 'partner_id', 'Partner Notifikasi Kode Barang Baru')
    notif_spm_lokal_partners_ids = fields.Many2many('res.partner', 'notif_spm_lokal_partners_rel', 'config_id', 'partner_id', 'Partner Notifikasi SPM Lokal')
    notif_spm_direksi_partners_ids = fields.Many2many('res.partner', 'notif_spm_direksi_partners_rel', 'config_id', 'partner_id', 'Partner Notifikasi SPM Direksi')
    logistik_user_ids = fields.Many2many('res.users', 'logistik_users_config_rel', 'config_id', 'user_id', 'Logistik User')
    
    