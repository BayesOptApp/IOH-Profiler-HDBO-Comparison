###############################################################################
# Copyright (c) 2019 Uber Technologies, Inc.                                  #
#                                                                             #
# Licensed under the Uber Non-Commercial License (the "License");             #
# you may not use this file except in compliance with the License.            #
# You may obtain a copy of the License at the root directory of this project. #
#                                                                             #
# See the License for the specific language governing permissions and         #
# limitations under the License.                                              #
###############################################################################

import math
import sys
import time
from copy import deepcopy

import gpytorch
import numpy as np
import torch
from torch.quasirandom import SobolEngine

from .gp import train_gp
from .utils import from_unit_cube, latin_hypercube, to_unit_cube
from .extension import LinearTransform

class trPCABO:
    """The TuRBO-1 algorithm.

    Parameters
    ----------
    f : function handle
    lb : Lower variable bounds, numpy.array, shape (d,).
    ub : Upper variable bounds, numpy.array, shape (d,).
    n_init : Number of initial points (2*dim is recommended), int.
    max_evals : Total evaluation budget, int.
    batch_size : Number of points in each batch, int.
    verbose : If you want to print information about the optimization progress, bool.
    use_ard : If you want to use ARD for the GP kernel.
    max_cholesky_size : Largest number of training points where we use Cholesky, int
    n_training_steps : Number of training steps for learning the GP hypers, int
    min_cuda : We use float64 on the CPU if we have this or fewer datapoints
    device : Device to use for GP fitting ("cpu" or "cuda")
    dtype : Dtype to use for GP fitting ("float32" or "float64")

    Example usage:
        turbo1 = Turbo1(f=f, lb=lb, ub=ub, n_init=n_init, max_evals=max_evals)
        turbo1.optimize()  # Run optimization
        X, fX = turbo1.X, turbo1.fX  # Evaluated points
    """

    def __init__(
        self,
        f,
        lb,
        ub,
        n_init,
        max_evals,
        batch_size=1,
        verbose=True,
        use_ard=True,
        max_cholesky_size=2000,
        n_training_steps=50,
        min_cuda=1024,
        device="cpu",
        dtype="float64",
    ):

        # Very basic input checks
        assert lb.ndim == 1 and ub.ndim == 1
        assert len(lb) == len(ub)
        assert np.all(ub > lb)
        assert max_evals > 0 and isinstance(max_evals, int)
        assert n_init > 0 and isinstance(n_init, int)
        assert batch_size > 0 and isinstance(batch_size, int)
        assert isinstance(verbose, bool) and isinstance(use_ard, bool)
        assert max_cholesky_size >= 0 and isinstance(batch_size, int)
        assert n_training_steps >= 30 and isinstance(n_training_steps, int)
        assert max_evals > n_init and max_evals > batch_size
        assert device == "cpu" or device == "cuda"
        assert dtype == "float32" or dtype == "float64"
        if device == "cuda":
            assert torch.cuda.is_available(), "can't use cuda if it's not available"

        # Save function information
        self.f = f
        self.dim = len(lb)
        self.lb = lb
        self.ub = ub

        # Settings
        self.n_init = n_init
        self.max_evals = max_evals
        self.batch_size = batch_size
        self.verbose = verbose
        self.use_ard = use_ard
        self.max_cholesky_size = max_cholesky_size
        self.n_training_steps = n_training_steps

        # Hyperparameters
        self.mean = np.zeros((0, 1))
        self.signal_var = np.zeros((0, 1))
        self.noise_var = np.zeros((0, 1))
        self.lengthscales = np.zeros((0, self.dim)) if self.use_ard else np.zeros((0, 1))

        # Tolerances and counters
        self.n_cand = min(100 * self.dim, 5000)
        self.failtol = np.ceil(np.max([4.0 / batch_size, self.dim / batch_size]))
        self.succtol = 3
        self.n_evals = 0

        # Trust region sizes
        self.length_min = 0.5 ** 7
        self.length_max = 1.6
        self.length_init = 0.8

        # Save the full history
        self.X = np.zeros((0, self.dim))
        self.fX = np.zeros((0, 1))

        # Device and dtype for GPyTorch
        self.min_cuda = min_cuda
        self.dtype = torch.float32 if dtype == "float32" else torch.float64
        self.device = torch.device("cuda") if device == "cuda" else torch.device("cpu")
        if self.verbose:
            print("Using dtype = %s \nUsing device = %s" % (self.dtype, self.device))
            sys.stdout.flush()

        # Initialize parameters
        self._restart()

        self.acq_opt_time = 0
        self.mode_fit_time = 0
        self.cum_iteration_time = 0

    def _restart(self):
        self._X = []
        self._fX = []
        self.failcount = 0
        self.succcount = 0
        self.length = self.length_init

    def _adjust_length(self, fX_next):
        if np.min(fX_next) < np.min(self._fX) - 1e-3 * math.fabs(np.min(self._fX)):
            self.succcount += 1
            self.failcount = 0
        else:
            self.succcount = 0
            self.failcount += 1

        if self.succcount == self.succtol:  # Expand trust region
            self.length = min([2.0 * self.length, self.length_max])
            self.succcount = 0
        elif self.failcount == self.failtol:  # Shrink trust region
            self.length /= 2.0
            self.failcount = 0

    def _create_candidates(self, X, fX, X_tr, length, n_training_steps, hypers, hypers1):
        """Generate candidates assuming X has been scaled to [0,1]^d."""
        # Pick the center as the point with the smallest function values
        # NOTE: This may not be robust to noise, in which case the posterior mean of the GP can be used instead
        #assert X.min() >= 0.0 and X.max() <= 1.0

        # Standardize function values.
        mu, sigma = np.median(fX), fX.std()
        sigma = 1.0 if sigma < 1e-6 else sigma
        fX = (deepcopy(fX) - mu) / sigma

        # Figure out what device we are running on
        if len(X) < self.min_cuda:
            device, dtype = torch.device("cpu"), torch.float64
        else:
            device, dtype = self.device, self.dtype
        # AGGIUNGO PCABO


        # X_tr = self._pca.fit_transform(X, fX)
        # self.new_dim = X_tr.shape[1]
        # bounds = self._pca.transform([np.zeros(self.dim), np.ones(self.dim)])
        #bounds = self._pca.transform([np.zeros(self.dim), np.ones(self.dim)])
        # ora riporto in zero uno la roba trasformata con i bounds -0 1 trasformati
        #X_tr_n = to_unit_cube(deepcopy(X_tr), bounds[0], bounds[1])
        #X_tr_n = to_unit_cube(deepcopy(X_tr), bounds[0], bounds[1])

        # We use CG + Lanczos for training if we have enough data
        with gpytorch.settings.max_cholesky_size(self.max_cholesky_size):
            X_torch_tr = torch.tensor(X_tr).to(device=device, dtype=dtype)
            X_torch = torch.tensor(X).to(device=device, dtype=dtype)
            y_torch = torch.tensor(fX).to(device=device, dtype=dtype)
            gp = train_gp(
                train_x=X_torch_tr, train_y=y_torch, use_ard=self.use_ard, num_steps=n_training_steps, hypers=hypers
            )

            # Save state dict
            hypers = gp.state_dict()

            gp1 = train_gp(
                train_x=X_torch, train_y=y_torch, use_ard=self.use_ard, num_steps=n_training_steps, hypers=hypers1
            )
            hypers1 = gp1.state_dict()
        # Create the trust region boundaries
        x_center = X[fX.argmin().item(), :][None, :]
        weights = gp1.covar_module.base_kernel.lengthscale.cpu().detach().numpy().ravel()
        weights = weights / weights.mean()  # This will make the next line more stable
        weights = weights / np.prod(np.power(weights, 1.0 / len(weights)))  # We now have weights.prod() = 1
        lb = np.clip(x_center - weights * length / 2.0, 0.0, 1.0)
        ub = np.clip(x_center + weights * length / 2.0, 0.0, 1.0)
        #dato che sto lavorando in uno spazio ruotato non 'e detto che 0-1 intervallo quindi come intervallo prendo il
        #nuovo 0 e il nuovo 1 che ho dopo la trasformazione imparata ogni volta

        # Draw a Sobolev sequence in [lb, ub]
        seed = np.random.randint(int(1e6))
        sobol = SobolEngine(self.dim, scramble=True, seed=seed)
        pert = sobol.draw(self.n_cand).to(dtype=dtype, device=device).cpu().detach().numpy()
        pert = lb + (ub - lb) * pert
        ##Sono arrivata qui
        # Create a perturbation mask
        prob_perturb = min(20.0 / self.dim, 1.0)
        mask = np.random.rand(self.n_cand, self.dim) <= prob_perturb
        ind = np.where(np.sum(mask, axis=1) == 0)[0]
        mask[ind, np.random.randint(0, self.dim - 1, size=len(ind))] = 1

        # Create candidate points
        X_cand = x_center.copy() * np.ones((self.n_cand, self.dim))
        X_cand[mask] = pert[mask]
        X_cand_tr = from_unit_cube(X_cand, self.lb, self.ub)
        X_cand_tr = self._pca.transform(X_cand_tr)
        X_cand_tr = to_unit_cube(deepcopy(X_tr), self.bounds[0], self.bounds[1])

        # Figure out what device we are running on
        if len(X_cand) < self.min_cuda:
            device, dtype = torch.device("cpu"), torch.float64
        else:
            device, dtype = self.device, self.dtype

        # We may have to move the GP to a new device
        gp = gp.to(dtype=dtype, device=device)

        # We use Lanczos for sampling if we have enough data
        with torch.no_grad(), gpytorch.settings.max_cholesky_size(self.max_cholesky_size):
            X_cand_torch = torch.tensor(X_cand).to(device=device, dtype=dtype)
            X_cand_torch_tr = torch.tensor(X_cand_tr).to(device=device, dtype=dtype)
            y_cand = gp1.likelihood(gp1(X_cand_torch)).sample(torch.Size([self.batch_size])).t().cpu().detach().numpy()
            y_cand_tr = gp.likelihood(gp(X_cand_torch_tr)).sample(torch.Size([self.batch_size])).t().cpu().detach().numpy()
        # Remove the torch variables
        del X_torch, y_torch, X_cand_torch, gp , X_torch_tr, X_cand_torch_tr, gp1

        # De-standardize the sampled values
        y_cand = mu + sigma * y_cand
        y_cand_tr = mu + sigma * y_cand_tr

        return X_cand_tr, y_cand_tr, hypers

    def _select_candidates(self, X_cand_tr, y_cand_tr):
        """Select candidates."""
        X_next = np.ones((self.batch_size, self.new_dim))
        for i in range(self.batch_size):            # Pick the best point and make sure we never pick it again
            indbest = np.argmin(y_cand_tr[:, i])
            X_next[i, :] = deepcopy(X_cand_tr[indbest, :])
            y_cand_tr[indbest, :] = np.inf
        #X_next = self._pca.inverse_transform(X_next)
        return X_next

    def optimize(self):
        """Run the full optimization process."""
        while self.n_evals < self.max_evals:
            if len(self._fX) > 0 and self.verbose:
                n_evals, fbest = self.n_evals, self._fX.min()
                print(f"{n_evals}) Restarting with fbest = {fbest:.4}")
                sys.stdout.flush()

            # Initialize parameters
            self._restart()

            # Generate and evalute initial design points
            X_init = latin_hypercube(self.n_init, self.dim)
            X_init = from_unit_cube(X_init, self.lb, self.ub) #questa da 01 a lb ub
            fX_init = np.array([[self.f(x)] for x in X_init])

            # Update budget and set as initial data for this TR
            self.n_evals += self.n_init
            self._X = deepcopy(X_init) #qui dentro ora non sono in 01
            self._fX = deepcopy(fX_init)

            # Append data to the global history
            self.X = np.vstack((self.X, deepcopy(X_init)))
            self.fX = np.vstack((self.fX, deepcopy(fX_init)))

            if self.verbose:
                fbest = self._fX.min()
                print(f"Starting from fbest = {fbest:.4}")
                sys.stdout.flush()

            # Thompson sample to get next suggestions

            while self.n_evals < self.max_evals and self.length >= self.length_min:
                # Warp inputs
                self._pca = LinearTransform(n_components=0.9, svd_solver="full", minimize=True)
                X_tr = self._pca.fit_transform(self._X, self._fX)
                self.new_dim = X_tr.shape[1]
                #bounds = self._pca.transform([np.zeros(self.dim), np.ones(self.dim)])
                self.bounds = self._pca.transform([np.array(self.dim * self.lb), np.array(self.dim * self.ub)])
                X_tr = to_unit_cube(deepcopy(X_tr), self.bounds[0], self.bounds[1]) #ora li porto in 0 1
                X = to_unit_cube(deepcopy(self._X), self.lb, self.ub) #ora li porto in 0 1

                # Standardize values
                fX = deepcopy(self._fX).ravel()

                # Create th next batch
                start = time.process_time()
                X_cand_tr, y_cand_tr, _ = self._create_candidates(
                    X, fX, X_tr, length=self.length, n_training_steps=self.n_training_steps, hypers={}, hypers1={}
                )
                self.mode_fit_time = time.process_time() - start

                start = time.process_time()
                X_next = self._select_candidates(X_cand_tr, y_cand_tr)
                self.acq_opt_time = time.process_time() - start
                # Undo the warping and the trasformation
                X_next = from_unit_cube(X_next, self.bounds[0], self.bounds[1])
                X_next = self._pca.inverse_transform(X_next)
                # Evaluate batch
                fX_next = np.array([[self.f(x)] for x in X_next])

                # Update trust region
                self._adjust_length(fX_next)

                # Update budget and append data
                self.n_evals += self.batch_size
                self._X = np.vstack((self._X, X_next))
                self._fX = np.vstack((self._fX, fX_next))

                if self.verbose and fX_next.min() < self.fX.min():
                    n_evals, fbest = self.n_evals, fX_next.min()
                    print(f"{n_evals}) New best: {fbest:.4}")
                    sys.stdout.flush()

                # Append data to the global history
                self.X = np.vstack((self.X, deepcopy(X_next)))
                self.fX = np.vstack((self.fX, deepcopy(fX_next)))
                # Track time for the single iteration
                self.cum_iteration_time = time.process_time()