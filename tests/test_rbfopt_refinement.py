"""Test the refinement routines in RBFOpt.

This module contains unit tests for the module rbfopt_refinement.

Licensed under Revised BSD license, see LICENSE.
(C) Copyright International Business Machines Corporation 2017.

"""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import unittest
import numpy as np
import test_rbfopt_env
import rbfopt_refinement as ref
import rbfopt_utils as ru
from rbfopt_settings import RbfoptSettings

def dist(a, b):
    """Distance function, for convenience reimplemented here.
    """
    return np.sqrt(np.dot(a-b, a-b))

class TestRefinement(unittest.TestCase):
    """Test the rbfopt_refinement module."""

    def setUp(self):
        """Create data for subsequent tests."""
        self.n = 3
        self.k = 10
        self.var_lower = np.array([i for i in range(self.n)])
        self.var_upper = np.array([i + 10 for i in range(self.n)])
        self.node_pos = np.array([self.var_lower, self.var_upper,
                                  [1, 2, 3], [9, 5, 8.8], [5.5, 7, 12],
                                  [3.2, 10.2, 4], [2.1, 1.1, 7.4], 
                                  [6.6, 9.1, 2.0], [10, 8.8, 11.1], 
                                  [7, 7, 7]])
        self.node_val = np.array([2*i for i in range(self.k)])
        self.integer_vars = np.array([0, 2])
        # Compute maximum distance between nodes
        max_dist = 0
        for node1 in self.node_pos:
            for node2 in self.node_pos:
                max_dist = max(max_dist, dist(node1, node2))
        self.max_dist = max_dist
    # -- end function        

    def test_init_trust_region(self):
        """Test the init_trust_region function.

        """
        settings = RbfoptSettings()
        # Compute maximum distance between nodes
        for k in range(2, self.k):
            model_set, radius = ref.init_trust_region(settings, self.n, k, 
                                                      self.node_pos[:k], 
                                                      self.node_pos[k-1])
            self.assertEqual(len(model_set), min(k, self.n + 1),
                             msg='Wrong size of model set')
            self.assertLessEqual(radius, self.max_dist)
    # -- end function

    def test_get_linear_model(self):
        """Test the get_linear_model function.

        """
        settings = RbfoptSettings()
        model_set = np.arange(self.k)
        for i in range(5):
            h = np.random.rand(self.n)
            b = np.random.rand()
            node_val = (np.dot(h, self.node_pos.T)).T + b
            hm, bm = ref.get_linear_model(settings, self.n, self.k, 
                                          self.node_pos, node_val, model_set)
            self.assertAlmostEqual(dist(h, hm), 0,
                                   msg='Wrong linear part of linear model')
            self.assertAlmostEqual(b - bm, 0,
                                   msg='Wrong constant part of linear model')
    # -- end function

    def test_get_candidate_point(self):
        """Test the get_candidate_point function.

        """
        settings = RbfoptSettings()
        model_set = np.arange(self.k)
        for i in range(self.k):
            h = np.random.rand(self.n)
            b = np.random.rand()
            tr_radius = np.random.uniform(self.max_dist/2)
            point, diff, grad_norm = ref.get_candidate_point(
                settings, self.n, self.k, self.var_lower, self.var_upper, 
                h, self.node_pos[i], tr_radius)
            self.assertGreaterEqual(np.dot(h, self.node_pos[i]),
                                    np.dot(h, point),
                                    msg='Function value did not decrease')
            self.assertLessEqual(dist(self.node_pos[i], point), 
                                 tr_radius + 1.0e-6,
                                 msg='Point moved too far')
            self.assertAlmostEqual(diff, np.dot(h, self.node_pos[i] - point),
                                   msg='Wrong model difference estimate')
            self.assertAlmostEqual(grad_norm, dist(h, np.zeros(self.n)),
                                   msg='Wrong gradient norm')
            for j in range(self.n):
                self.assertLessEqual(self.var_lower[j], point[j],
                                     msg='Point outside bounds')
                self.assertGreaterEqual(self.var_upper[j], point[j],
                                     msg='Point outside bounds')
    # -- end function

    def test_get_integer_candidate(self):
        """Test the get_integer_candidate function.

        """
        settings = RbfoptSettings()
        model_set = np.arange(self.k)
        for i in range(self.k):
            h = np.random.rand(self.n)
            b = np.random.rand()
            tr_radius = np.random.uniform(self.max_dist/2)
            candidate, diff, grad_norm = ref.get_candidate_point(
                settings, self.n, self.k, self.var_lower, self.var_upper, 
                h, self.node_pos[i], tr_radius)
            point, diff = ref.get_integer_candidate(
                settings, self.n, self.k, h, self.node_pos[i], 
                tr_radius, candidate, self.integer_vars)
            self.assertAlmostEqual(diff, np.dot(h, candidate - point),
                                   msg='Wrong model difference estimate')
            for j in range(self.n):
                self.assertLessEqual(self.var_lower[j], point[j],
                                     msg='Point outside bounds')
                self.assertGreaterEqual(self.var_upper[j], point[j],
                                     msg='Point outside bounds')
            for j in self.integer_vars:
                self.assertEqual(np.floor(point[j] + 0.5), int(point[j]),
                                 msg='Point is not integer')
    # -- end function

    def test_update_trust_region_radius(self):
        """Test the update_trust_region_radius function.

        """
        settings = RbfoptSettings()
        model_diff = 10.0
        tr_radius = 1.0
        new_tr_radius, move = ref.update_trust_region_radius(
            settings, tr_radius, model_diff,
            model_diff * settings.tr_acceptable_decrease_shrink - 1.0e-3)
        self.assertLess(new_tr_radius, tr_radius,
                        msg='Trust region radius did not decrease')
        new_tr_radius, move = ref.update_trust_region_radius(
            settings, tr_radius, model_diff,
            model_diff * settings.tr_acceptable_decrease_enlarge + 1.0e-3)
        self.assertGreater(new_tr_radius, tr_radius,
                           msg='Trust region radius did not increase')
        new_tr_radius, move = ref.update_trust_region_radius(
            settings, tr_radius, model_diff,
            model_diff * settings.tr_acceptable_decrease_move + 1.0e-3)
        self.assertTrue(move, msg='Candidate point did not move')
                         
    # -- end function

# -- end class

if (__name__ == '__main__'):
    unittest.main()
