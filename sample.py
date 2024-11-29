import unittest
import json
from collateral.HandleGraphs import RunOneGraph
from collateral.CollateralsDatas import CollateralsDatas
from collateral.CurrencyCollection import CurrencyCollection


class TestHandleGraphs(unittest.TestCase):
    def setUp(self):
        self.input_file_path = r"C:\Users\amittal070422\Downloads\input.json"
        with open(self.input_file_path, 'r') as file:
            self.valid_json_data = json.load(file)

        # Initialize necessary objects
        self.collaterals_datas = CollateralsDatas(json_datas=self.valid_json_data)
        self.collaterals_datas.launch_engine()

        self.graph = self.collaterals_datas._graphs[0]  # Assume we take the first graph
        self.ct_calc = self.collaterals_datas._ct_calc
        self.nb_virtual_assets = self.collaterals_datas._nb_virtual_assets

    def test_run_one_graph(self):
        """Test that RunOneGraph properly runs on a graph."""
        run_one_graph = RunOneGraph(self.graph, 1, self.ct_calc, self.nb_virtual_assets)
        run_one_graph.run()
        self.assertGreater(len(run_one_graph.graphs_links), 0)

    def test_run_solver(self):
        """Test that the solver runs successfully and returns a valid object."""
        run_one_graph = RunOneGraph(self.graph, 1, self.ct_calc, self.nb_virtual_assets)
        solver = run_one_graph.run_solver(self.graph, optimize_coll=False)
        self.assertIsNotNone(solver)

    def test_update_graph(self):
        """Test that the graph is updated after running the solver."""
        run_one_graph = RunOneGraph(self.graph, 1, self.ct_calc, self.nb_virtual_assets)
        run_one_graph.run_solver(self.graph, optimize_coll=True)
        run_one_graph.update_graph(self.graph)
        # Assert that DB is updated for the collateral
        self.assertGreater(self.graph["collaterals"]["C1"].db, 0)

    def test_check_link_zero(self):
        """Test that zero links are removed from the graph."""
        run_one_graph = RunOneGraph(self.graph, 1, self.ct_calc, self.nb_virtual_assets)
        solver = run_one_graph.run_solver(self.graph, optimize_coll=False)
        graph, is_zero_link = run_one_graph.check_link_zero(self.graph, solver)
        self.assertFalse(is_zero_link)

    def test_add_allocation_graph(self):
        """Test adding an allocation to the graph."""
        run_one_graph = RunOneGraph(self.graph, 1, self.ct_calc, self.nb_virtual_assets)
        link = {"Exposure_id": "E1", "ct_eligible": True}
        cur_allocation_graph = {"allocations": []}
        cur_allocation = run_one_graph.add_allocation(cur_allocation_graph, link)
        self.assertIn("E1", cur_allocation["allocations"])

    def test_update_coverpercentage(self):
        """Test updating the coverage percentage."""
        run_one_graph = RunOneGraph(self.graph, 1, self.ct_calc, self.nb_virtual_assets)
        prev_allocation = {"coveragePercentage": 50}
        prev_link = {"eng_expo": 100}
        run_one_graph.update_coverpercentage(prev_allocation, prev_link)
        self.assertEqual(prev_allocation["coveragePercentage"], 50)

    def test_create_direct_links(self):
        """Test direct link creation when there is only one exposure."""
        run_one_graph = RunOneGraph(self.graph, 1, self.ct_calc, self.nb_virtual_assets)
        self.graph["exposures"] = {"E1": {"amount_eur": 100}}
        self.graph["collaterals"] = {"C1": {"amount_eur": 200}}
        direct_links = run_one_graph._create_direct_links(self.graph, {}, "sub_graph_1")
        self.assertIn(("C1", "E1"), direct_links.keys())
        self.assertEqual(direct_links[("C1", "E1")]["value"], 200)

    def test_propagate_db_to_coll(self):
        """Test that DB is propagated to all collaterals."""
        run_one_graph = RunOneGraph(self.graph, 1, self.ct_calc, self.nb_virtual_assets)
        solver = run_one_graph.run_solver(self.graph, optimize_coll=True)
        run_one_graph.update_graph(self.graph)
        for c_id, collateral in self.graph["collaterals"].items():
            self.assertGreaterEqual(collateral.db, 0)  # DB should be non-negative


if __name__ == "__main__":
    unittest.main()
