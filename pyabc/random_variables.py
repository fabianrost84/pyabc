import logging
from abc import ABC, abstractmethod
from functools import reduce
from typing import Union
from .parameters import Parameter, ParameterStructure
rv_logger = logging.getLogger("RV")


class RVBase(ABC):
    """
    Random variable abstract base class.

    .. note::

        Why introduce another random variable class and not just use
        the one's provided in
        ``scipy.stats``?

        This funny construction is done because ``scipy.stats``
        distributions are not pickleable.
        This class is really a very thin wrapper around ``scipy.stats``
        distributions to make them pickleable.
        It is important to be able to pickle them to execute the ACBSMC
        algorithm in a distributed cluster
        environment
    """

    @abstractmethod
    def copy(self) -> "RVBase":
        """
        Copy the random variable.

        Returns
        -------
        copied_rv: RVBase
            A copy of the random variable.
        """

    @abstractmethod
    def rvs(self, *args, **kwargs) -> float:
        """
        Sample from the RV.

        Returns
        -------

        sample: float
            A sample from the random variable.
        """

    @abstractmethod
    def pmf(self, x, *args, **kwargs) -> float:
        """
        Probability mass function

        Parameters
        ----------

        x: int
            Probability mass at ``x``.

        Returns
        -------

        mass: float
            The mass at ``x``.
        """

    @abstractmethod
    def pdf(self, x: float, *args, **kwargs) -> float:
        """
        Probability density function

        Parameters
        ----------
        x: float
            Probability density at x.

        Returns
        -------

        density: float
            Probability density at x.
        """

    @abstractmethod
    def cdf(self, x: float, *args, **kwargs) -> float:
        """
        Cumulative distribution function.

        Parameters
        ----------
        x: float
            Cumulative distribution function at x.

        Returns
        -------

        density: float
            Cumulative distribution function at x.
        """


class RV(RVBase):
    """
    Concrete random variable.

    Parameters
    ----------

    name: str
        Name of the distribution as in ``scipy.stats``

    args:
        Arguments as in ``scipy.stats`` matching the distribution
        with name "name".

    kwargs:
        Keyword arguments as in s``cipy.stats``
        matching the distribution with name "name".
    """
    @staticmethod
    def from_dictionary(dictionary: dict) -> "RV":
        """
        Construct random variable from dictionary.

        Parameters
        ----------

        dictionary: dict
            A dictionary with the keys

               * "name" (mandatory)
               * "args" (optional)
               * "kwargs" (optional)

            as in scipy.stats.



        .. note::

            Either the "args" or the "kwargs" key has to be present.
        """
        return RV(dictionary['type'], *dictionary.get('args', []),
                  **dictionary.get('kwargs', {}))

    def __init__(self, name: str, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.distribution = None
        "the scipy.stats. ... distribution object"
        self.__setstate__(self.__getstate__())

    def __getattr__(self, item):
        return getattr(self.distribution, item)

    def __getstate__(self):
        return self.name, self.args, self.kwargs

    def __setstate__(self, state):
        self.name = state[0]
        self.args = state[1]
        self.kwargs = state[2]
        import scipy.stats as st
        distribution = getattr(st, self.name)
        self.distribution = distribution(*self.args, **self.kwargs)

    def copy(self):
        return RV(self.name, *self.args, **self.kwargs)

    def rvs(self, *args, **kwargs):
        return self.distribution.rvs(*args, **kwargs)

    def pmf(self, x, *args, **kwargs):
        return self.distribution.pmf(x, *args, **kwargs)

    def pdf(self, x, *args, **kwargs):
        return self.distribution.pdf(x, *args, **kwargs)

    def cdf(self, x, *args, **kwargs):
        return self.distribution.cdf(x, *args, **kwargs)

    def __repr__(self):
        return ("<RV(name={name}, args={args} kwargs={kwargs})>"
                .format(name=self.name, args=self.args, kwargs=self.kwargs))


class RVDecorator(RVBase):
    """
    Random variable decorater base class.

    Implement a decorator pattern.

    Further decorators should derive from this class.

    It stores the decorated random variable in ``self.component``

    Overwrite the method ``decorator_repr`` the represent the decorator type.
    The decorated variable will then be automatically included in
    the call to ``__repr__``.

    Parameters
    ----------

    component: RVBase
        The random variable to be decorated.
    """
    def __init__(self, component: RVBase):
        self.component = component  #: The decorated random variable

    def rvs(self, *args, **kwargs):
        return self.component.rvs(*args, **kwargs)

    def pmf(self, x, *args, **kwargs):
        return self.component.pmf(x, *args, **kwargs)

    def pdf(self, x, *args, **kwargs):
        return self.component.pdf(x, *args, **kwargs)

    def cdf(self, x, *args, **kwargs):
        return self.component.cdf(x, *args, **kwargs)

    def copy(self):
        return self.__class__(self.component.copy())

    def decorator_repr(self) -> str:
        """
        Represent the decorator itself.

        Template method.

        The ``__repr__`` method used ``decorator_repr`` and the
        ``__repr__`` of the
        decorated RV to build a combined representation.

        Returns
        -------

        decorator_repr: str
            A string representing the decorator only.
        """
        return "Decorator"

    def __repr__(self):
        return ("[{decorator_repr}]"
                .format(decorator_repr=self.decorator_repr())
                + self.component.__repr__())


class LowerBoundDecorator(RVDecorator):
    """
    Impose a strict lower bound on a random variable.
    Condition RV X to X > lower bound.
    In particular P(X = lower_bound) = 0.

    .. note::

        Sampling is done via rejection. Up to 10000 samples are taken
        from the decorated RV.
        The first sample within the permitted range is then taken.
        Otherwise None is returned.

    Parameters
    ----------

    component: RV
        The decorated random variable.

    lower_bound: float
        The lower bound.
    """
    MAX_TRIES = 10000

    def __init__(self, component: RV, lower_bound: float):
        if component.cdf(lower_bound) == 1:
            raise Exception(
                "LowerBoundDecorator: Conditioning on a set of measure zero.")
        self.lower_bound = lower_bound
        super(LowerBoundDecorator, self).__init__(component)

    def copy(self):
        return self.__class__(self.component.copy(), self.lower_bound)

    def decorator_repr(self):
        return "Lower: X > {lower:2f}".format(lower=self.lower_bound)

    def rvs(self):
        for _ in range(LowerBoundDecorator.MAX_TRIES):
            sample = self.component.rvs()
            # not sure whether > is the exact opposite. but <= is consistent
            if not (sample <= self.lower_bound):
                return sample  # with the other functions
        return None

    def pdf(self, x):
        if x <= self.lower_bound:
            return 0.
        return (self.component.pdf(x)
                / (1 - self.component.cdf(self.lower_bound)))

    def pmf(self, x):
        if x <= self.lower_bound:
            return 0.
        return (self.component.pmf(x)
                / (1 - self.component.cdf(self.lower_bound)))

    def cdf(self, x):
        if x <= self.lower_bound:
            return 0.
        lower_mass = self.component.cdf(self.lower_bound)
        return (self.component.cdf(x) - lower_mass) / (1 - lower_mass)


class Distribution(ParameterStructure):
    """
    Distribution of parameters for a model.

    A distribution is a collection of RVs and/or distributions.
    Essentially something like a dictionary
    of random variables or distributions.

    This should be used as prior and also as Kernel density.
    """
    def __repr__(self):
        return "<Distribution {keys}>".format(
            keys=str(list(self.get_parameter_names()))[1:-1])

    @staticmethod
    def from_dictionary_of_dictionaries(dict_of_dicts: dict) -> "Distribution":
        """
        Create distribution from dictionary of dictionaries

        Parameters
        ----------
        dict_of_dicts: dict
            The keys of the dict indicate the parameters names.
            The values are itself dictionaries representing scipy.stats
            distribution. I.e. the have the key "name" and at least one
            of the keys "args" or "kwargs".

        Returns
        -------

        distribution: Distribution
            Created distribution.
        """
        rv_dictionary = {}
        for key, value in dict_of_dicts.items():
            rv_dictionary[key] = RV.from_dictionary(value)
        return Distribution(rv_dictionary)

    def copy(self) -> "Distribution":
        """
        Copy the distribution

        Returns
        -------

        copied_distribution: Distribution
            A copy of the distribution.
        """
        return Distribution(**{key: value.copy()
                               for key, value in self.items()})

    def update_random_variables(self, **random_variables):
        """
        Update random variables within the distribution

        Parameters
        ----------

        **random_variables:
            keywords are the parameters' names, the values are random variable.

        """
        self.update(random_variables)

    def get_parameter_names(self) -> list:
        """
        Sorted list of parameter names.

        Returns
        -------

        sorted_names: list
            Sorted list of parameter names.
        """
        return sorted(self.keys())

    def rvs(self) -> Parameter:
        """
        Sample from joint distribution

        Returns
        -------

        parameter: Parameter
            A parameter which was sampled.
        """
        return Parameter(**{key: val.rvs() for key, val in self.items()})

    def pdf(self, x: Union[Parameter, dict]):
        """
        Get combination of probability density function (for continuous
        variables) and
        probability mass function (for discrete variables) at point x

        Parameters
        ----------
        x : Union[Parameter, dict]
            Evaluate at the given Parameter ``x``.
        """
        # check if the parameters match
        if sorted(x.keys()) != sorted(self.keys()):
            raise Exception("Random variable parameter mismatch. Expected: " +
                            str(sorted(self.keys())) +
                            " got " + str(sorted(x.keys())))
        if len(self) > 0:
            res = []
            for key, val in x.items():
                try:
                    # works for continuous variables
                    res.append(self[key].pdf(val))
                except AttributeError:
                    # discrete variables do not have a pdf but a pmf
                    res.append(self[key].pmf(val))
            return reduce(lambda s, t: s*t, res)
        else:
            return 1


class Kernel:
    """
    A Kernel of the form K(x,y) = K(x-y).

    Can be initialized from a distribution or using individual variables.
    E.g. do ``Kernel(distribution)`` or
    ``Kernel(par_name_1=rv1, par_name2=rv2)``

    If X is a given RV with pdf f, then K(x,y) = f(x-y).
    """
    def __init__(self, *distribution, **random_variables):
        if not ((bool(len(distribution)) != bool(len(random_variables))) or
                (len(distribution) == len(random_variables) == 0)):
            raise Exception(
                "Give single argument XOR keyword arguments. Never both.")
        elif len(distribution) == 1:  # parameter is a Distribution object
            self.distribution = distribution[0]
        else:  # parameter is a dictionary
            self.distribution = Distribution(**random_variables)

    def add_random_variables(self, **random_variables):
        """
        Add random variables to kernel

        Parameters
        ----------
        random_variables: keyword arguments
            Keys are the names, values the random variables
        """
        self.distribution.update_random_variables(**random_variables)

    def get_parameter_names(self):
        return self.distribution.get_parameter_names()

    def rvs(self, theta):
        """
        Return sample form :math:`K( \\dot, theta)`
        """
        return self.distribution.rvs() + theta

    def pdf(self, x, y):
        """
        Return density :math:`K(x,y)`
        I.e probability of getting form y to x.
        """
        return self.distribution.pdf(x-y)


class ModelPerturbationKernel:
    """
    Model perturbation kernel.

    Parameters
    ----------

    nr_of_models: int
        Number of models

    probability_to_stay:  Union[float, None]
        If ``None``, probability to stay is set to 1/nr_of_models.
        Otherwise, the supplied value is used.
    """
    def __init__(self, nr_of_models: int,
                 probability_to_stay: Union[float, None]=None):
        self.nr_of_models = nr_of_models
        if nr_of_models == 1:
            self.probability_to_stay = 1
        else:
            if probability_to_stay is None:
                self.probability_to_stay = 1 / nr_of_models
            else:
                self.probability_to_stay = min(
                    max(probability_to_stay, 0), 1)

    def _get_discrete_rv(self, m):
        p_stay = self.probability_to_stay
        p_move = (1 - p_stay) / (self.nr_of_models-1)
        probabilities = [p_stay if n == m else p_move
                         for n in range(self.nr_of_models)]
        return RV('rv_discrete',
                  values=(range(len(probabilities)), probabilities))

    def rvs(self, m: int) -> int:
        """
        Sample a Kernel jump from model ``m`` to another model.

        Parameters
        ----------
        m: int
            Model source nr.

        Returns
        -------

        target: int
            Target model nr.
        """
        if not 0 <= m <= self.nr_of_models-1:
            raise Exception('m has to be between 0 and nr_of_models - 1')
        if self.nr_of_models == 1:
            return 0  # always stay, no other choice
        else:
            return self._get_discrete_rv(m).rvs()

    def pmf(self, n: int, m: int) -> float:
        """

        Parameters
        ----------
        n: int
            Model target nr.

        m: int
            Model source nr.

        Returns
        -------

        probability: float
            Probability with which to jump from ``m`` to ``n``.
        """
        if not (0 <= n <= self.nr_of_models
                and 0 <= m <= self.nr_of_models-1):
            raise Exception(
                'n and m have to be between 0 and nr_of_models - 1')
        if self.nr_of_models == 1:
            return 1 if n == m else 0
        else:
            return self._get_discrete_rv(m).pmf(n)
