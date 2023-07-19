# -*- coding: utf-8 -*-
from odoo import fields, models


class ExtraComponents(models.Model):
    """Class defined for adding extra components in the work order"""
    _name = 'extra.components'
    _description = "Extra components details"

    extra_components = fields.Char(string='Extra component')
    extra_comp_id = fields.Many2one('work.order', string="Work order")
