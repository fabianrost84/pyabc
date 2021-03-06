from distributed import Client
from .base import Sampler
from .eps_sampling_function import sample_until_n_accepted_proto, \
    full_submit_function_pickle
import numpy as np


class DaskDistributedSampler(Sampler):
    """
    Parallelize with dask. This sampler is intended to be used with a pre-con-
    figured dask client, but is able to initialize client, scheduler and
    workers on its own on the local machine for testing/debugging purposes.

    Parameters
    ----------

    dask_client: dask.Client, optional
        The configured dask Client.
        If none is provided, then a local dask distributed Cluster is created.

    client_max_jobs:
        Maximum number of jobs that can submitted to the client at a time.
        If this value is smaller than the maximum number of cores provided by
        the distributed infrastructure, the infrastructure will not be utilized
        fully.

    default_pickle:
        Specify if the sampler uses pythons default pickle function to
        communicate the submit function to python; if this is the case, a
        cloud-pickle based workaround is used to pickle the simulate and
        evaluate functions. This allows utilization of locally defined
        functions, which can not be pickled using default pickle, at the cost
        of an additional pickling overhead. For dask, this workaround should
        not be necessary and it should be save to use default_pickle=false

    batchsize: int, optional
        Number of parameter samples that are evaluated in one remote execution
        call. Batchsubmission can be used to reduce the communication overhead
        for fast (ms-s) model evaluations. Large batchsizes can result in un-
        necessary model evaluations. By default, batchsize=1, i.e. no batching
        is done

    """
    sample_until_n_accepted = sample_until_n_accepted_proto
    full_submit_function_pickle = full_submit_function_pickle

    def __init__(self, dask_client=None, client_max_jobs=np.inf,
                 default_pickle=False, batchsize=1):
        super().__init__()
        self.nr_evaluations_ = 0

        # Assign Client
        if dask_client is None:
            dask_client = Client()
        self.my_client = dask_client

        # Client options
        self.client_max_jobs = client_max_jobs

        # Job state
        self.jobs_queued = 0

        # For dask, we use cloudpickle by default
        self.default_pickle = default_pickle

        # Batchsize
        self.batchsize = batchsize

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['my_client']
        return d

    def client_cores(self):
        return sum(self.my_client.ncores().values())
