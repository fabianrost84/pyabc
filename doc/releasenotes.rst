Release Notes
=============

0.6 series
..........


0.6.4
-----

Performance improvement. Use MulticoreEvalParallelSampler as default. This
should bring better performance for machines with many cores and comparatively
small population sizes.

0.6.3
-----

Bug fix. Ensure numpy.int64 can also be passed to History methods were an
integer argument is expected.


0.6.2
-----

Bug fix. Forgot to add the new Multicore base class.


0.6.1
-----

MulticoreEvalParallelSampler gets an n_procs parameter.


0.6.0
-----

History API
~~~~~~~~~~~

Change the signature from History.get_distribution(t, m)
to History.get_distribution(m, t) and make the time argument optional
defaulting to the last time point


0.5 series
..........


0.5.2
-----

* Minor History API changes
    * Remove History.get_results_distribution
    * rename History.get_weighted_particles_dataframe to
      History.get_distribution


0.5.1
-----

* Minor ABCSMC API changes
    * Mark the de facto private methods as private by prepending an
      underscore. This should not cause trouble as usually noone would
      ever use these methods.


0.5.0
-----

* Usability improvements and minor API canges
    * ABCSMC accepts now an integer to be passed for constant population size
    * The maximum number populations specification has moved from the
      PopulationStrategy classes to the ABCSMC.run method. The ABCSMC.run
      method will be where it is defined when to stop.


0.4 series
..........


0.4.4
-----

* Improvements to adaptive population size strategy
   * Use same CV estimation algorithm for Transition and PopulationStrategy
   * Bootstrapping on full joint space for model selection


0.4.3
-----

* Fix edge case of models without parameters for population size adaptation


0.4.2
-----

* Changes to the experimental adaptive population strategy.
   * Smarter update for model selection
   * Better CV estimation



0.4.1
-----

* fix minor bug in RVs wrapper. args and keyword args were not passed to the
  wrapper random variable.


0.4.0
-----

* Add local transition class which makes a local KDE fit.
* Fix corner cases of adaptive population size strategy
* Change the default: Do not stop if only a single model is alive.
* Also include population 0, i.e. a sample from the prior, in the websever
  visualization
* Minor bug fixes
    * Fix inconsistency in ABC options if db_path given as sole string argument
* Add four evaluation parallel samplers
    * Dask based implementation
        * More communication overhead
    * Future executor evaluation parallel sampler
        * Very similar to the Dask implementation
    * Redis based implementation
        * Less communication overhad
        * Performs also well for short running simulations
    * Multicore evaluation parallel sampler
        * In most common cases, where the population size is much bigger
          than the number of cores, this sampler is not going to be faster
          than the multicore particle parallel sampler.
        * However, on machines with lots of cores and moderate sized populations
          this sampler might be faster


0.3 series
..........

0.3.3
-----

* Fix SGE regression. Forgot to update a module path on refactoring.


0.3.2
-----

PEP8
~~~~

Comply with PEP8 with a few exceptions where it does not make sense.
Flake8 runs now with the test. The tests do not pass if flake8 complains.


Legacy code cleanup
~~~~~~~~~~~~~~~~~~~

Remove legacy classes such as the MultivariateMultiTypeNormalDistributions
and the legacy covariance calculation. Also remove devideas folder.


0.3.1
-----

Easier usage
~~~~~~~~~~~~

Refactor the ABCSMC.set_data and provide defaults.


0.3.0
-----

Easier usage
~~~~~~~~~~~~

Provide more default values for ABCSMC. This improves usability.


0.2 series
..........

0.2.0
-----

Add an efficient multicore sampler
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The new sampler relies on forking instead of pickling for the ``sample_one``,
``simulate_one`` and ``accept_one`` functions.
This brings a huge performance improvement for single machine multicore settings
compared to ``multiprocessing.Pool.map`` like execution which repeatedly pickles.


0.1 series
..........

0.1.3
-----

Initial release to the public.
