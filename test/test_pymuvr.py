import unittest
import random
import os
import numpy as np

import pymuvr

# check if spykeutils is available. As a special case needed for
# Travis, pretend it's not available in any case if the
# without_spykeutils environment variable is set and is not an empty
# string.
try:
    import quantities as pq
    import spykeutils.spike_train_generation as stg
    import spykeutils.spike_train_metrics as stm
    SPYKEUTILS_IS_AVAILABLE = not bool(os.environ['without_spykeutils'])
except ImportError:
    SPYKEUTILS_IS_AVAILABLE = False
except KeyError:
    SPYKEUTILS_IS_AVAILABLE = True
    

def simple_train(mean_isi, max_duration):
    train = []
    last_spike = 0
    while last_spike < max_duration:
        delta = random.uniform(0, 2*mean_isi)
        last_spike += delta
        train.append(last_spike)
    return train


class TestTrivialTrains(unittest.TestCase):
    def setUp(self):
        self.tau = 0.012
        self.cos = 0.5

    def test_empty_spike_trains(self):
        observations = [[[]], [[]]]
        d_rectangular = pymuvr.distance_matrix(observations,
                                               observations,
                                               self.cos, self.tau)
        np.testing.assert_array_equal(d_rectangular,
                                      np.zeros_like(d_rectangular))

    def test_identical_trains(self):
        observations = [[[1.,2.],[1.5]], [[1.,2.],[1.5]]]
        d_rectangular = pymuvr.distance_matrix(observations,
                                               observations,
                                               self.cos, self.tau)
        np.testing.assert_array_equal(d_rectangular,
                                      np.zeros_like(d_rectangular))

    def test_missing_spike(self):
        observations = [[[1.,2.]], [[1.]]]
        d_rectangular = pymuvr.distance_matrix(observations,
                                               observations,
                                               self.cos, self.tau)
        np.testing.assert_array_almost_equal(d_rectangular,
                                             np.array([[0,1],[1,0]]))
        

class TestRandomTrains(unittest.TestCase):
    def setUp(self):
        n_observations = 10
        n_cells = 100
        mean_isi = 0.03
        max_duration = 2
        self.tau = 0.012
        self.cos = 0.5
        self.observations = [[simple_train(mean_isi, max_duration) for c in range(n_cells)] for o in range(n_observations)]
        # observation 1 is identical to observation 0 for all the cells.
        self.observations[0] = self.observations[1][:]

    def test_square_distance_matrix(self):
        d = pymuvr.square_distance_matrix(self.observations, self.cos, self.tau)
        self.assertEqual(d.shape, (len(self.observations), len(self.observations)))

    def test_distance_matrix(self):
        d = pymuvr.distance_matrix(self.observations[:3],
                                   self.observations[3:],
                                   self.cos,
                                   self.tau)
        self.assertEqual(d.shape, (3, len(self.observations)-3))

    def test_compare_square_and_rectangular(self):
        d_rectangular = pymuvr.distance_matrix(self.observations,
                                               self.observations,
                                               self.cos,
                                               self.tau)
        d_square = pymuvr.square_distance_matrix(self.observations,
                                                 self.cos,
                                                 self.tau)

        np.testing.assert_array_almost_equal(d_rectangular, d_square)

    def test_empty_spike_train(self):
        observations = [o[:] for o in self.observations]
        observations[0][0] = []
        d_rectangular = pymuvr.distance_matrix(observations[:3],
                                               observations[3:],
                                               self.cos, self.tau)

@unittest.skipIf(not SPYKEUTILS_IS_AVAILABLE,
                 "can't import spykeutils")
class TestCompareWithSpykeutils(unittest.TestCase):
    def setUp(self):
        self.n_observations = 10
        self.n_cells = 20
        self.rate = 30
        self.tstop = 2
        self.cos = np.linspace(0, 1, 5)
        self.tau = np.linspace(0.006, 0.018, 3)
        self.sutils_units = {}
        self.pymuvr_observations = []
        for unit in range(self.n_cells):
            self.sutils_units[unit] = []
            for ob in range(self.n_observations):
                self.sutils_units[unit].append(stg.gen_homogeneous_poisson(self.rate * pq.Hz, t_stop=self.tstop * pq.s))
        # observation 1 is identical to observation 0 for all the cells.
        for unit in range(self.n_cells):
            self.sutils_units[unit][1] = self.sutils_units[unit][0]
        for ob in range(self.n_observations):
            self.pymuvr_observations.append([])
            for unit in range(self.n_cells):
                self.pymuvr_observations[ob].append(self.sutils_units[unit][ob].tolist())
        
    def test_compare_with_spykeutils(self):
        for cos in self.cos:
            for tau in self.tau:
                sutils_d = stm.van_rossum_multiunit_dist(self.sutils_units,
                                                         weighting=cos,
                                                         tau=tau)
                pymuvr_d = pymuvr.square_distance_matrix(self.pymuvr_observations,
                                                         cos,
                                                         tau)
                np.testing.assert_array_almost_equal(sutils_d, pymuvr_d)

if __name__ == "__main__":
    unittest.main(verbosity=2)