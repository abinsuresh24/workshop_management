# -*- coding: utf-8 -*-
from odoo import fields, models


class OtherComplaints(models.TransientModel):
    """Class defined for creating wizard for adding additional notes"""
    _name = 'other.complaints'
    _description = 'Other complaints wizard'

    other_complaints = fields.Html(string="Other complaints")
    appointment = fields.Char(string='Appointment')

    def confirm_complaints(self):
        """Function defined for adding notes to appointment when confirming"""
        active_id = self.env.context.get('active_id')
        if self.other_complaints:
            self.env['workshop.appointment'].search(
                [('id', '=', active_id)]).write(
                {'state': 'received', 'notes': self.other_complaints})
