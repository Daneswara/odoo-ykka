# -*- coding: utf-8 -*-

"""Author:
	@CakJuice <hd.brandoz@gmail.com>

Website:
	https://cakjuice.com
"""

from odoo import models, fields

class KaHrPangkat(models.Model):
    """Master data of employee job rank.

    _name = 'hr.pangkat'
    """

    _name = 'hr.pangkat'

    name = fields.Char(string="Nama", size=64, required=True)
