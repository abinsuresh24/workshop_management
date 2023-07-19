# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    """Class inherited for adding pay later boolean button in contacts"""
    _inherit = "res.partner"

    pay_on_account = fields.Boolean(string="Pay on account",
                                    help="If enabled pay later option on car"
                                         " services")
