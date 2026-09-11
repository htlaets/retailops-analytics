import unittest
from dataclasses import replace

from pipeline.run_pipeline import generate_orders, validate


class PipelineTests(unittest.TestCase):
    def test_generation_is_deterministic(self):
        self.assertEqual(generate_orders(5, 7), generate_orders(5, 7))

    def test_order_ids_are_unique(self):
        orders = generate_orders(100)
        self.assertEqual(len(orders), len({row.order_id for row in orders}))

    def test_invalid_quantity_is_rejected(self):
        orders = generate_orders(2)
        orders[0] = replace(orders[0], quantity=0)
        with self.assertRaises(AssertionError):
            validate(orders)


if __name__ == "__main__":
    unittest.main()
