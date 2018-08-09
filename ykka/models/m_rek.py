from odoo import models, fields, api

class rekening_peserta(models.Model):
    _name = 'ykka.rek_peserta'
    _order = 'rek_bank asc'

    peserta_id = fields.Many2one('ykka.peserta')
    name = fields.Char(string='Atas Nama')
    rek_no = fields.Char(string='Nomer Rekening')
    rek_bank = fields.Char(string='Bank')
    rek_dipakai = fields.Boolean(string='Gunakan')


    _sql_constraints = [
        ('unique_kode', 'unique(rek_no)', 'Nomer rek sudah digunakan, mohon cek kembali!'),
    ]
