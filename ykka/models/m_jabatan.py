from odoo import models, fields, api

class jabatan_peserta(models.Model):
    _name = 'ykka.jabatan_peserta'
    _order = 'tanggal_pengangkatan asc'

    peserta_id = fields.Many2one('ykka.peserta')
    jabatan = fields.Many2one('ykka.jabatan')
    tanggal_pengangkatan = fields.Date()


class jabatan(models.Model):
    _name = 'ykka.jabatan'

    name = fields.Char()
    jabatan_id = fields.One2many('ykka.jabatan_peserta', 'jabatan', 'Peserta')


    _sql_constraints = [
        ('unique_kode', 'unique(nama)', 'Nama Jabatan sudah ada, mohon cek kembali !'),
    ]
