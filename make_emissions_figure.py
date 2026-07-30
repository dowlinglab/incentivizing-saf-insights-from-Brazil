"""Net-transportation-emissions contour with the literature comparison (Figure 6).

Reproduces the manuscript's Figure 6 in full, including the two annotations that
were previously added by hand and so lived nowhere in the repository: the dashed
conversion upper bound at 0.65 (derived in SI Section S5.1) and the labels on the
five literature points.

The literature points are labelled A-E rather than by reference number. The
published version carried reference numbers baked into the image, which silently
became wrong when the bibliography style changed from alphabetical
(elsarticle-harv) to citation order: the five labels [59], [12], [51], [50], [33]
should now read [7], [63], [64], [65], [66]. Letters keep the figure independent
of the bibliography; the mapping lives in the manuscript caption. Do not
reintroduce numbers here.

Letters follow the row order of SI Table S2, so A-E read down that table.

Examples:
    python make_emissions_figure.py
    python make_emissions_figure.py --output /path/to/images/emissions_v7.png
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

this_file_path = os.path.dirname(os.path.realpath(__file__))

#Nominal quantities, matching SupplyChainSummary.ipynb exactly so the contour is
#unchanged from the published figure
SAF_50_PCT = 2_140_000        #m3 SAF for a 50% blend
ETHANOL_MJ_PER_M3 = 21_200    #energy density of ethanol
JET_MJ_PER_M3 = 35_300        #energy density of jet fuel and SAF
GASOLINE_MINUS_ETHANOL = 52.4 #gCO2/MJ; 75.5 gasoline less 23.1 sugarcane ethanol
JET_FUEL_CO2 = 90             #gCO2/MJ for conventional jet fuel

#Nominal ATJ point. The published figure plots the star at conversion 0.42 while
#the caption and SI Table S2 both say 0.41; that discrepancy is an open item in
#claude_audit2.tex, so the published value is kept here rather than silently
#resolved. Change with --nominal-conv once the authors decide.
NOMINAL_EMISSIONS = 45
NOMINAL_CONVERSION = 0.42

#Theoretical maximum ethanol-to-SAF conversion from the carbon balance in
#SI Section S5.1 (\label{sec: best SAF conv}; confirmed against SI_jcp.aux)
CONVERSION_UPPER_BOUND = 0.65

#Literature points, in SI Table S2 row order, which fixes the A-E labelling.
#park2022techno is plotted at 37 gCO2/MJ to match the published figure; SI
#Table S2 lists 1.63 for the same study. That disagreement is also an open audit
#item and is deliberately not resolved here.
LITERATURE = [
    ("A", 2.3, 0.42, "tanzil2022evaluation"),
    ("B", 20.7, 0.26, "klein2018techno"),
    ("C", 26.0, 0.40, "de2017life"),
    ("D", 37.0, 0.56, "park2022techno"),
    ("E", 26.0, 0.27, "pescarini2025strategic"),
]


def net_emissions(saf_co2, saf_conv):
    """Net CO2 for a 0% -> 50% SAF blend change, Mt CO2/year.

    Positive is an emissions increase. First term is the ground-transport penalty
    from ethanol displaced into SAF; second is the aviation saving.
    """
    ground = (SAF_50_PCT / saf_conv) * ETHANOL_MJ_PER_M3 * GASOLINE_MINUS_ETHANOL
    aviation = SAF_50_PCT * JET_MJ_PER_M3 * (JET_FUEL_CO2 - saf_co2)
    return (ground - aviation) / 1e12


def build(output, nominal_conv, dpi):
    #Finer grid than the notebook's 51x11 so the contour lines are smooth; the
    #function is analytic, so this changes appearance only, not values
    emissions_axis = np.linspace(0, 50, 201)
    conversion_axis = np.linspace(0.2, 1.0, 161)
    grid_e, grid_c = np.meshgrid(emissions_axis, conversion_axis)
    net = net_emissions(saf_co2=grid_e, saf_conv=grid_c)

    fig, ax = plt.subplots(figsize=(8, 5.6))
    norm = TwoSlopeNorm(vmin=net.min(), vcenter=0, vmax=net.max())
    filled = ax.contourf(grid_e, grid_c, net, levels=40, cmap="RdYlGn_r", norm=norm)
    lines = ax.contour(grid_e, grid_c, net, levels=12, colors="black", linewidths=0.5)
    ax.clabel(lines, lines.levels, inline=True, fontsize=9)

    cbar = fig.colorbar(filled, ax=ax)
    cbar.set_label("Net Transportation CO$_2$ Emissions\n(Mt CO$_2$ year$^{-1}$)",
                   weight="bold", fontsize=12)

    #Theoretical conversion ceiling: everything above it is unreachable
    ax.axhline(CONVERSION_UPPER_BOUND, color="black", linestyle="--", linewidth=2)
    #Placed away from the left edge so it clears the 3.0 contour label
    ax.text(16.0, CONVERSION_UPPER_BOUND + 0.015, "conversion upper bound",
            fontsize=11, weight="bold", va="bottom")

    ax.scatter(NOMINAL_EMISSIONS, nominal_conv, color="black", s=170,
               marker="*", label="Nominal", zorder=5)
    ax.scatter([e for _, e, _, _ in LITERATURE], [c for _, _, c, _ in LITERATURE],
               color="black", s=60, marker="o", label="Literature", zorder=5)

    #Letters, not reference numbers -- see the module docstring
    for letter, e, c, _key in LITERATURE:
        ax.annotate(letter, (e, c), textcoords="offset points", xytext=(9, -4),
                    fontsize=13, weight="bold", zorder=6)

    ax.set_xlabel("SAF LCA Emissions\n(gCO$_2$ MJ$^{-1}$)", weight="bold", fontsize=13)
    ax.set_ylabel("ATJ Conversion\n(m$^3$ SAF m$^{-3}$ ethanol)", weight="bold", fontsize=13)
    ax.tick_params(labelsize=12)
    ax.set_xlim(0, 50)
    ax.set_ylim(0.2, 1.0)
    ax.legend(loc="upper right", fontsize=12)

    fig.savefig(output, bbox_inches="tight", dpi=dpi)
    print(f"wrote {output}")

    nominal = net_emissions(NOMINAL_EMISSIONS, nominal_conv)
    at_caption_value = net_emissions(NOMINAL_EMISSIONS, 0.41)
    print(f"  net emissions at the plotted nominal "
          f"({NOMINAL_EMISSIONS} gCO2/MJ, {nominal_conv}): {nominal:.2f} Mt CO2/yr")
    print(f"  net emissions at the caption's 0.41 conversion        : "
          f"{at_caption_value:.2f} Mt CO2/yr  <- the published 2.4 Mt")
    print("  literature labels: " +
          ", ".join(f"{l}={k}" for l, _, _, k in LITERATURE))


parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--output",
                    default=os.path.join(this_file_path, "Results_Figures",
                                         "emissions_labelled_regenerated.png"),
                    help="output path (default: Results_Figures/"
                         "emissions_labelled_regenerated.png)")
parser.add_argument("--nominal-conv", type=float, default=NOMINAL_CONVERSION,
                    help=f"ATJ conversion for the nominal star "
                         f"(default: {NOMINAL_CONVERSION}, the published value; "
                         f"the caption says 0.41)")
parser.add_argument("--dpi", type=int, default=400, help="output resolution (default: 400)")
args = parser.parse_args()

build(args.output, args.nominal_conv, args.dpi)
