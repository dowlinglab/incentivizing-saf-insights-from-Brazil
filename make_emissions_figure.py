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
    python make_emissions_figure.py --output Results_Figures/emissions_v9.png

Emission factors are the cited ones: sugarcane ethanol 21.3 gCO2/MJ (Seabra et al.)
and conventional jet fuel 89 gCO2/MJ (CORSIA). The published figure was drawn with
23.1 and 90 -- the code had rounded 90 and transposed 21.3 -- which put the nominal
net at 2.40 Mt CO2/yr instead of 2.67.
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
GASOLINE_MINUS_ETHANOL = 54.2 #gCO2/MJ; 75.5 gasoline less 21.3 sugarcane ethanol
JET_FUEL_CO2 = 89             #gCO2/MJ for conventional jet fuel (CORSIA default)

#Nominal ATJ point. 0.41 is the decided value, matching the manuscript caption and
#SI Table S2. The published image plotted the star at 0.42, which was the anomaly:
#0.41 reproduces the 2.4 Mt CO2/yr headline that appears in the abstract, Key
#Finding 1 and Conclusion 1, whereas 0.42 gives 2.26. Confirmed by the author.
#Use --nominal-conv 0.42 to reproduce the superseded position.
NOMINAL_EMISSIONS = 45
NOMINAL_CONVERSION = 0.41

#Theoretical maximum ethanol-to-SAF conversion from the carbon balance in
#SI Section S5.1 (\label{sec: best SAF conv}; confirmed against SI_jcp.aux)
CONVERSION_UPPER_BOUND = 0.65

#Literature points, in SI Table S2 row order, which fixes the A-E labelling.
#
#park2022techno at 37 gCO2/MJ is correct and no longer an open item: their 1.63 is
#kg CO2,eq per kg of product, which at this study's jet energy density of
#44.1 MJ/kg is 36.9 gCO2/MJ. SI Table S2 has been corrected to 37.
#
#Three values were revised against primary sources:
#  A tanzil2022evaluation  conversion 0.42 -> 0.41. Their SI Table S2B adopts a
#    total fuel yield of 0.6 kg fuel per kg ethanol directly from Geleynse et al.
#    (2018), the same ATJ technology used here, so their conversion is identical
#    to our nominal rather than 0.01 above it. SI Table S2 already listed 0.41.
#  C de2017life           emissions 26.0 -> 31.0. The genuine error in the
#    published figure. 26 was read off their Figure 5, captioned "Sensitivity
#    analysis on hydrogen consumption, N fertilizer input and conversion yield" --
#    a sensitivity bound, not a central estimate. Their Table 4 gives
#    ATJ/sugarcane as 31 gCO2-eq/MJ, identically under energy allocation and
#    displacement.
#  E pescarini2025strategic emissions 26.0 -> 27.0. Scenario ATJ1G-C (first-
#    generation ethanol, no biomethane, no direct land use change): SI Table A.16
#    gives 1.71 Mt CO2e against a delivered SAF demand of 63.4 PJ, i.e.
#    26.97 gCO2e/MJ. Confirmed by the author.
LITERATURE = [
    ("A", 2.3, 0.41, "tanzil2022evaluation"),
    ("B", 20.7, 0.26, "klein2018techno"),
    ("C", 31.0, 0.40, "de2017life"),
    ("D", 37.0, 0.56, "park2022techno"),
    ("E", 27.0, 0.27, "pescarini2025strategic"),
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
    superseded = net_emissions(NOMINAL_EMISSIONS, 0.42)
    print(f"  net emissions at the plotted nominal "
          f"({NOMINAL_EMISSIONS} gCO2/MJ, {nominal_conv}): {nominal:.2f} Mt CO2/yr")
    print(f"  for the record, at the superseded 0.42 conversion      : "
          f"{superseded:.2f} Mt CO2/yr")
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
                         f"(default: {NOMINAL_CONVERSION}, matching the caption and "
                         f"SI Table S2; pass 0.42 for the superseded position)")
parser.add_argument("--dpi", type=int, default=400, help="output resolution (default: 400)")
args = parser.parse_args()

build(args.output, args.nominal_conv, args.dpi)
