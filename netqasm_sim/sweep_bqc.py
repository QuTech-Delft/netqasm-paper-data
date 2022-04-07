from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any, Tuple

import numpy as np
from netsquid.qubits.qubitapi import fidelity
from squidasm.run.stack.config import StackNetworkConfig
from squidasm.sim.stack.common import LogManager

from bqc import bqc

PI = math.pi
PI_OVER_2 = math.pi / 2

COMPILE_VERSIONS = ["vanilla", "nv"]


def dump_data(data: Any, filename: str) -> None:
    output_dir = os.path.join(os.path.dirname(__file__), "sweep_data_bqc")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    with open(os.path.join(output_dir, filename), "w") as f:
        json.dump(data, f)


def get_avg_error_rate(
    cfg, num_times: int = 5, return_time: bool = False
) -> Tuple[float, float]:
    fail_rates = []
    times = []

    theta1s = [0, PI_OVER_2]
    theta2s = [0, PI_OVER_2]
    dummies = [1]
    # dummies = [1, 2]
    # theta1s = [0]
    # theta2s = [0]
    # dummies = [1]

    nr_of_combis = len(theta1s) * len(theta2s) * len(dummies)

    inner_times = []
    for theta1 in theta1s:
        for theta2 in theta2s:
            for dummy in dummies:
                rate, dur = bqc.trap_round(
                    cfg, num_times, theta1=theta1, theta2=theta2, dummy=dummy
                )
                fail_rates.append(rate)
                inner_times += dur

    for i in range(num_times):
        times_for_run_i = []
        for j in range(nr_of_combis):
            times_for_run_i.append(inner_times[j * num_times + i])
        avg_for_run_i = sum(times_for_run_i) / len(times_for_run_i)
        times.append(avg_for_run_i)

    print(f"fail rates: {fail_rates}")
    print(f"times: {times}")

    result_dict = {}
    fr = fail_rates
    mean = round(sum(fr) / len(fr), 3)
    variance = sum((r - mean) * (r - mean) for r in fr) / len(fr)
    std_deviation = math.sqrt(variance)
    std_error = round(std_deviation / math.sqrt(len(fr)), 3)
    result_dict = (mean, std_error)

    if not return_time:
        return result_dict

    times_result_dict = {}
    tim = times
    mean = round(sum(tim) / len(tim), 3)
    variance = sum((r - mean) * (r - mean) for r in tim) / len(tim)
    std_deviation = math.sqrt(variance)
    std_error = round(std_deviation / math.sqrt(len(tim)), 3)

    times_result_dict = (mean, std_error)

    return result_dict, times_result_dict


def get_avg_fidelity(
    cfg: StackNetworkConfig,
    num_times: int = 1,
    return_time: bool = False,
    log_level: str = "WARNING",
):

    fidelities = []
    times = []

    alphas = [0, PI_OVER_2, PI]
    betas = [0, PI_OVER_2, PI]
    # alphas = [0]
    # betas = [0]
    nr_of_alpha_beta_combis = len(alphas) * len(betas)

    inner_times = []
    for alpha in alphas:
        for beta in betas:
            fid, dur = bqc.computation_round(
                cfg=cfg,
                num_times=num_times,
                alpha=alpha,
                beta=beta,
                log_level=log_level,
            )
            fidelities += fid
            inner_times += dur

    for i in range(num_times):
        times_for_run_i = []
        for j in range(nr_of_alpha_beta_combis):
            times_for_run_i.append(inner_times[j * num_times + i])
        avg_for_run_i = sum(times_for_run_i) / len(times_for_run_i)
        times.append(avg_for_run_i)

    # print(fidelities)
    # print(f"times: {times}")

    result_dict = {}
    fid = fidelities
    mean = round(sum(fid) / len(fid), 3)
    variance = sum((r - mean) * (r - mean) for r in fid) / len(fid)
    std_deviation = math.sqrt(variance)
    std_error = round(std_deviation / math.sqrt(len(fid)), 3)

    result_dict = (mean, std_error)

    if not return_time:
        return result_dict

    times_result_dict = {}
    tim = times
    mean = round(sum(tim) / len(tim), 3)
    variance = sum((r - mean) * (r - mean) for r in tim) / len(tim)
    std_deviation = math.sqrt(variance)
    std_error = round(std_deviation / math.sqrt(len(tim)), 3)

    times_result_dict = (mean, std_error)

    return result_dict, times_result_dict



def sweep_gate_noise_error_rate(
    cfg_file: str, num_times: int, log_level: str = "WARNING"
) -> None:
    LogManager.set_log_level(log_level)

    cfg = StackNetworkConfig.from_file(cfg_file)

    probs = list(np.linspace(0, 0.1, 10))

    nr_of_calls_to_get_avg_error_rate = len(probs) * len(COMPILE_VERSIONS)
    iteration = 0
    start_time = time.time()

    data = {}
    for version in COMPILE_VERSIONS:
        data[version] = []

    for version in COMPILE_VERSIONS:
        if version == "vanilla":
            cfg.stacks[0].qdevice_typ = "nv_vanilla"
            cfg.stacks[1].qdevice_typ = "nv_vanilla"
        else:
            cfg.stacks[0].qdevice_typ = "nv"
            cfg.stacks[1].qdevice_typ = "nv"

        for depolar_prob in probs:
            cfg.stacks[0].qdevice_cfg["ec_gate_depolar_prob"] = depolar_prob
            cfg.stacks[1].qdevice_cfg["ec_gate_depolar_prob"] = depolar_prob
            print(f"iteration {iteration} out of {nr_of_calls_to_get_avg_error_rate}")
            print(f"time since start: {time.time() - start_time}")
            result = get_avg_error_rate(cfg, num_times=num_times)
            iteration += 1

            error_rate, std_err = result
            print(
                f"depolar_prob = {depolar_prob}: error rate = {error_rate}, std_err = {std_err}"
            )

            data[version].append(
                {
                    "sweep_value": depolar_prob,
                    "error_rate": error_rate,
                    "std_err": std_err,
                }
            )

    dump_data(data, "sweep_gate_noise_trap.json")

