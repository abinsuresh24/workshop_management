# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MaterialOrder(models.Model):
    """Class defined for adding used parts in the work order"""
    _name = 'material.order'
    _description = "material order details"

    materials_id = fields.Many2one('product.product', string="Materials")
    quantity = fields.Float(string="Quantity")
    price = fields.Float(string="Unit price")
    total_price = fields.Float(string="Total")
    material_order_id = fields.Many2one('work.order')

    @api.onchange('quantity', 'price')
    def total_amount(self):
        """Function defined for calculating total price of the product"""
        self.total_price = self.quantity * self.price
