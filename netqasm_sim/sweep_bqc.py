from __future__ import annotations

import json
import math
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from netsquid.qubits.qubitapi import fidelity
from squidasm.run.stack.config import StackNetworkConfig
from squidasm.sim.stack.common import LogManager

from bqc import bqc

PI = math.pi
PI_OVER_2 = math.pi / 2

COMPILE_VERSIONS = ["vanilla", "nv"]

class Metric:
    def __init__(self, name: str, data: List[Any]) -> None:
        self._name = name
        self._data = data

        self._mean: Optional[float] = None
        self._std_error: Optional[float] = None

    @property
    def size(self) -> int:
        return len(self._data)

    @property
    def data(self) -> List[Any]:
        return self._data

    @property
    def mean(self) -> float:
        if self._mean is None:
            self._mean = sum(self._data) / self.size
        return self._mean

    @property
    def std_error(self) -> float:
        if self._std_error is None:
            variance = (
                sum((d - self.mean) * (d - self.mean) for d in self.data) / self.size
            )
            self._std_error = math.sqrt(variance) / math.sqrt(self.size)
        return self._std_error

    def serialize(self) -> Dict:
        return {"mean": self.mean, "std_error": self.std_error}


def dump_data(data: Any, filename: str) -> None:
    output_dir = os.path.join(os.path.dirname(__file__), "sweep_data_bqc")
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename_timestamp = f"{filename}_{timestamp}.json"
    filename_last = f"{filename}_LAST.json"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    path_timestamp = os.path.join(output_dir, filename_timestamp)
    path_last = os.path.join(output_dir, filename_last)
    with open(path_timestamp, "w") as f:
        json.dump(data, f, indent=4)
    # copy (i.e. write again) data to "LAST" file
    with open(path_last, "w") as f:
        json.dump(data, f, indent=4)
    print(f"data written to {path_timestamp} and {path_last}")


def get_avg_error_rate(
    cfg, num_times: int = 5, return_time: bool = False
) -> Tuple[Metric, Metric, Metric]:
    fail_rates = []
    times = []
    epr1_fids = []
    epr2_fids = []

    theta1s = [0, PI_OVER_2]
    theta2s = [0, PI_OVER_2]
    dummies = [1]
    # dummies = [1, 2]
    # theta1s = [0]
    # theta2s = [0]
    # dummies = [1]

    nr_of_combis = len(theta1s) * len(theta2s) * len(dummies)

    inner_times = []
    inner_fid1s = []
    inner_fid2s = []
    for theta1 in theta1s:
        for theta2 in theta2s:
            for dummy in dummies:
                rate, dur, fid1s, fid2s = bqc.trap_round(
                    cfg, num_times, theta1=theta1, theta2=theta2, dummy=dummy
                )
                fail_rates.append(rate)
                inner_times += dur
                inner_fid1s += fid1s
                inner_fid2s += fid2s

    for i in range(num_times):
        times_for_run_i = []
        fid1s_for_run_i = []
        fid2s_for_run_i = []
        for j in range(nr_of_combis):
            times_for_run_i.append(inner_times[j * num_times + i])
            fid1s_for_run_i.append(inner_fid1s[j * num_times + i])
            fid2s_for_run_i.append(inner_fid2s[j * num_times + i])
        time_avg_for_run_i = sum(times_for_run_i) / len(times_for_run_i)
        fid1_avg_for_run_i = sum(fid1s_for_run_i) / len(fid1s_for_run_i)
        fid2_avg_for_run_i = sum(fid2s_for_run_i) / len(fid2s_for_run_i)
        times.append(time_avg_for_run_i)
        epr1_fids.append(fid1_avg_for_run_i)
        epr2_fids.append(fid2_avg_for_run_i)

    # print(f"fail rates: {fail_rates}")
    # print(f"times: {times}")
    print(f"EPR 1 fids: {epr1_fids}")
    print(f"EPR 2 fids: {epr2_fids}")
    epr1_fid_mean = round(sum(epr1_fids) / len(epr1_fids), 3)
    epr2_fid_mean = round(sum(epr2_fids) / len(epr2_fids), 3)

    result_dict = {}
    fail_rates_metric = Metric("error_rate", fail_rates)
    epr1_fids_metric = Metric("epr1_fid", epr1_fids)
    epr2_fids_metric = Metric("epr2_fid", epr2_fids)
    # fr = fail_rates
    # mean = round(sum(fr) / len(fr), 3)
    # variance = sum((r - mean) * (r - mean) for r in fr) / len(fr)
    # std_deviation = math.sqrt(variance)
    # std_error = round(std_deviation / math.sqrt(len(fr)), 3)
    # result_dict = (mean, std_error)

    if not return_time:
        # return result_dict, epr1_fid_mean, epr2_fid_mean
        return fail_rates_metric, epr1_fids_metric, epr2_fids_metric
    else:
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
    # LogManager.log_to_file("dump.log")

    cfg = StackNetworkConfig.from_file(cfg_file)

    probs = list(np.linspace(0, 0.1, 10))
    # probs = list(np.linspace(0, 0.1, 3))

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
            # result, fid1, fid2 = get_avg_error_rate(cfg, num_times=num_times)
            error_rate, epr1_fid, epr2_fid = get_avg_error_rate(cfg, num_times=num_times)
            iteration += 1

            print(
                f"depolar_prob = {depolar_prob}: error rate = {error_rate.mean}, std_err = {error_rate.std_error}"
            )

            data[version].append(
                {
                    "sweep_value": depolar_prob,
                    "error_rate": error_rate.mean,
                    "std_err": error_rate.std_error,
                    "epr_fid1": epr1_fid.mean,
                    "epr_fid1_std_err": epr1_fid.std_error,
                    "epr_fid2": epr2_fid.mean,
                    "epr_fid2_std_err": epr2_fid.std_error,
                }
            )
            data["meta"] = {}
            data["meta"]["config"] = cfg.json()
            data["meta"]["num_times"] = num_times

    dump_data(data, "sweep_bqc")

