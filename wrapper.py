import numpy as np
import sys
import os
from ioh import get_problem

class Py_CMA_ES_Wrapper:
    def __init__(self, func, dim, ub, lb, total_budget, random_seed):
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        bayes_bo_lib = os.path.join(
            my_dir, 'mylib', 'lib_BO_bayesoptim', 'Bayesian-Optimization')
        self.func = func
        self.dim = dim
        self.total_budget = total_budget
        self.random_seed = random_seed
        self.ub = ub
        self.lb = lb

    def run(self):
        from bayes_optim import RandomForest, BO, GaussianProcess
        import cma
        from bayes_optim.extension import RealSpace

        import random
        space = RealSpace([self.lb, self.ub], random_seed=self.random_seed) * self.dim
        ma = float('-inf')
        argmax = None
        for i in range(10*self.dim):
            x = space.sample(1)[0]
        cma.fmin(self.func, x, 1., options={'bounds': [
                 [self.lb]*self.dim, [self.ub]*self.dim], 'maxfevals': self.total_budget, 'seed': self.random_seed})

        def get_acq_time(self):
            return self.opt.acq_opt_time

        def get_mode_time(self):
            return self.opt.mode_fit_time

        def get_iter_time(self):
            return self.opt.cum_iteration_time

class SaasboWrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        sys.path.append(os.path.join(my_dir, 'mylib', 'lib_saasbo'))

        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        #from saasbo import run_saasbo, get_acq_time, get_mode_time
        from saasbo import Saasbo


        # run_saasbo(
        #     self.func,
        #     np.ones(self.dim) * self.ub,
        #     np.ones(self.dim) * self.lb,
        #     self.total_budget,
        #     self.Doe_size,
        #     self.random_seed,
        #     alpha=0.01,
        #     num_warmup=256,
        #     num_samples=256,
        #     thinning=32,
        #     device="cpu",
        # )

        self.opt = Saasbo(func=self.func,
                          dim=self.dim,
                          ub=self.ub,
                          lb=self.lb,
                          total_budget=self.total_budget,
                          DoE_size=self.Doe_size,
                          random_seed=self.random_seed)

        print(self.opt.run_saasbo(self.func,np.ones(self.dim) * self.ub,np.ones(self.dim) * self.lb,self.total_budget,self.Doe_size,self.random_seed,alpha=0.01,num_warmup=256,num_samples=256,thinning=32,device="cpu",))

    def get_acq_time(self):
        return self.opt.acq_opt_time

    def get_mode_time(self):
        return self.opt.mode_fit_time

    def get_iter_time(self):
        return self.opt.cum_iteration_time



class BO_sklearnWrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        sys.path.append(os.path.join(my_dir, 'mylib', 'lib_BO_sklearn'))

        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        from bosklearn import bosklearn

        self.opt= bosklearn(func=self.func,
                          dim=self.dim,
                          ub=self.ub,
                          lb=self.lb,
                          total_budget=self.total_budget,
                          DoE_size=self.Doe_size,
                          random_seed=self.random_seed)
        self.opt.gp_minimize(self.func,  # the function to minimize
                    # the bounds on each dimension of x
                    list((((self.lb, self.ub),) * self.dim)),
                    acq_func="EI",  # the acquisition function
                    n_calls=self.total_budget,  # the number of evaluations of f
                    n_random_starts=self.Doe_size,  # the number of random initialization points
                    noise=0.1 ** 2,  # the noise level (optional)
                    random_state=self.random_seed)

    def get_acq_time(self):
        return self.opt.acq_opt_time

    def get_mode_time(self):
        return self.opt.mode_fit_time

    def get_iter_time(self):
        return self.opt.cum_iteration_time

class BO_bayesoptimWrapper:
    # BO of Hao
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        sys.path.append('./mylib/' + 'lib_' + "BO_bayesoptim")
        print(sys.path)

        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        from bayes_optim import BO, RealSpace
        from bayes_optim.surrogate import GaussianProcess

        space = RealSpace([self.lb, self.ub]) * \
            self.dim  # create the search space

        # hyperparameters of the GPR model
        thetaL = 1e-10 * (self.ub - self.lb) * np.ones(self.dim)
        thetaU = 10 * (self.ub - self.lb) * np.ones(self.dim)
        model = GaussianProcess(  # create the GPR model
            thetaL=thetaL, thetaU=thetaU
        )

        opt = BO(
            search_space=space,
            obj_fun=self.func,
            model=model,
            DoE_size=self.Doe_size,  # number of initial sample points
            max_FEs=self.total_budget,  # maximal function evaluation
            verbose=True
        )
        opt.run()


class BO_development_bayesoptimWrapper:
    # Latest changes from Hao's repository
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        bayes_bo_lib = os.path.join(
            my_dir, 'mylib', 'lib_BO_bayesoptim', 'Bayesian-Optimization')
        if not os.path.isdir(bayes_bo_lib):
            raise ImportError(
                'No such module Bayesian-Optimization, please consider cloning this repository: https://github.com/wangronin/Bayesian-Optimization to the folder mylib/lib_BO_bayesoptim/')
        sys.path.insert(0, bayes_bo_lib)
        print(sys.path)

        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        from bayes_optim.extension import RealSpace
        from bayes_optim.bayes_opt import BO

        space = RealSpace([self.lb, self.ub], random_seed=self.random_seed) * self.dim
        opt = BO(
            search_space=space,
            obj_fun=self.func,
            DoE_size=self.Doe_size,
            n_point=1,
            random_seed=self.random_seed,
            acquisition_optimization={"optimizer": "BFGS"},
            max_FEs=self.total_budget,
            verbose=False,
        )
        opt.run()

class KPCABOWrapper:
     # Latest changes from Hao's repository
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        bayes_bo_lib = os.path.join(
            my_dir, 'mylib', 'lib_BO_bayesoptim', 'Bayesian-Optimization')
        if not os.path.isdir(bayes_bo_lib):
            raise ImportError(
                'No such module Bayesian-Optimization, please unzip the folder Bayesian-Optimization.zip and move the unzip folder to mylib/lib_BO_bayesoptim/')
        sys.path.insert(0, bayes_bo_lib)
        print(sys.path)

        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        

        from bayes_optim import RandomForest, BO, GaussianProcess

        from bayes_optim.extension import PCABO, RealSpace, KernelPCABO, KernelFitStrategy
        from bayes_optim.mylogging import eprintf

        import random   
        

        space = RealSpace([self.lb, self.ub], random_seed=self.random_seed) * self.dim
        self.opt = KernelPCABO(
            search_space=space,
            obj_fun=self.func,
            DoE_size=self.Doe_size,
            max_FEs=self.total_budget,
            verbose=False,
            n_point=1,
            acquisition_optimization={"optimizer": "BFGS"},
            max_information_loss=0.1,
            kernel_fit_strategy=KernelFitStrategy.AUTO,
            NN=self.dim,
            random_seed=self.random_seed
        )

        print(self.opt.run())

    def get_acq_time(self):
        return self.opt.acq_opt_time

    def get_mode_time(self):
        return self.opt.mode_fit_time

    def get_iter_time(self):
        return self.opt.cum_iteration_time


class randomWrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):

        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        import ioh

        def random_search(func, search_space, budget):
            """
               Implementa la ricerca casuale per minimizzare un problema di dimensione n.

               Parameters:
               - objective_function: La funzione obiettivo da minimizzare. Deve accettare un vettore di dimensione n come input e restituire un valore numerico.
               - search_space: Una lista di tuple, ognuna contenente il range di valori ammissibili per ciascuna dimensione.
               - budget: Il numero massimo di valutazioni della funzione obiettivo consentite.

               Returns:
               - best_solution: La migliore soluzione trovata.
               - best_score: Il valore minimo della funzione obiettivo associato alla migliore soluzione.
               """
            best_solution = None
            best_score = float('inf')

            for _ in range(budget):
                solution = [np.random.uniform(low, high) for (low, high) in search_space]
                score = self.func(solution)

                # Aggiorna la migliore soluzione se necessario
                if score < best_score:
                    best_solution = solution
                    best_score = score
                print(best_score)
            return best_solution, best_score
        search_space = [(self.lb, self.ub) for _ in range(self.dim)]
        budget = self.total_budget
        random_search(self.func, search_space, budget)


class linearPCABOWrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        #import sys
        #sys.path.append('./mylib/' + 'lib_' + "linearPCABO")
        #print(sys.path)
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        bayes_bo_lib = os.path.join(
            my_dir, 'mylib', 'lib_BO_bayesoptim', 'Bayesian-Optimization')
        if not os.path.isdir(bayes_bo_lib):
            raise ImportError(
                'No such module Bayesian-Optimization, please unzip the folder Bayesian-Optimization.zip and move the unzip folder to mylib/lib_BO_bayesoptim/')
        sys.path.insert(0, bayes_bo_lib)
        print(sys.path)
        #sys.path.insert(0, bayes_bo_lib)
        #print(sys.path)
        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        #import sys
        #sys.path.insert(0, "./mylib/lib_linearPCABO/Bayesian-Optimization")
        from bayes_optim.extension import PCABO, RealSpace

        space = RealSpace([self.lb, self.ub]) * self.dim
        self.opt = PCABO(
            search_space=space,
            obj_fun=self.func,
            DoE_size=self.Doe_size,
            max_FEs=self.total_budget,
            verbose=False,
            n_point=1,
            n_components=0.90,
            acquisition_optimization={"optimizer": "BFGS"},
            random_seed=self.random_seed
        )
        
        print(self.opt.run())

    def get_acq_time(self):
        return self.opt.acq_opt_time

    def get_mode_time(self):
        return self.opt.mode_fit_time

    def get_iter_time(self):
        return self.opt.cum_iteration_time


class RDUCBWrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        # import sys
        # sys.path.append('./mylib/' + 'lib_' + "linearPCABO")
        # print(sys.path)
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        sys.path.append(os.path.join(my_dir, 'mylib', 'lib_RDUCB/HEBO/RDUCB'))
        print(sys.path)
        # sys.path.insert(0, bayes_bo_lib)
        # print(sys.path)
        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        # import sys
        # sys.path.insert(0, "./mylib/lib_linearPCABO/Bayesian-Optimization")

        from hdbo.algorithms import RDUCB
        self.opt = RDUCB( algorithm_random_seed=1,
    eps=-1,
    exploration_weight= 'lambda t: 0.5 * np.log(2*t)',
    graphSamplingNumIter=100,
    learnDependencyStructureRate=1,
    lengthscaleNumIter=2,
    max_eval=-4,
    noise_var= 0.1,
    param_n_iter=16,
    size_of_random_graph=0.2,
    data_random_seed=self.random_seed,
    fn_noise_var=0.15,
    grid_size=150,
    fn= self.func,
n_iter=self.total_budget-self.Doe_size,
n_rand=self.Doe_size, dim=self.dim,)
        self.opt.run()

    def get_acq_time(self):
        return self.opt.mybo.acq_opt_time

    def get_mode_time(self):
        return self.opt.mybo.mode_fit_time

    def get_iter_time(self):
        return self.opt.mybo.cum_iteration_time


class turbo1Wrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        #import sys
        #sys.path.append('./mylib/' + 'lib_' + "turbo1")
        #print(sys.path)
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        sys.path.append(os.path.join(my_dir, 'mylib', 'lib_turbo1'))
        print(sys.path)
        
        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        from turbo import Turbo1
        import torch
        import math
        import matplotlib
        import matplotlib.pyplot as plt
        self.opt = Turbo1(
            f=self.func,  # Handle to objective function
            lb=np.ones(self.dim) * self.lb,  # Numpy array specifying lower bounds
            ub=np.ones(self.dim) * self.ub,  # Numpy array specifying upper bounds
            n_init=self.Doe_size,  # Number of initial bounds from an Latin hypercube design
            max_evals=self.total_budget,  # Maximum number of evaluations
            batch_size=5,  # How large batch size TuRBO uses
            verbose=True,  # Print information from each batch
            use_ard=True,  # Set to true if you want to use ARD for the GP kernel
            max_cholesky_size=2000,  # When we switch from Cholesky to Lanczos
            n_training_steps=50,  # Number of steps of ADAM to learn the hypers
            min_cuda=1024,  # Run on the CPU for small datasets
            device="cpu",  # "cpu" or "cuda"
            dtype="float64",  # float64 or float32
        )
        self.opt.optimize()

    def get_acq_time(self):
        return self.opt.acq_opt_time

    def get_mode_time(self):
        return self.opt.mode_fit_time

    def get_iter_time(self):
        return self.opt.cum_iteration_time


class turbomWrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
        #import sys
        #sys.path.append('./mylib/' + 'lib_' + "turbom")
        #print(sys.path)
        
        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        sys.path.append(os.path.join(my_dir, 'mylib', 'lib_turbo1'))
        print(sys.path)
        
        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        from turbo import TurboM
        import torch
        import math
        import matplotlib
        import matplotlib.pyplot as plt
        #tr = math.floor(self.total_budget / self.Doe_size) - 1
        tr = int(self.dim/5)
        n_init = math.floor(self.Doe_size/tr)
        self.opt = TurboM(
            f=self.func,  # Handle to objective function
            lb=np.ones(self.dim) * self.lb,  # Numpy array specifying lower bounds
            ub=np.ones(self.dim) * self.ub,  # Numpy array specifying upper bounds
            n_init=n_init,  # Number of initial bounds from an Symmetric Latin hypercube design
            max_evals=self.total_budget,  # Maximum number of evaluations
            n_trust_regions=tr,  # Number of trust regions
            batch_size=5,  # How large batch size TuRBO uses
            verbose=True,  # Print information from each batch
            use_ard=True,  # Set to true if you want to use ARD for the GP kernel
            max_cholesky_size=2000,  # When we switch from Cholesky to Lanczos
            n_training_steps=50,  # Number of steps of ADAM to learn the hypers
            min_cuda=1024,  # Run on the CPU for small datasets
            device="cpu",  # "cpu" or "cuda"
            dtype="float64",  # float64 or float32
        )
        self.opt.optimize()

    def get_acq_time(self):
        return self.opt.acq_opt_time

    def get_mode_time(self):
        return self.opt.mode_fit_time

    def get_iter_time(self):
        return self.opt.cum_iteration_time

class EBOWrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
         # import sys
                 # sys.path.append('./mylib/' + 'lib_' + "EBO")
                         # print(sys.path)

        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        sys.path.append(os.path.join(my_dir, 'mylib', 'lib_EBO'))
        print(sys.path)

        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        import numpy.matlib as nm
        import functools
        from ebo_core.ebo import ebo
        from test_functions.simple_functions import sample_z
        import time
        import logging

        dx = self.dim
        z = sample_z(dx)
        k = np.array([10] * dx)
        x_range = nm.repmat([[self.lb], [self.ub]], 1, self.dim)
        x_range = x_range.astype(float)
        sigma = 0.01
        n = self.Doe_size
        budget = self.total_budget
        f = self.func
        f = functools.partial(lambda f, x: -f(x), f)
        options = {'x_range': x_range,  # input domain
                  'dx': x_range.shape[1],  # input dimension
                  'max_value': 0,  # target value
                  'T': budget,  # number of iterations
                  'B': 1,  # number of candidates to be evaluated
                  'dim_limit': 3,  # max dimension of the input for each additive function component
                  'isplot': 0,  # 1 if plotting the result; otherwise 0.
                  'z': None, 'k': None,  # group assignment and number of cuts in the Gibbs sampling subroutine
                  'alpha': 1.,  # hyperparameter of the Gibbs sampling subroutine
                  'beta': np.array([5., 2.]),
                  'opt_n': 1000,  # points randomly sampled to start continuous optimization of acfun
                  'pid': 'test3',  # process ID for Azure
                  'datadir': 'tmp_data/',  # temporary data directory for Azure
                  'gibbs_iter': 10,  # number of iterations for the Gibbs sampling subroutine
                  'useAzure': False,  # set to True if use Azure for batch evaluation
                  'func_cheap': True,  # if func cheap, we do not use Azure to test functions
                  'n_add': None,  # this should always be None. it makes dim_limit complicated if not None.
                  'nlayers': 100,  # number of the layers of tiles
                  'gp_type': 'l1',  # other choices are l1, sk, sf, dk, df
                  'gp_sigma': 0.1,  # noise standard deviation
                  'n_bo': 10,  # min number of points selected for each partition
                  'n_bo_top_percent': 0.5,  # percentage of top in bo selections
                  'n_top': 10,  # how many points to look ahead when doing choose Xnew
                  'min_leaf_size': 10,  # min number of samples in each leaf
                  'max_n_leaves': 10,  # max number of leaves
                  'thresAzure': 1,  # if batch size > thresAzure, we use Azure
                  'save_file_name': 'tmp/tmp.pk',
                  }
        self.opt = ebo(f, options)
        start = time.time()
        self.opt.run()

        print("elapsed time: ", time.time() - start)

    def get_acq_time(self):
        return self.opt.acq_opt_time

    def get_mode_time(self):
        return self.opt.mode_fit_time

    def get_iter_time(self):
        return self.opt.cum_iteration_time

class EBO_BWrapper:
    def __init__(self, func, dim, ub, lb, total_budget, DoE_size, random_seed):
         # import sys
                 # sys.path.append('./mylib/' + 'lib_' + "EBO")
                         # print(sys.path)

        import pathlib
        my_dir = pathlib.Path(__file__).parent.resolve()
        sys.path.append(os.path.join(my_dir, 'mylib', 'lib_EBO'))
        print(sys.path)

        self.func = func
        self.dim = dim
        self.ub = ub
        self.lb = lb
        self.total_budget = total_budget
        self.Doe_size = DoE_size
        self.random_seed = random_seed

    def run(self):
        import numpy.matlib as nm
        import functools
        from ebo_core.ebo import ebo
        from test_functions.simple_functions import sample_z
        import time
        import logging

        dx = self.dim
        z = sample_z(dx)
        k = np.array([10] * dx)
        x_range = nm.repmat([[self.lb], [self.ub]], 1, self.dim)
        x_range = x_range.astype(float)
        sigma = 0.01
        n = self.Doe_size
        budget = self.total_budget
        t= int (float(budget)/10)
        f = self.func
        f = functools.partial(lambda f, x: -f(x), f)
        options = {'x_range': x_range,  # input domain
                  'dx': x_range.shape[1],  # input dimension
                  'max_value': 0,  # target value
                  'T': t,  # number of iterations
                  'B': 10,  # number of candidates to be evaluated
                  'dim_limit': 3,  # max dimension of the input for each additive function component
                  'isplot': 0,  # 1 if plotting the result; otherwise 0.
                  'z': None, 'k': None,  # group assignment and number of cuts in the Gibbs sampling subroutine
                  'alpha': 1.,  # hyperparameter of the Gibbs sampling subroutine
                  'beta': np.array([5., 2.]),
                  'opt_n': 1000,  # points randomly sampled to start continuous optimization of acfun
                  'pid': 'test3',  # process ID for Azure
                  'datadir': 'tmp_data/',  # temporary data directory for Azure
                  'gibbs_iter': 10,  # number of iterations for the Gibbs sampling subroutine
                  'useAzure': False,  # set to True if use Azure for batch evaluation
                  'func_cheap': True,  # if func cheap, we do not use Azure to test functions
                  'n_add': None,  # this should always be None. it makes dim_limit complicated if not None.
                  'nlayers': 100,  # number of the layers of tiles
                  'gp_type': 'l1',  # other choices are l1, sk, sf, dk, df
                  'gp_sigma': 0.1,  # noise standard deviation
                  'n_bo': 10,  # min number of points selected for each partition
                  'n_bo_top_percent': 0.5,  # percentage of top in bo selections
                  'n_top': 10,  # how many points to look ahead when doing choose Xnew
                  'min_leaf_size': 10,  # min number of samples in each leaf
                  'max_n_leaves': 10,  # max number of leaves
                  'thresAzure': 1,  # if batch size > thresAzure, we use Azure
                  'save_file_name': 'tmp/tmp.pk',
                  }
        self.opt = ebo(f, options)
        start = time.time()
        self.opt.run()

        print("elapsed time: ", time.time() - start)

    def get_acq_time(self):
        return self.opt.acq_opt_time

    def get_mode_time(self):
        return self.opt.mode_fit_time

    def get_iter_time(self):
        return self.opt.cum_iteration_time



def wrapopt(optimizer_name, func, ml_dim, ml_total_budget, ml_DoE_size, random_seed):
    ub = +5
    lb = -5
    if optimizer_name == "saasbo":
        return SaasboWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == "BO_sklearn":
        return BO_sklearnWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                                 random_seed=random_seed)
    if optimizer_name == "BO_bayesoptim":
        return BO_bayesoptimWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                                    random_seed=random_seed)
    if optimizer_name == "random":
        return randomWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == "linearPCABO":
        return linearPCABOWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == "turbo1":
        return turbo1Wrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == "turbom":
        return turbomWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == 'BO_dev_Hao':
        return BO_development_bayesoptimWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == 'EBO':
        return EBOWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == 'EBO_B':
        return EBO_BWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == 'KPCABO':
        return KPCABOWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)
    if optimizer_name == 'pyCMA':
        return Py_CMA_ES_Wrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget,
                             random_seed=random_seed)
    if optimizer_name == 'RDUCB':
        return RDUCBWrapper(func=func, dim=ml_dim, ub=ub, lb=lb, total_budget=ml_total_budget, DoE_size=ml_DoE_size,
                             random_seed=random_seed)

if __name__ == "__main__":
    dim = 10
    total_budget = 150
    doe_size = dim
    seed = 0
    # Algorithm alternatives:
    algorithm_name = "RDUCB"

    f = get_problem(5, dimension=dim, instance=1, problem_type='Real')

    opt = wrapopt(algorithm_name, f, dim, total_budget, doe_size, seed)
    opt.run()
