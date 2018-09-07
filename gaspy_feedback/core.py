'''
This submodule contains various Luigi tasks that are meant to be
used continuously/automatically to perform active machine
learning/surrogate based optimization.
'''

__author__ = 'Kevin Tran'
__email__ = 'ktran@andrew.cmu.edu'

import numpy as np
from scipy.stats import norm
import luigi
from gaspy import defaults
from gaspy.gasdb import get_low_coverage_docs_by_surface
from gaspy.tasks.core import FingerprintRelaxedAdslab
from gaspy.tasks.submit_calculations.adsorption_calculations import _make_adslab_parameters_from_doc

DEFAULT_ENCUT = defaults.ENCUT
DEFAULT_XC = defaults.XC
DEFAULT_MAX_BULK_SIZE = defaults.MAX_NUM_BULK_ATOMS
DEFAULT_MAX_ROCKETS = 50


class BestLowCoverageSitesWithGaussianNoise(luigi.WrapperTask):
    '''
    This task will create FireWorks rockets (i.e., submit calculations)
    for various adsorption sites. We choose only sites that we predict
    to have the lowest adsorption energy on their respective surfaces
    (which are therefore the "low coverage" sites) as per both DFT
    and surrogate models. We also choose a subset of these low-coverage
    sites using Gaussian noise that is centered at the target and
    with a specified standard deviation.

    Luigi args:
        adsorbates      A list of strings of the [co]adsorbates that you want to make
                        FireWorks/calculations for. Note that this task does not
                        iterate through the adsorbates in this list; it assumes that
                        the adsorbates in this list are coadsorbates.
        energy_target   A float indicating the adsorption energy that you're trying to target
                        with the adsorptions you're making rockets for
        model_tag       A string indicating which surrogate model you want to use
                        when estimating what you think the adsorption energy is going
                        to be.
        stdev           A float indicating the standard deviation of the Gaussian
                        noise you want to add to the selection.
        xc              A string indicating the cross-correlational you want to use.
        encut           A float indicating the energy cutoff you want to be used for
                        the corresponding bulk relaxation.
        max_bulk_atoms  A positive integer indicating the maximum number of atoms you want
                        in the bulk relaxation.
        max_rockets     A positive integer indicating the maximum number of sites you want to
                        submit to FireWorks. If the number of possible site/adsorbate
                        combinations is greater than the maximum number of submissions, then
                        submission priority is assigned randomly.
    '''
    adsorbates = luigi.ListParameter()
    energy_target = luigi.IntParameter()
    model_tag = luigi.Parameter()
    stdev = luigi.FloatParameter(0.1)
    xc = luigi.Parameter(DEFAULT_XC)
    encut = luigi.FloatParameter(DEFAULT_ENCUT)
    max_bulk_atoms = luigi.IntParameter(DEFAULT_MAX_BULK_SIZE)
    max_rockets = luigi.IntParameter(DEFAULT_MAX_ROCKETS)

    def requires(self):
        '''
        We use `get_low_coverage_docs_by_surface` to get a dictionary whose keys
        represent various surfaces and whose values are docs---i.e., dictionaries
        that contain various information about the adsorption site that we predict to
        have the lowest adsorption energy (as per both DFT data and the surrogate model).

        Once we have these documents, we use scipy to create a probability density function (pdf)
        centered at our target and with the specified standard deviation. This pdf can then
        be used to quantify the probability of choosing a document based on its distance
        from the target. We then feed these probabilities to np.random.choice to choose
        the documents.
        '''
        # Get the documents and their energies
        docs_by_surface = get_low_coverage_docs_by_surface(self.adsorbates, self.model_tag)
        docs = [doc for doc in docs_by_surface.values() if not doc['DFT_calculated']]
        energies = [doc['energy'] for doc in docs]

        # Choose the documents with Gaussian noise
        gaussian_distribution = norm(loc=self.energy_target, scale=self.stdev)
        probability_densities = [gaussian_distribution.pdf(energy) for energy in energies]
        probabilities = probability_densities/sum(probability_densities)
        docs = np.random.choice(docs, size=self.max_rockets, replace=False, p=probabilities)

        # Now that we have the documents for the sites we want to use,
        # turn them into parameters and tasks
        for doc in docs:
            parameters = _make_adslab_parameters_from_doc(doc, self.adsorbates,
                                                          encut=self.encut,
                                                          xc=self.xc,
                                                          max_atoms=self.max_bulk_atoms)
            task_to_make_rocket = FingerprintRelaxedAdslab(parameters=parameters)
            yield task_to_make_rocket
