import unittest
from collateral.HandleGraphs import RunOneGraph
from collateral.CollateralsDatas import CollateralsDatas


class TestHandleGraphs(unittest.TestCase):
    def setUp(self):
        """Set up mock input data and initialize necessary objects."""
        self.sample_input_data = {
            "collaterals": {
                "CASHWITHINSG_7000001_CAVN70000001": {
                    "id": "CASHWITHINSG_7000001_CAVN70000001",
                    "eligibleExposures": [
                        "PARENT_C00000010",
                        "PARENT_C00000011",
                        "C0000001",
                        "C0000002",
                        "C0000003"
                    ],
                    "assetType": "Deposit",
                    "marketValue": 2500000,
                    "currency": "EUR",
                    "assetST": 0,
                    "eligibiltyFlag": True,
                    "assetIssuerType": "Issuer1",
                    "fundFlag": False,
                    "economicSector": "Sector1",
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
            "currencyCategories": [
                {"category": "A", "stressFactor": 0.07, "currencies": ["CAD", "EUR"]},
                {"category": "B", "stressFactor": 0.1, "currencies": ["AUD", "CNY"]},
            ],
            "currencyExchangeRates": [
                {"currency": "AED", "rate": 0.24842, "date": "2024-01-08"},
                {"currency": "USD", "rate": 0.9124, "date": "2024-01-08"},
                {"currency": "EUR", "rate": 1.0, "date": "2024-01-08"},
            ],
        }

        # Initialize CollateralsDatas and RunOneGraph
        self.collaterals_datas = CollateralsDatas(json_datas=self.sample_input_data)
        self.run_one_graph = RunOneGraph(
            graph=self.collaterals_datas._graphs[0],
            num=1,
            ct_calc=self.collaterals_datas._ct_calc,
            nb_virtual_assets=self.collaterals_datas.nb_virtual_assets,
        )

    def test_run_one_graph(self):
        """Test the main `run` method of RunOneGraph."""
        self.run_one_graph.run()
        self.assertGreater(len(self.run_one_graph.graphs_links), 0)

    def test_run_solver(self):
        """Test the solver execution."""
        solver = self.run_one_graph.run_solver(
            self.collaterals_datas._graphs[0], optimize_coll=False
        )
        self.assertIsNotNone(solver)

    def test_update_graph(self):
        """Test the graph update functionality."""
        self.run_one_graph.run_solver(self.collaterals_datas._graphs[0], optimize_coll=True)
        self.run_one_graph.update_graph(self.collaterals_datas._graphs[0])

        collateral = self.collaterals_datas._graphs[0]["collaterals"][
            "CASHWITHINSG_7000001_CAVN70000001"
        ]
        self.assertGreater(collateral.db, 0)

    def test_check_link_zero(self):
        """Test removal of zero-value links."""
        solver = self.run_one_graph.run_solver(
            self.collaterals_datas._graphs[0], optimize_coll=False
        )
        updated_graph, is_zero_link = self.run_one_graph.check_link_zero(
            self.collaterals_datas._graphs[0], solver
        )
        self.assertFalse(is_zero_link)

    def test_add_allocation_graph(self):
        """Test adding an allocation graph."""
        link = {"Exposure_id": "C0000001", "ct_eligible": True}
        cur_allocation_graph = {"allocations": []}
        cur_allocation = self.run_one_graph.add_allocation(cur_allocation_graph, link)
        self.assertIn("C0000001", [a["exposureId"] for a in cur_allocation_graph["allocations"]])

    def test_update_coverpercentage(self):
        """Test coverage percentage updates."""
        prev_allocation = {"coveragePercentage": 0}
        prev_link = {"eng_expo": 100}
        self.run_one_graph.update_coverpercentage(prev_allocation, prev_link)
        self.assertEqual(prev_allocation["coveragePercentage"], 0)

    def test_create_direct_links(self):
        """Test creating direct links."""
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

    def test_propagate_db_to_coll(self):
        """Test DB propagation to collaterals."""
        self.run_one_graph.run_solver(self.collaterals_datas._graphs[0], optimize_coll=True)
        self.run_one_graph.update_graph(self.collaterals_datas._graphs[0])

        collateral = self.collaterals_datas._graphs[0]["collaterals"][
            "CASHWITHINSG_7000001_CAVN70000001"
        ]
        self.assertGreater(collateral.db, 0)


if __name__ == "__main__":
    unittest.main()
