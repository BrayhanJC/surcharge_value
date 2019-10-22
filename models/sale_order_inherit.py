# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    Autor: Brayhan Andres Jaramillo Castaño
#    Correo: brayhanjaramillo@hotmail.com
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from odoo import api, fields, models, _
import time
from datetime import datetime, timedelta, date
import logging
_logger = logging.getLogger(__name__)
from odoo import modules
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class SaleOrderInherit(models.Model):

	_inherit = "sale.order"

	surcharge = fields.Boolean('Rescargo')
	amount1 = fields.Float('AIU 1 (%)',digits=dp.get_precision('Discount'))
	amount2 = fields.Float('AIU 2 (%)',digits=dp.get_precision('Discount'))
	amount3 = fields.Float('AIU 3 (%)',digits=dp.get_precision('Discount'))
	amount_surcharge = fields.Float(string= 'AIU (%)', readonly=True, store=True)
	amount_surcharge_vale = fields.Monetary(string= 'AIU', readonly=True, store=True)

	@api.depends('order_line.price_total')
	def _amount_all(self):
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.order_line:
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax

			order.update({
				'amount_untaxed': amount_untaxed,
				'amount_tax': amount_tax,
				'amount_total': amount_untaxed + amount_tax + order.amount_surcharge_vale,
			})
			
	@api.multi
	def update_sale_order(self):

		amount_surcharge = (self.amount1 or 0) + (self.amount2 or 0) + (self.amount3 or 0)

		self.amount_surcharge = amount_surcharge

		value_amount_surgical = 0

		if amount_surcharge > 0:

			if len(self.order_line) > 0:

				data_product_pack = []
				for value in self.order_line:

					if value.product_id.pack_line_ids:

						for product in value.product_id.pack_line_ids:
							data_product_pack.append(product.product_id.id)

				for x in self.order_line:

					if x.product_id:

						if x.product_id.id not in data_product_pack:
							_logger.info(x.product_id.id)
							amount_surcharge_vale = (x.price_unit * (amount_surcharge/100))
							value_amount_surgical += amount_surcharge_vale * x.product_uom_qty

							price = x.price_unit * (1 - (x.discount or 0.0) / 100.0)
							taxes = x.tax_id.compute_all(price, x.order_id.currency_id, x.product_uom_qty, product=x.product_id, partner=x.order_id.partner_shipping_id)
					
							vals={	'amount1': self.amount1 or 0,
									'amount2': self.amount2 or 0,
									'amount3': self.amount3 or 0,
									'amount_surcharge': amount_surcharge,
									#'price_subtotal': taxes['total_included'] + ((x.price_unit * (amount_surcharge/100)) * x.product_uom_qty)
									'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
									'price_total': taxes['total_included'],
									'price_subtotal': taxes['total_excluded'],

									}
							x.write(vals)

				self.amount_surcharge_vale = value_amount_surgical

				amount_untaxed = 0
				amount_tax = 0

				for line in self.order_line:
					amount_untaxed += line.price_subtotal
					amount_tax += line.price_tax

				self.amount_total = amount_untaxed + amount_tax + self.amount_surcharge_vale
		else:

			raise ValidationError(_('Para poder generar un recargo, los porcentajes deberían sumar más de 0'))



SaleOrderInherit()