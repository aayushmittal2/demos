import unittest
from collateral.HandleGraphs import RunOneGraph
from collateral.CollateralsDatas import CollateralsDatas
from collateral.HairCut import CategoryCollection, CurrencyCollection

class TestHandleGraphs(unittest.TestCase):
    def setUp(self):
        """Set up mock data and initialize necessary objects."""
        # Sample input data
        self.sample_input_data = {
            "collaterals": {
                "CASHWITHINSG_7000001_CAVN70000001": {
                    "id": "CASHWITHINSG_7000001_CAVN70000001",
                    "eligibleExposures": [
                        "PARENT_C00000010",
                        "PARENT_C00000011",
                        "C0000001",
                        "C0000002",
                        "C0000003",
                    ],
                    "assetType": "Deposit",
                    "marketValue": 2500000,
                    "currency": "EUR",
                    "assetST": 0.05,
                    "eligibiltyFlag": True,
                    "assetIssuerType": "SampleIssuer",
                    "fundFlag": False,
                    "economicSector": "Finance",
                    "corelationFactor": 0.203,
                    "enhanceabilityLevel": "medium",
                    "enhanceabilityFlag": True,
                    "realAssetFlag": True,
                    "isDerivativeFlag": False,
                    "monoMultiFlag": True,
                }
            },
            "exposures": {
                "C0000001": {
                    "id": "C0000001",
                    "parentID": "PARENT_C00000010",
                    "exposureCurrency": "EUR",
                    "exposureAmount": 4000000,
                    "exposureType": "OVERDRAFT",
                    "derivativeFlag": False,
                    "eligibleCollaterals": ["CASHWITHINSG_7000001_CAVN70000001"],
                }
            },
            "currencyCategories": {
                "A": {"stressFactor": 0.07, "currencies": ["CAD", "EUR"]},
                "B": {"stressFactor": 0.1, "currencies": ["AUD", "CNY"]},
            },
            "currencyExchangeRates": {
                "AED": {"rate": 0.24842, "date": "2024-01-08"},
                "USD": {"rate": 0.9124, "date": "2024-01-08"},
                "EUR": {"rate": 1.0, "date": "2024-01-08"},
            },
        }

        # Mocked category and currency collections
        self.category_collection = CategoryCollection(self.sample_input_data["currencyCategories"])
        self.currency_collection = CurrencyCollection(self.sample_input_data["currencyExchangeRates"])

        # Initialize CollateralsDatas
        self.collaterals_datas = CollateralsDatas(json_datas=self.sample_input_data)

        # Initialize RunOneGraph
        self.run_one_graph = RunOneGraph(
            graph=self.collaterals_datas.graphs[0],
            num=1,
            ct_calc=self.collaterals_datas._ct_calc,
            nb_virtual_assets=self.collaterals_datas.nb_virtual_assets,
        )

    def test_run_one_graph(self):
        """Test the main run logic of RunOneGraph."""
        self.run_one_graph.run()
        self.assertGreater(len(self.run_one_graph.graphs_links), 0)

    def test_run_solver(self):
        """Test the solver initialization and execution."""
        solver = self.run_one_graph.run_solver(self.collaterals_datas.graphs[0], optimize_coll=False)
        self.assertIsNotNone(solver)

    def test_update_graph(self):
        """Test updating graph after running the solver."""
        self.run_one_graph.run_solver(self.collaterals_datas.graphs[0], optimize_coll=True)
        self.run_one_graph.update_graph(self.collaterals_datas.graphs[0])

        # Validate updated DB values
        collateral = self.collaterals_datas.graphs[0]["collaterals"]["CASHWITHINSG_7000001_CAVN70000001"]
        self.assertGreater(collateral.db, 0)

    def test_check_link_zero(self):
        """Test removal of zero-value links."""
        solver = self.run_one_graph.run_solver(self.collaterals_datas.graphs[0], optimize_coll=False)
        updated_graph, is_zero_link = self.run_one_graph.check_link_zero(
            self.collaterals_datas.graphs[0], solver
        )
        self.assertFalse(is_zero_link)

    def test_create_direct_links(self):
        """Test creation of direct links."""
        single_exposure_graph = {
            "collaterals": {
                "C2": {
                    "id": "C2",
                    "amount_eur": 3000000.0,
                    "currency": "USD",
                    "eligibleExposures": ["E2"],
                }
            },
            "exposures": {
                "E2": {
                    "id": "E2",
                    "amount_eur": 1000000.0,
                    "currency": "USD",
                    "eligibleCollaterals": ["C2"],
                }
            },
        }
        direct_links = self.run_one_graph._create_direct_links(single_exposure_graph, {}, "sub_graph_1")
        self.assertIn(("C2", "E2"), direct_links.keys())
        self.assertEqual(
            direct_links[("C2", "E2")]["value"], 3000000.0 * (1 - 0.0)
        )

    def test_propagate_db_to_coll(self):
        """Test that DB values are propagated correctly."""
        self.run_one_graph.run_solver(self.collaterals_datas.graphs[0], optimize_coll=True)
        self.run_one_graph.update_graph(self.collaterals_datas.graphs[0])

        for c_id, collateral in self.collaterals_datas.graphs[0]["collaterals"].items():
            self.assertGreaterEqual(collateral.db, 0)


if __name__ == "__main__":
    unittest.main()
