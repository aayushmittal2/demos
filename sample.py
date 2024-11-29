import unittest
from collateral.HandleGraphs import RunOneGraph
from collateral.CollateralsDatas import CollateralsDatas
from collateral.CurrencyCollection import CurrencyCollection


class TestHandleGraphs(unittest.TestCase):
    def setUp(self):
        """Set up mock data and initialize necessary objects."""
        # Sample input data mimicking the structure used in your actual program
        self.sample_currency_data = {
            "EUR": {"rate": 1.0},
            "USD": {"rate": 1.1},
        }

        self.sample_collaterals = {
            "C1": {
                "amount_eur": 2000000.0,
                "currency": "EUR",
                "eligibleExposures": ["E1"],
                "db": 0,
                "assetST": 0.05,
                "enhanceabilityFlag": True,
                "enhanceabilityLevel": "high",
                "amount": 2000000.0,
            },
        }

        self.sample_exposures = {
            "E1": {
                "amount_eur": 1500000.0,
                "currency": "EUR",
                "eligibleCollaterals": ["C1"],
                "eng_value": 1500000.0,
                "ct": 0,
            },
        }

        self.sample_graph = {
            "collaterals": self.sample_collaterals,
            "exposures": self.sample_exposures,
        }

        # Initialize currency collection and dummy CollateralsDatas
        self.currency_collection = CurrencyCollection(self.sample_currency_data)
        self.collaterals_datas = CollateralsDatas(json_datas=self.sample_graph)

        # Initialize RunOneGraph with mock data
        self.run_one_graph = RunOneGraph(
            self.sample_graph, 1, self.collaterals_datas._ct_calc, 10
        )

    def test_run_one_graph(self):
        """Test the main run logic of RunOneGraph."""
        self.run_one_graph.run()
        self.assertGreater(len(self.run_one_graph.graphs_links), 0)

    def test_run_solver(self):
        """Test that the solver runs successfully and returns a valid object."""
        solver = self.run_one_graph.run_solver(self.sample_graph, optimize_coll=False)
        self.assertIsNotNone(solver)

    def test_update_graph(self):
        """Test that the graph updates DB and CT values after solver runs."""
        self.run_one_graph.run_solver(self.sample_graph, optimize_coll=True)
        self.run_one_graph.update_graph(self.sample_graph)

        # Check that DB is updated for the collateral
        collateral = self.sample_graph["collaterals"]["C1"]
        self.assertGreater(collateral["db"], 0)

    def test_check_link_zero(self):
        """Test that links with zero allocation are removed."""
        solver = self.run_one_graph.run_solver(self.sample_graph, optimize_coll=False)
        updated_graph, is_zero_link = self.run_one_graph.check_link_zero(
            self.sample_graph, solver
        )
        self.assertFalse(is_zero_link)

    def test_add_allocation_graph(self):
        """Test adding an allocation to the graph."""
        link = {"Exposure_id": "E1", "ct_eligible": True}
        cur_allocation_graph = {"allocations": []}
        cur_allocation = self.run_one_graph.add_allocation(
            cur_allocation_graph, link
        )
        self.assertIn("E1", [a["Exposure_id"] for a in cur_allocation["allocations"]])

    def test_update_coverpercentage(self):
        """Test updating the coverage percentage."""
        prev_allocation = {"coveragePercentage": 50}
        prev_link = {"eng_expo": 100}
        self.run_one_graph.update_coverpercentage(prev_allocation, prev_link)
        self.assertEqual(prev_allocation["coveragePercentage"], 50)

    def test_create_direct_links(self):
        """Test creating direct links when there is only one exposure."""
        single_exposure_graph = {
            "collaterals": {
                "C2": {"amount_eur": 3000000.0, "currency": "USD"},
            },
            "exposures": {
                "E2": {"amount_eur": 1000000.0, "currency": "USD"},
            },
        }
        direct_links = self.run_one_graph._create_direct_links(
            single_exposure_graph, {}, "sub_graph_1"
        )
        self.assertIn(("C2", "E2"), direct_links.keys())
        self.assertEqual(
            direct_links[("C2", "E2")]["value"], 3000000.0 * (1 - 0)  # Adjusted value
        )

    def test_propagate_db_to_coll(self):
        """Test that DB values are propagated to all collaterals."""
        self.run_one_graph.run_solver(self.sample_graph, optimize_coll=True)
        self.run_one_graph.update_graph(self.sample_graph)

        for c_id, collateral in self.sample_graph["collaterals"].items():
            self.assertGreaterEqual(collateral["db"], 0)


if __name__ == "__main__":
    unittest.main()
