# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class WorkOrders(CustomerPortal):
    """Class defined for getting details of work order from the backend and
    inherited for customize customer portal in the website"""

    def _prepare_home_portal_values(self, counters):
        """Inherited function for adding work orders in the portal"""
        user = request.env.user
        partner = user.partner_id.id
        val = super(WorkOrders, self)._prepare_home_portal_values(counters)
        val['order_count'] = request.env['work.order'].sudo().search_count(
            [('customer_id', '=', partner)])
        return val

    @http.route('/my/work_order_web', type='http', auth='public', website=True)
    def track_order_web(self):
        """Function defined for getting details from work order
        and pass it to the front end"""
        user = request.env.user
        partner = user.partner_id.id
        order = request.env['work.order'].sudo().search(
            [('customer_id', '=', partner)])
        return request.render("workshop_management.work_order_portal_list",
                              {'orders': order})

    @http.route('/my/work_order_web/<model("work.order"):order_id>',
                type='http', auth='public', website=True)
    def orders(self, order_id):
        """Function defined for setting approve button in the customer portal"""
        vals = {'orders': order_id}
        return request.render("workshop_management.work_order_portal_form",
                              vals)

    @http.route('/my/work_order_web/<model("work.order"):order_id>/approve',
                type='http', auth='public',
                website=True)
    def approve_appointment(self, order_id):
        order_id.write({'state': 'request_approved'})
        return request.render("workshop_management.work_order_portal_approve",
                              {'type': 'ir.actions.client', 'tag': 'reload'})

    @http.route('/my/work_order_web/<model("work.order"):order_id>/reject',
                type='http', auth='public',
                website=True)
    def reject_appointment(self, order_id):
        order_id.write({'state': 'request_rejected'})
        return request.render("workshop_management.work_order_portal_reject",
                              {'type': 'ir.actions.client', 'tag': 'reload'})
