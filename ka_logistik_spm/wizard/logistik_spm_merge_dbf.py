import base64
from odoo import models, fields, api
from dbfpy import dbf
import tempfile

class WizardSpmMergeDbf(models.TransientModel):
    _name = 'wizard.spm.merge.dbf'
    _description = 'Merge DBF file with Odoo'

    file_input_header = fields.Binary("File Header")
    file_input_detail = fields.Binary("File Detail")
    file_output_header = fields.Binary("File Header", readonly=True)
    file_output_detail = fields.Binary("File Detail", readonly=True)
    file_name_header = fields.Char('Header File', default="LOGB1.DBF")
    pengajuan_ids = fields.Many2many('logistik.pengajuan.spm', 'wizard_merge_pengajuan_spm', 'wizard_spm_merge_id', 'pengajuan_spm_id', 'SPM Yang ditambahkan')
    state = fields.Selection([
        ('input', 'Kirim'),
        ('output', 'Download')
    ], string='Status', readonly=True, default='input')

    @api.multi
    def action_process(self):
        LOGB1_DBF = '%s.dbf' % tempfile.mkstemp()[1]
        LOGSP1_DBF = '%s.dbf' % tempfile.mkstemp()[1]
        header_dbf = open(LOGB1_DBF, 'w')
        detail_dbf = open(LOGSP1_DBF, 'w')
        
        #copy from record set into temporary file
        header_dbf.write(base64.decodestring(self.file_input_header))
        header_dbf.close()
        # detail_dbf.write(base64.decodestring(self.file_input_detail))
        # detail_dbf.close()

        #open file DBF
        dbLOGB1 = dbf.Dbf(LOGB1_DBF)
        rec = dbLOGB1.newRecord()
        rec['PENGAJU'] = 'XXX0011'
        rec.store()
        dbLOGB1.close()
        
        #open and read mofified database and bind to record set
        output = open(LOGB1_DBF, 'r').read()
        self.file_output_header = base64.encodestring(output)
        
        
        mod_obj = self.env['ir.model.data']
        self.write({'state':'output'})
        res = mod_obj.get_object_reference('ka_logistik_spm', 'view_spm_merge_dbf_form')
        view_id = res and res[1] or False
        return {
            'name': 'Update DBF File(SPM Lokal)',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.spm.merge.dbf',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_id': [view_id],
            'res_id': self.id, 
            'context': self._context,
        }
