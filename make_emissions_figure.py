"""Net-transportation-emissions contour with the literature comparison (Figure 6).

Reproduces the manuscript's Figure 6 in full, including the two annotations that
were previously added by hand and so lived nowhere in the repository: the dashed
conversion upper bound at 0.65 (derived in SI Section S5.1) and the labels on the
five literature points.

ICAO's two CORSIA default intensities are also drawn, as dashed vertical lines
rather than as points: CORSIA publishes an emissions intensity per pathway and no
ethanol-to-jet yield, so plotting a point would pair ICAO's x with our y and imply
they report a conversion. See the comment on CORSIA below for the ICAO source and
the full reasoning.

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
    python make_emissions_figure.py --output Results_Figures/emissions_v11.png

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

#ICAO's CORSIA default intensities for this exact pathway, plotted as reference
#values rather than as literature studies.
#
#Source: ICAO, "CORSIA Default Life Cycle Emissions Values for CORSIA Eligible
#Fuels", March 2024, Table 4 -- the table for the Alcohol (ethanol) to jet (ETJ)
#fuel conversion process -- first row: region Brazil, feedstock Sugarcane, pathway
#specification "Integrated conversion design". That row gives a Core LCA value of
#24.1, an ILUC LCA value of 8.7 and an LCEF total of 32.8 gCO2e/MJ, so
#32.8 = 24.1 + 8.7.
#
#Take the row from Table 4 specifically. The preceding table carries a
#visually similar Brazil/Sugarcane row at 24.0 / 7.3 / 31.3 for a different
#conversion process, and the later one gives 32.8 / 11.3 / 44.1.
#
#Deliberately NOT appended to LITERATURE. That list's row order fixes the A-E
#labelling against SI Table S2, and check_consistency.py in the manuscript
#repository parses LITERATURE and cross-checks all five entries against that
#table. CORSIA is an external reference value, not one of the five studies.
#
#Drawn as dashed VERTICAL LINES, not as points. CORSIA publishes an emissions
#intensity per pathway and no ethanol-to-jet yield, so the data is one-dimensional.
#Plotting it as a point would pair ICAO's x with our y and imply they report a
#conversion, which they do not. A line also says more: it shows what the CORSIA
#intensity implies at every conversion rather than only at ours. The lines stop at
#CONVERSION_UPPER_BOUND because conversions above it are unreachable.
#
#The star stays a point -- both of its coordinates are ours.
CORSIA = [("CORSIA core", 24.1), ("CORSIA total", 32.8)]

#Per-letter label offsets, in typographic points -- matplotlib's "offset points"
#unit, not emissions units, and nothing to do with the plotted points.
#
#The default puts the letter to the right of its marker. C is overridden to the left
#because the dashed CORSIA total line stands at 32.8 while C's marker is at 31.0: at
#the default (9, -4) the letter lands at roughly 32.0 to 32.7 on the emissions axis,
#which the line runs straight through. Measured on the render rather than reasoned
#about -- the default gives 2 intersecting bounding-box pairs at 0 px separation,
#the letter merging with the line, while the override gives 0. Keep the override for
#as long as that line is at 32.8.
LABEL_OFFSETS = {"C": (-17, -4)}
DEFAULT_LABEL_OFFSET = (9, -4)


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

    #CORSIA intensities as vertical lines -- see the comment on CORSIA for why these
    #are not points. vlines rather than axvline so they terminate at the ceiling.
    #Same linewidth 2 and dash style as the horizontal conversion bound, so the three
    #reference lines read as one family.
    for tag, e in CORSIA:
        ax.vlines(e, ax.get_ylim()[0], CONVERSION_UPPER_BOUND, color="black",
                  linestyle="--", linewidth=2, zorder=4)
        #Rotated and to the right of the line: the two lines are only 8.7 apart on a
        #0-50 axis, so horizontal text would collide. Hung from just under the
        #ceiling so it clears the markers lower down. Labels are deliberately short --
        #"core" is the core LCA value and "total" adds ILUC; the caption and main text
        #carry that explanation rather than the figure.
        ax.text(e + 0.6, CONVERSION_UPPER_BOUND - 0.015, tag, rotation=90,
                fontsize=11, weight="bold", va="top", ha="left", zorder=6)

    #Letters, not reference numbers -- see the module docstring
    for letter, e, c, _key in LITERATURE:
        ax.annotate(letter, (e, c), textcoords="offset points",
                    xytext=LABEL_OFFSETS.get(letter, DEFAULT_LABEL_OFFSET),
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
    print(f"  net emissions along the nominal-conversion line "
          f"(conversion {nominal_conv}):")
    for tag, e in [("nominal", NOMINAL_EMISSIONS)] + [(t, e) for t, e in
                                                      reversed(CORSIA)]:
        print(f"    {tag:<26} {e:>5} gCO2/MJ -> "
              f"{net_emissions(e, nominal_conv):6.3f} Mt CO2/yr")

    #Where each intensity breaks even, and what it gives at the ceiling. This is the
    #interpretive content of drawing these as lines: net = 0 when
    #(SAF/c) * ETH_MJ * GME == SAF * JET_MJ * (JET_FUEL_CO2 - e), i.e.
    #c = ETH_MJ * GME / (JET_MJ * (JET_FUEL_CO2 - e)).
    print("  break-even conversion, and net at the 0.65 ceiling:")
    for tag, e in [(t, e) for t, e in CORSIA] + [("nominal", NOMINAL_EMISSIONS)]:
        c_star = (ETHANOL_MJ_PER_M3 * GASOLINE_MINUS_ETHANOL
                  / (JET_MJ_PER_M3 * (JET_FUEL_CO2 - e)))
        reach = "below the ceiling" if c_star < CONVERSION_UPPER_BOUND else "UNREACHABLE"
        print(f"    {tag:<26} {e:>5} gCO2/MJ -> break-even c = {c_star:.3f} "
              f"({reach}); net at 0.65 = {net_emissions(e, CONVERSION_UPPER_BOUND):+.3f}")


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
