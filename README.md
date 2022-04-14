Code and data used for the evaluation section of the [NetQASM paper](https://arxiv.org/abs/2111.09823).

To run the code, a specific version of the `netqasm` and `squidasm` packages are needed.
These are provided as submodules in this repository.

## Prerequisites
The code uses the `netqasm` and `squidasm` Python packages. `squidasm` relies on [NetSquid](https://netsquid.org/).
To install NetSquid, an account is needed. See the NetSquid website how this is done.

Initialize the submodules:

```
git submodule init
git submodule update
```


Install `netqasm`:
```
cd netqasm
make install
```

Make sure you have two environment variables set with your NetSquid username and password:
```
export NETSQUIDPYPI_USER=<username>
export NETSQUIDPYPI_PWD=password
```

Install `squidasm`:
```
cd ../squidasm
make install
```



After installation, the simulations can be run, as described below.

## Producing simulation data and plots

Teleportation fidelity as a function of gate noise (Figure 11.a):
```
$ python netqasm_sim/simulate_teleport.py sweep --param gate_noise --config teleport_cfg1 --num <NUM_ITERATIONS>
$ python netqasm_sim/plot_teleport.py --param gate_noise
```


Teleportation fidelity as a function of gate duration (Figure 11.b):
```
$ python netqasm_sim/simulate_teleport.py sweep --param gate_time --config teleport_cfg1 --num <NUM_ITERATIONS>
$ python netqasm_sim/plot_teleport.py --param gate_time
```


BQC error rate as a function of gate noise (Figure 13):
```
$ python netqasm_sim/simulate_bqc.py sweep --param gate_noise_trap --config near_perfect_nv --num <NUM_ITERATIONS>
$ python netqasm_sim/plot_bqc.py --param gate_noise_trap
```

To also plot the fidelity of the remotely prepared states.
```
$ python netqasm_sim/plot_bqc.py --param gate_noise_epr_fidelity
```

The simulation data that was used to create the plots in the paper is in the `final_data` directory.