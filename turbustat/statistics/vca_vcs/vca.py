# Licensed under an MIT open source license - see LICENSE


import numpy as np
import warnings
from numpy.fft import fftshift

from ..rfft_to_fft import rfft_to_fft
from slice_thickness import change_slice_thickness
from ..base_pspec2 import StatisticBase_PSpec2D


class VCA(StatisticBase_PSpec2D):

    '''
    The VCA technique (Lazarian & Pogosyan, 2004).

    Parameters
    ----------
    cube : numpy.ndarray
        Data cube.
    header : FITS header
        Corresponding FITS header.
    slice_sizes : float or int, optional
        Slices to degrade the cube to.
    phys_units : bool, optional
        Sets whether physical scales can be used.
    '''

    def __init__(self, cube, header, slice_size=None, phys_units=False):
        super(VCA, self).__init__()

        self.cube = cube.astype("float64")
        if np.isnan(self.cube).any():
            self.cube[np.isnan(self.cube)] = 0
        self.header = header
        self.shape = self.cube.shape

        if slice_size is None:
            self.slice_size = 1.0

        if slice_size != 1.0:
            self.cube = \
                change_slice_thickness(self.cube.copy(),
                                       slice_thickness=self.slice_size)

        self.phys_units_flag = False
        if phys_units:
            self.phys_units_flag = True

        self._ps1D_stddev = None

    def compute_pspec(self):
        '''
        Compute the 2D power spectrum.
        '''

        vca_fft = fftshift(rfft_to_fft(self.cube))

        self._ps2D = np.power(vca_fft, 2.).sum(axis=0)

        return self

    def run(self, verbose=False, brk=None, return_stddev=True,
            logspacing=True):
        '''
        Full computation of VCA.

        Parameters
        ----------
        verbose : bool, optional
            Enables plotting.
        brk : float, optional
            Initial guess for the break point.
        return_stddev : bool, optional
            Return the standard deviation in the 1D bins.
        logspacing : bool, optional
            Return logarithmically spaced bins for the lags.
        '''

        self.compute_pspec()
        self.compute_radial_pspec(return_stddev=return_stddev)
        self.fit_pspec(brk=brk)

        if verbose:

            print self.fit.summary()

            self.plot_fit(show=True, show_2D=True)

        return self


class VCA_Distance(object):

    '''
    Calculate the distance between two cubes using VCA. The 1D power spectrum
    is modeled by a linear model. The distance is the t-statistic of the
    interaction between the two slopes.

    Parameters
    ----------
    cube1 : FITS hdu
        Data cube.
    cube2 : FITS hdu
        Data cube.
    slice_size : float, optional
        Slice to degrade the cube to.
    breaks : float, list or array, optional
        Specify where the break point is. If None, attempts to find using
        spline. If not specified, no break point will be used.
    fiducial_model : VCA
        Computed VCA object. use to avoid recomputing.
    '''

    def __init__(self, cube1, cube2, slice_size=1.0, breaks=None,
                 fiducial_model=None):
        super(VCA_Distance, self).__init__()
        cube1, header1 = cube1
        cube2, header2 = cube2
        self.shape1 = cube1.shape[1:]  # Shape of the plane
        self.shape2 = cube2.shape[1:]

        assert isinstance(slice_size, float)

        if not isinstance(breaks, list) or not isinstance(breaks, np.ndarray):
            breaks = [breaks] * 2

        if fiducial_model is not None:
            self.vca1 = fiducial_model
        else:
            self.vca1 = \
                VCA(cube1, header1, slice_size=slice_size).run(brk=breaks[0])

        self.vca2 = \
            VCA(cube2, header2, slice_size=slice_size).run(brk=breaks[1])

    def distance_metric(self, labels=None, verbose=False):
        '''

        Implements the distance metric for 2 VCA transforms, each with the
        same channel width. We fit the linear portion of the transform to
        represent the powerlaw.

        Parameters
        ----------
        labels : list, optional
            Contains names of datacubes given in order.
        verbose : bool, optional
            Enables plotting.
        '''

        # Construct t-statistic
        self.distance = \
            np.abs((self.vca1.slope - self.vca2.slope) /
                   np.sqrt(self.vca1.slope_err**2 +
                           self.vca2.slope_err**2))

        if verbose:
            if labels is None:
                labels = ['1', '2']

            print "Fit to %s" % (labels[0])
            print self.vca1.fit.summary()
            print "Fit to %s" % (labels[1])
            print self.vca2.fit.summary()

            import matplotlib.pyplot as p
            self.vca1.plot_fit(show=False, color='b', label=labels[0])
            self.vca2.plot_fit(show=False, color='r', label=labels[1])
            p.legend(loc='best')
            p.show()

        return self
