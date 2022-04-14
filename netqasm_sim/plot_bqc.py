import json
import os
from argparse import ArgumentParser
from pathlib import Path

import matplotlib.pyplot as plt

COMPILE_VERSIONS = ["vanilla", "nv"]
FORMATS = {
    "vanilla": "-ro",
    "nv": "-bs",
}
FORMATS_EPR1 = {
    "vanilla": "-go",
    "nv": "--yo",
}
FORMATS_EPR2 = {
    "vanilla": "-r^",
    "nv": "-bs",
}
VERSION_LABELS = {
    "vanilla": "Vanilla NetQASM",
    "nv": "NV NetQASM",
}
LABEL_EPR_FID1 = {
    "vanilla": "2nd prepared state (both vanilla and NV)",
    "nv": "EPR 1 fidelity nv",
}
LABEL_EPR_FID2 = {
    "vanilla": "1st prepared state (vanilla)",
    "nv": "1st prepared state (nv)",
}

X_LABELS = {
    "gate_noise_trap": "2-qubit gate depolarising probability",
    "gate_noise_epr_fidelity": "2-qubit gate depolarising probability"
}


def create_png(param_name):
    output_dir = os.path.join(os.path.dirname(__file__), "plots_bqc")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, f"bqc_sweep_{param_name}.png")
    plt.savefig(output_path)
    print(f"plot written to {output_path}")


def plot_gate_noise_trap(data: str):
    param_name = "gate_noise_trap"

    data_path = os.path.join(
        os.path.dirname(__file__), f"sweep_data_bqc/sweep_bqc_{data}.json"
    )

    with open(data_path, "r") as f:
        all_data = json.load(f)

    fig, ax = plt.subplots()

    ax.grid()
    ax.set_xlabel(X_LABELS[param_name])
    ax.set_ylabel("Error rate")

    for version in COMPILE_VERSIONS:
        data = all_data[version]
        sweep_values = [v["sweep_value"] for v in data]
        error_rates = [v["error_rate"] for v in data]
        std_errs = [v["std_err"] for v in data]
        ax.errorbar(
            x=sweep_values,
            y=error_rates,
            yerr=std_errs,
            fmt=FORMATS[version],
            label=VERSION_LABELS[version],
        )


    ax.set_title(
        "BQC trap round error rate vs two-qubit gate noise probability",
        wrap=True,
    )

    ax.legend()

    create_png(param_name)

def plot_gate_noise_epr_fidelity(data: str):
    param_name = "gate_noise_epr_fidelity"

    data_path = os.path.join(
        os.path.dirname(__file__), f"sweep_data_bqc/sweep_bqc_{data}.json"
    )

    with open(data_path, "r") as f:
        all_data = json.load(f)

    fig, ax = plt.subplots()

    ax.grid()
    ax.set_xlabel(X_LABELS[param_name])
    ax.set_ylabel("Fidelity")

    for version in COMPILE_VERSIONS:
        data = all_data[version]
        sweep_values = [v["sweep_value"] for v in data]
        epr_fid1s = [v["epr_fid1"] for v in data]
        epr_fid1_std_errs = [v["epr_fid1_std_err"] for v in data]
        epr_fid2s = [v["epr_fid2"] for v in data]
        epr_fid2_std_errs = [v["epr_fid2_std_err"] for v in data]
        if version == "vanilla":
            ax.errorbar(
                x=sweep_values,
                y=epr_fid1s,
                yerr=epr_fid1_std_errs,
                fmt=FORMATS_EPR1[version],
                label=LABEL_EPR_FID1[version],
            )
        ax.errorbar(
            x=sweep_values,
            y=epr_fid2s,
            yerr=epr_fid2_std_errs,
            fmt=FORMATS_EPR2[version],
            label=LABEL_EPR_FID2[version],
        )
    
    ax.set_ylim(0.75, 1)

    ax.set_title(
        "Fidelity of remotely prepared states",
        wrap=True,
    )

    ax.legend(loc="best")

    create_png(param_name)


def plot(args):
    if args.data is None:
        args.data = "LAST"
    if args.param == "gate_noise_trap":
        plot_gate_noise_trap(args.data)
    elif args.param == "gate_noise_epr_fidelity":
        plot_gate_noise_epr_fidelity(args.data)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.set_defaults(func=plot)
    parser.add_argument(
        "--param",
        type=str,
        choices={
            "gate_noise_trap",
            "gate_noise_epr_fidelity",
        },
        required=True,
    )
    parser.add_argument("--data", type=str, required=False)

    args = parser.parse_args()
    args.func(args)
