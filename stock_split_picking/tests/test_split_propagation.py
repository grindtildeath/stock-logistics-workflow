# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestSplitPropagation(TransactionCase):

    def setUp(self):
        super().setUp()
        ref = self.env.ref
        self.env['res.config.settings'].create({
            'group_stock_multi_locations': True,
            'group_stock_adv_location': True
        }).execute()
        self.warehouse = self.env['stock.warehouse'].create({
            'name': 'TEST WAREHOUSE',
            'code': 'TEST 3 STEPS',
            'reception_steps': 'three_steps',
        })
        self.product = ref('stock.product_icecream')
        self.warehouse.write({
            'reception_steps': 'three_steps',
        })
        self.picking_type_receipts = ref('stock.picking_type_in')
        self.location_suppliers = ref('stock.stock_location_suppliers')
        self.location_input = ref('stock.stock_location_company')


    def test_split_propagation(self):
        in_picking = self.env['stock.picking'].create({
            'name': '/',
            'picking_type_id': self.warehouse.in_type_id.id,
            'location_id': self.location_suppliers.id,
            'location_dest_id': self.warehouse.wh_input_stock_loc_id.id,
            'move_lines': [(0, 0, {
                'name': self.product.name,
                'product_id': self.product.id,
                'product_uom': self.product.product_tmpl_id.uom_id.id,
                'product_uom_qty': 200.0,
                'qty_done': 200.0
            })]
        })
        in_picking.move_lines.onchange_product_id()
        in_picking.button_validate()
        input_to_qc_move = in_picking.move_lines.move_dest_ids
        input_to_qc_picking = input_to_qc_move.picking_id
        # qc_to_stock_move = input_to_qc_move.move_dest_ids
        # qc_to_stock_picking = qc_to_stock_move.picking_id
        # Split Input to QC with 50.0, backorder of 150.0
        input_to_qc_move.quantity_done = 50.0
        input_to_qc_picking.split_process()
        # Check split move
        self.assertEqual(input_to_qc_move.product_uom_qty, 50.0)
        # Check backorder move
        input_to_qc_backorder = self.env['stock.picking'].search([
            ('backorder_id', '=', input_to_qc_picking.id)
        ])
        self.assertEqual(input_to_qc_backorder.move_lines.product_id,
                         self.product)
        self.assertEqual(input_to_qc_backorder.move_lines.product_uom_qty,
                         150.0)
        # Check destination moves
        self.assertEqual(len(input_to_qc_move.move_dest_ids), 1)
        self.assertEqual(input_to_qc_move.move_dest_ids.product_id,
                         self.product)
        self.assertEqual(input_to_qc_move.move_dest_ids.product_uom_qty,
                         50.0)
        self.assertEqual(input_to_qc_backorder.move_lines.move_dest_ids.product_id,
                         self.product)
        self.assertEqual(input_to_qc_backorder.move_lines.move_dest_ids.product_uom_qty,
                         150.0)
