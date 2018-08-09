# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from dateutil.parser import parse

class peserta(models.Model):
    _name = 'ykka.peserta'
    _order = 'kode asc'

    name = fields.Char()
    kode = fields.Char(string='ID', default='/', readonly=True)
    tanggal_kepesertaan = fields.Date()
    status = fields.Selection([
        ('aktif','Aktif'),
        ('pensiun','Pensiun'),
    ], string='Status')

    history_jabatan = fields.One2many('ykka.jabatan_peserta', 'peserta_id', 'History Jabatan')
    rekening = fields.One2many('ykka.rek_peserta', 'peserta_id', 'Rekening Penerima')

    _sql_constraints = [
        ('unique_kode', 'unique(id, name)', 'kombinasi id dan nama sudah digunakan, mohon cek kembali !'),
    ]

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('ykka.peserta.seq') or '/'
        vals['kode'] = seq
        return super(peserta, self).create(vals)

    # def create(self, vals):
    #     seq = self.env['ir.sequence'].search([
    #         ('code', '=', 'ykka.peserta.seq')
    #     ], limit=1);
    #
    #     if seq:
    #         vals['kode'] = seq.next_by_id()
    #         print(vals['kode'])
    #     return
    #     return super(peserta, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for me_id in self :
            if me_id.kode and me_id.kode != '/' :
                result.append((me_id.id, "%s - %s" % (me_id.kode, me_id.name)))
            else :
                result.append((me_id.id, me_id.name))
        return result

class kas(models.Model):
    _name = 'kas'
