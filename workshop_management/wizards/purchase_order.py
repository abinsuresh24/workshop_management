# -*- coding: utf-8 -*-
from odoo import fields, models


class PurchaseOrder(models.TransientModel):
    """Class defined for creating wizard for adding additional notes"""
    _name = 'work.purchase'
    _description = 'Purchase Order wizard'

    product_id = fields.Many2one('product.product', string="Product")
    vendor_id = fields.Many2one('res.partner', string='Vendor')
    order_details = fields.Char(string="Order no")

    def confirm_order(self):
        """Function defined for creating purchase order for materials"""
        if self.vendor_id and self.product_id:
            self.env['purchase.order'].create({"partner_id": self.vendor_id.id,
                                               'origin': self.order_details,
                                               'order_line': [
                                                   fields.Command.create(
                                                       {
                                                'product_id': self.product_id.id
                                                           })]})
