"""Test the module rbfopt_aux_problems in RBFOpt.

This module contains unit tests for the module rbfopt_aux_problems.

Licensed under Revised BSD license, see LICENSE.
(C) Copyright International Business Machines Corporation 2016.

"""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import unittest
import numpy as np
import test_rbfopt_env
import rbfopt_aux_problems as aux
import rbfopt_utils as ru
from rbfopt_settings import RbfSettings

def quadratic(points):
    """Quadratic function for optimization.

    For each point in the given list, compute the sum of the squares
    of all coordinates.

    """
    return [sum(val*val for val in point) for point in points]
# -- end function

def shifted_quadratic(points):
    """Quadratic function for optimization.

    For each point in the given list, compute the sum of the squares
    of all coordinates shifted to the left by 1.

    """
    return [sum((val-1)*(val-1) for val in point) for point in points]
# -- end function

class TestAuxProblems(unittest.TestCase):
    """Test the successful solution of auxiliary problems."""

    def setUp(self):
        """Generate data to simulate an optimization problem."""
        self.settings = RbfSettings(rbf = 'cubic',
                                    num_samples_aux_problems = 10000,
                                    ga_base_population_size = 1000)
        self.n = 3
        self.k = 5
        self.var_lower = [i for i in range(self.n)]
        self.var_upper = [i + 10 for i in range(self.n)]
        self.node_pos = [self.var_lower, self.var_upper,
                         [1, 2, 3], [9, 5, 8.8], [5.5, 7, 12]]
        self.node_val = [2*i for i in range(self.k)]
        Amat = [[0.0, 5196.152422706633, 5.196152422706631,
                 1714.338065908822, 2143.593744305343, 0.0, 1.0, 2.0, 1.0],
                [5196.152422706633, 0.0, 3787.995116153135, 324.6869498824983,
                 218.25390174061036, 10.0, 11.0, 12.0, 1.0],
                [5.196152422706631, 3787.995116153135, 0.0, 1101.235503851924,
                 1418.557944049167, 1.0, 2.0, 3.0, 1.0], 
                [1714.338065908822, 324.6869498824983, 1101.235503851924, 
                 0.0, 136.3398894271225, 9.0, 5.0, 8.8, 1.0],
                [2143.593744305343, 218.25390174061036, 1418.557944049167,
                 136.3398894271225, 0.0, 5.5, 7.0, 12.0, 1.0],
                [0.0, 10.0, 1.0, 9.0, 5.5, 0.0, 0.0, 0.0, 0.0], 
                [1.0, 11.0, 2.0, 5.0, 7.0, 0.0, 0.0, 0.0, 0.0],
                [2.0, 12.0, 3.0, 8.8, 12.0, 0.0, 0.0, 0.0, 0.0],
                [1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0]]
        self.Amat = np.matrix(Amat)
        self.Amatinv = self.Amat.getI()
        self.rbf_lambda = [-0.02031417613815348, -0.0022571306820170587, 
                           0.02257130682017054, 6.74116235140294e-18,
                           -1.0962407017011667e-18]
        self.rbf_h = [-0.10953754862932995, 0.6323031632900591,
                      0.5216788297837124, 9.935450288253636]
        self.integer_vars = [1]
    # -- end function

    def test_pure_global_search(self):
        """Check solution of pure global search problem.

        This function verifies that the solution of the global search
        problem on a small test istance is relatively close to a
        pre-computed solution, for all algorithms. Relatively close
        here has a loose meaning because we cannot account for machine
        precision or random numbers that could cause the instance to
        give a very different solution. It also checks that integer
        variables are integer valued.
        """
        solutions = {'Gutmann' : [8.279843262880693, 8.0, 10.768370103772106],
                     'MSRSM' : [4.7403574071279078, 11, 2.3070673078496355]}
        for algorithm in RbfSettings._allowed_algorithm:
            for method in RbfSettings._allowed_global_search_method:
                self.settings.algorithm = algorithm
                self.settings.global_search_method = method
                ref = solutions[algorithm]
                sol = aux.pure_global_search(self.settings, self.n, self.k,
                                             self.var_lower, self.var_upper,
                                             self.integer_vars, 
                                             self.node_pos, self.Amat)
                for i in range(self.n):
                    tolerance = (self.var_upper[i] - self.var_lower[i])*0.2
                    lb = ref[i] - tolerance
                    ub = ref[i] + tolerance
                    msg_lb = ('Lb not satisfied on var {:d}: '.format(i) +
                              'lb {:f} solution {:f} '.format(lb, sol[i]) +
                              'alg {:s} '.format(algorithm) +
                              'method {:s}'.format(method))
                    msg_ub = ('Ub not satisfied on var {:d}: '.format(i) +
                              'ub {:f} solution {:f} '.format(ub, sol[i]) +
                              'alg {:s} '.format(algorithm) +
                              'method {:s}'.format(method))
                    self.assertLessEqual(lb, sol[i], msg = msg_lb)
                    self.assertLessEqual(sol[i], ub, msg = msg_ub)
                for i in self.integer_vars:
                    msg = ('Variable {:d} not integer in solution'.format(i)
                           + ' alg {:s} '.format(algorithm) +
                           'method {:s}'.format(method))
                    self.assertAlmostEqual(abs(sol[i] - round(sol[i])), 0.0,
                                           msg = msg)
    # -- end function

    def test_minimize_rbf(self):
        """Check solution of RBF minimization problem.

        This function verifies that the solution of the RBF
        minimization problem on a small test istance is close to one
        of two pre-computed solution, for all algorithms. It also
        checks that integer variables are integer valued.

        """
        solutions = {'Gutmann' : [[0.0, 1.0, 2.0], [10.0, 1.0, 2.0]],
                     'MSRSM' : [[0.0, 1.0, 2.0], [10.0, 1.0, 2.0]]}
        for algorithm in RbfSettings._allowed_algorithm:
            self.settings.algorithm = algorithm
            references = solutions[algorithm]
            sol = aux.minimize_rbf(self.settings, self.n, self.k,
                                   self.var_lower, self.var_upper,
                                   self.integer_vars, self.node_pos,
                                   self.rbf_lambda, self.rbf_h,)
            val = ru.evaluate_rbf(self.settings, sol, self.n, self.k, 
                                  self.node_pos, self.rbf_lambda,
                                  self.rbf_h)
            found_solution = False
            for ref in references:
                satisfied = True
                for i in range(self.n):
                    tolerance = 1.0e-3
                    lb = ref[i] - tolerance
                    ub = ref[i] + tolerance
                    if (lb > sol[i] or ub < sol[i]):
                        satisfied = False
                if satisfied:
                    found_solution = True
            self.assertTrue(found_solution, 
                            msg = 'The minimize_rbf solution' +
                            ' with algorithm {:s}'.format(algorithm) +
                            ' does not match any known local optimum')
            for i in self.integer_vars:
                msg = ('Variable {:d} not integer in solution'.format(i)
                       + ' alg {:s} '.format(algorithm))
                self.assertAlmostEqual(abs(sol[i] - round(sol[i])), 0.0,
                                       msg = msg)
    # -- end function

    def test_global_search(self):
        """Check solution of global search problem.

        This function verifies that the solution of the global search
        problem on a small test istance is relatively close to a
        pre-computed solution, for all algorithms. Relatively close
        here has a loose meaning because we cannot account for machine
        precision or random numbers that could cause the instance to
        give a very different solution. It also checks that integer
        variables are integer valued.
        """
        solutions = {'Gutmann' : [2.433653775898717, 4.0, 5.288279914554452],
                     'MSRSM' : [9.6569123529739933, 1, 2.0364710264329515]}
        target_val = -0.1
        dist_weight = 0.5
        for algorithm in RbfSettings._allowed_algorithm:
            for method in RbfSettings._allowed_global_search_method:
                self.settings.algorithm = algorithm
                self.settings.global_search_method = method
                ref = solutions[algorithm]
                sol = aux.global_search(self.settings, self.n, self.k,
                                        self.var_lower, self.var_upper,
                                        self.integer_vars, self.node_pos, 
                                        self.rbf_lambda, self.rbf_h, 
                                        self.Amat, target_val, dist_weight)
                for i in range(self.n):
                    tolerance = (self.var_upper[i] - self.var_lower[i])*0.2
                    lb = ref[i] - tolerance
                    ub = ref[i] + tolerance
                    msg_lb = ('Lb not satisfied on var {:d}: '.format(i) +
                              'lb {:f} solution {:f} '.format(lb, sol[i]) +
                              'alg {:s} '.format(algorithm) +
                              'method {:s} '.format(method)) 
                    msg_ub = ('Ub not satisfied on var {:d}: '.format(i) +
                              'ub {:f} solution {:f} '.format(ub, sol[i]) +
                              'alg {:s} '.format(algorithm) +
                              'method {:s} '.format(method))
                    self.assertLessEqual(lb, sol[i], msg = msg_lb)
                    self.assertLessEqual(sol[i], ub, msg = msg_ub)
                for i in self.integer_vars:
                    msg = ('Variable {:d} not integer in solution'.format(i)
                           + ' alg {:s} '.format(algorithm) +
                           'method {:s}'.format(method))
                    self.assertAlmostEqual(abs(sol[i] - round(sol[i])), 0.0,
                                           msg = msg)
    # -- end function

    def test_get_noisy_rbf_coefficients(self):
        """Check solution of noisy RBF coefficients problem.

        This function verifies that the solution of the convex problem
        that computes the RBF coefficients for a noisy interpolant on
        a small test istance satisfies the (noisy) interpolation
        conditions.
        """
        ref = [0.0]
        fast_node_index = [2, 3, 4]
        fast_node_err_bounds = [(-1.0, 1.0), (-1.0, 1.0), (-1.0, 1.0)]
        (l, h) = aux.get_noisy_rbf_coefficients(self.settings, self.n, self.k, 
                                                self.Amat[:self.k, :self.k],
                                                self.Amat[:self.k, self.k:],
                                                self.node_val,
                                                fast_node_index, 
                                                fast_node_err_bounds,
                                                self.rbf_lambda, self.rbf_h)
        # Verify interpolation conditions for noisy nodes
        for (i, j) in enumerate(fast_node_index):
            val = ru.evaluate_rbf(self.settings, self.node_pos[j],
                                  self.n, self.k, self.node_pos, l, h)
            lb = self.node_val[j] + fast_node_err_bounds[i][0]
            ub = self.node_val[j] + fast_node_err_bounds[i][1]
            self.assertLessEqual(lb, val, msg = 'Node value outside bounds')
            self.assertGreaterEqual(ub, val, msg = 'Node value outside bounds')
        # Verify interpolation conditions for regular (exact) nodes
        for i in range(self.k):
            if i in fast_node_index:
                continue
            val = ru.evaluate_rbf(self.settings, self.node_pos[j],
                                  self.n, self.k, self.node_pos, l, h)
            self.assertAlmostEqual(self.node_val[j], val,
                                   msg = 'Node value does not match')
    # -- end function

    def test_generate_sample_points(self):
        """Verify that sample points are inside the box and integer.

        Additionally test some limit cases.
        """

        samples = aux.generate_sample_points(self.settings, self.n, 
                                             self.var_lower, self.var_upper,
                                             self.integer_vars, 123)
        self.assertEqual(len(samples), 123,
                         msg = 'Wrong number of sample points')
        for sample in samples:
            self.assertEqual(len(sample), self.n, msg = 'Wrong point length')
            for i in self.integer_vars:
                msg = 'Variable {:d} not integer in sample'.format(i)
                self.assertAlmostEqual(abs(sample[i] - round(sample[i])),
                                       0.0, msg = msg)
        # Now test some limit cases
        samples = aux.generate_sample_points(self.settings, 0, [], [], 
                                             [], 45)
        self.assertListEqual(samples, [[] for i in range(45)],
                             msg = 'Samples are not empty when n = 0')
        samples = aux.generate_sample_points(self.settings, self.n, 
                                             self.var_lower, self.var_upper,
                                             self.integer_vars, 0)
        self.assertFalse(samples, msg = 'List of samples should be empty')
    # -- end function

    def test_ga_optimize(self):
        """Verify that the genetic algorithm can solve simple problems.
        """
        var_lower = [-1] * 3
        var_upper = [1] * 3
        settings = RbfSettings(ga_base_population_size = 100)
        point = aux.ga_optimize(settings, 3, var_lower, var_upper,
                                [], quadratic)
        self.assertLessEqual(quadratic([point])[0], 0.05,
                             msg = 'Could not solve quadratic with GA')
        point = aux.ga_optimize(settings, 3, var_lower, var_upper,
                                [], shifted_quadratic)
        self.assertLessEqual(shifted_quadratic([point])[0], 0.05,
                             msg = 'Could not solve shifted quadratic with GA')
    # -- end function

# - end class

if (__name__ == '__main__'):
    unittest.main()
