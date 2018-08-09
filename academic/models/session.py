from odoo import api, fields, models, _

class Session(models.Model):
    _name = 'academic.session'

    name = fields.Char("Name", required=True)
    course_id = fields.Many2one(comodel_name='academic.course', string='Course', required=True)
    instructor_id = fields.Many2one(comodel_name='res.partner', string='Instructor', required=True)
    start_date = fields.Date(string='Start Date')
    duration = fields.Integer(string='Duration')
    seats = fields.Integer()
    active = fields.Boolean()

    attendee_ids = fields.One2many(comodel_name="academic.attendee", inverse_name="session_id", string="Attendees", required=False)
