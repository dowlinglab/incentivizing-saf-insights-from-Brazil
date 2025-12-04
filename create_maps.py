#Import Necessary Packages
import pandas as pd
import folium
from folium import LayerControl
import os
import geopandas as gpd
from shapely.geometry import Point

def create_model_map(results_folder1,results_folder2):

    this_file_path = os.path.dirname(os.path.realpath(__file__))

    # create a directory to save results
    results_dir1 = os.path.join(this_file_path, results_folder1)
    results_dir = os.path.join(results_dir1, results_folder2)

    # Load the CSV files and the Excel files
    mill_to_mill_volumes_path = results_dir + '/mill_to_mill_volumes.csv'
    mill_to_airport_volumes_path = results_dir + '/mill_to_airport_volumes.csv'
    mill_to_refinery_path = results_dir + '/mill_to_ref_vol_saf.csv'
    mill_to_ref_path_eth = results_dir + '/mill_to_ref_vol_eth.csv'
    ref_to_airport_path = results_dir + '/ref_to_air_vol_saf.csv'
    mills_lat_lon_path = '335MillsLatitudesLongitudes.xlsx'
    airports_lat_lon_path = 'AirportsLatitudeLongitude.xlsx'
    refineries_lat_lon_path = 'OilRefineriesLatLong.xlsx'

    # Load the volume data ensuring proper decimal handling
    mill_to_mill_volumes = pd.read_csv(mill_to_mill_volumes_path, delimiter=',', decimal='.')
    mill_to_airport_volumes = pd.read_csv(mill_to_airport_volumes_path, delimiter=',', decimal='.')
    mill_to_ref_volumes = pd.read_csv(mill_to_refinery_path, delimiter=',', decimal='.')
    mill_to_ref_volumes_eth = pd.read_csv(mill_to_ref_path_eth, delimiter=',', decimal='.')
    ref_to_air_volumes = pd.read_csv(ref_to_airport_path, delimiter=',', decimal='.')

    # Load the lat/lon data for mills and airports
    mills_lat_lon = pd.read_excel(mills_lat_lon_path)
    airports_lat_lon = pd.read_excel(airports_lat_lon_path)
    refineries_lat_lon = pd.read_excel(refineries_lat_lon_path)

    # Create dictionaries for lat/lon data
    mills_lat_lon_dict = mills_lat_lon.set_index('Mills')[['Latitude', 'Longitude']].to_dict('index')
    airports_lat_lon_dict = airports_lat_lon.set_index('NOME')[['Latitude', 'Longitude']].to_dict('index')
    refineries_lat_lon_dict = refineries_lat_lon.set_index('name')[['Latitude', 'Longitude']].to_dict('index')

    shapefile_path = "ne_50m_admin_0_countries.shp"
    world = gpd.read_file(shapefile_path)

    if world.crs is None:
        world = world.set_crs(epsg=4326)
    else:
        world = world.to_crs(epsg=4326)

    print(world.columns)

    # Filter for Brazil
    brazil = world[world['NAME'] == 'Brazil']

    # Prepare the base map centered on Brazil
    map_center = [-15.788497, -47.879873]  # Center of Brazil
    m = folium.Map(location=map_center, zoom_start=5)

    # Add layers to the map
    mill_to_airport_layer = folium.FeatureGroup(name="Mills producing SAF").add_to(m)
    mill_to_mill_layer = folium.FeatureGroup(name="Ethanol supplying Mills (to Mills)").add_to(m)
    mill_to_ref_layer = folium.FeatureGroup(name="Ethanol supplying Mills (to Refineries)").add_to(m)
    inactive_mill_layer = folium.FeatureGroup(name="Unused Mills").add_to(m)
    airport_layer = folium.FeatureGroup(name="Airports").add_to(m)
    refinery_layer = folium.FeatureGroup(name="Refineries").add_to(m)
    mill_mill_line_layer = folium.FeatureGroup(name="Ethanol Supply Lines (Blue)").add_to(m)
    mill_to_ref_eth_line_layer = folium.FeatureGroup(name="Ethanol Supply Lines").add_to(m)
    mill_airport_line_layer = folium.FeatureGroup(name="SAF Supply Lines (Green)").add_to(m)
    mill_to_ref_line_layer = folium.FeatureGroup(name="SAF Supply Lines (Green)").add_to(m)
    ref_airport_line_layer = folium.FeatureGroup(name="Blended SAF Supply Lines (Green)").add_to(m)

    # Get mills (from columns) and airports (from the 'volumes' column)
    mills = mill_to_airport_volumes.columns[2:]  # Mills are in the columns (skipping the first column 'volumes')
    airports = mill_to_airport_volumes['volumes'].values  # Airports are in the 'volumes' column
    refineries = refineries_lat_lon['name'].values

    # Function to normalize line thickness
    def normalize_thickness(volume, min_volume, max_volume, min_thickness=2, max_thickness=10):
        if max_volume == min_volume:
            return min_thickness  # Avoid division by zero
        return min_thickness + (max_thickness - min_thickness) * (volume - min_volume) / (max_volume - min_volume)

    # Convert to numeric and handle non-numeric values as NaN
    mill_to_mill_volumes_numeric = mill_to_mill_volumes.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
    mill_to_airport_volumes_numeric = mill_to_airport_volumes.iloc[:, 2:].apply(pd.to_numeric, errors='coerce')
    # print(mill_to_airport_volumes)

    mill_to_ref_vol_numeric = mill_to_ref_volumes.iloc[:, 2:].apply(pd.to_numeric, errors='coerce')

    mill_to_ref_vol_eth_numeric = mill_to_ref_volumes_eth.iloc[:, 2:].apply(pd.to_numeric, errors='coerce')

    print(mill_to_ref_vol_numeric)
    ref_to_air_vol_numeric = ref_to_air_volumes.iloc[:, 2:].apply(pd.to_numeric, errors='coerce')
    print(ref_to_air_vol_numeric)

    # Get min and max volumes for normalization
    ethanol_volumes = mill_to_mill_volumes_numeric.stack()
    saf_volumes = mill_to_airport_volumes_numeric.stack()

    min_ethanol_volume, max_ethanol_volume = ethanol_volumes.min(), ethanol_volumes.max()
    min_saf_volume, max_saf_volume = saf_volumes.min(), saf_volumes.max()

    # Identify mills that send to airports
    mills_sending_to_airports = mill_to_airport_volumes_numeric.columns[(mill_to_airport_volumes_numeric > 0).any(axis=0)].tolist()
    # Identify mills that send to other mills
    mills_sending_to_mills = mill_to_mill_volumes_numeric.columns[(mill_to_mill_volumes_numeric > 0).any(axis=0)].tolist()
    # Identify mills that send to refs
    mills_sending_to_refs = mill_to_ref_vol_numeric.columns[(mill_to_ref_vol_numeric > 0).any(axis=0)].tolist()
    # Identify mills that send eth to refs
    mills_sending_eth_to_refs = mill_to_ref_vol_eth_numeric.columns[(mill_to_ref_vol_eth_numeric > 0).any(axis=0)].tolist()
    # Identify refs that send to airport
    refs_sending_to_airports = ref_to_air_vol_numeric.columns[(ref_to_air_vol_numeric > 0).any(axis=0)].tolist()

    # Mills that are in the data but don't send anything
    inactive_mills = [mill for mill in mills if mill not in mills_sending_to_airports and mill not in mills_sending_to_mills and mill not in mills_sending_to_refs and mill not in mills_sending_eth_to_refs]

    inactive_refs = [ref for ref in refineries if ref not in refs_sending_to_airports]

    # Count mills and airports
    total_mills_airport = len(mills_sending_to_refs)
    total_mills_ref = len(mills_sending_eth_to_refs)
    total_mills_mill = len(mills_sending_to_mills)
    total_refs = len(refs_sending_to_airports)
    total_inactive_mills = len(inactive_mills)
    total_inactive_refs = len(inactive_refs)
    total_airports = len(airports)

    # Add markers for mills (with different colors)
    for mill in mills:
        coords = [mills_lat_lon_dict[mill]['Latitude'], mills_lat_lon_dict[mill]['Longitude']]
        
        if mill in mills_sending_to_refs:
            folium.Marker(
                location=coords,
                popup=mill,
                icon=folium.Icon(color="green", icon="circle", prefix='fa')  # Green for mills sending to airports (using "tint" icon for drop)
            ).add_to(mill_to_airport_layer)
        elif mill in mills_sending_to_mills:
            folium.Marker(
                location=coords,
                popup=mill,
                icon=folium.Icon(color="darkblue", icon="play", prefix = 'fa')  # Blue for mills sending to other mills
            ).add_to(mill_to_mill_layer)
        elif mill in mills_sending_eth_to_refs:
            folium.Marker(
                location=coords,
                popup=mill,
                icon=folium.Icon(color="darkblue", icon="play", prefix = 'fa')  # Blue for mills sending eth to other refs
            ).add_to(mill_to_ref_layer)
        elif mill in inactive_mills:
            folium.Marker(
                location=coords,
                popup=mill,
                icon=folium.Icon(color="lightblue", icon="tint")  # Light blue for inactive mills
            ).add_to(inactive_mill_layer)

    # Add markers for airports
    for airport in airports:
        if airport in airports_lat_lon_dict:  # Ensure the airport exists in the latitude/longitude data
            coords = airports_lat_lon_dict[airport]
            folium.Marker(
                location=[coords['Latitude'], coords['Longitude']],
                popup=airport,
                icon=folium.Icon(color="red", icon="plane")
            ).add_to(airport_layer)

    # Add markers for refineries
    for ref in refineries:
        if ref in refs_sending_to_airports:  # Ensure the airport exists in the latitude/longitude data
            coords = refineries_lat_lon_dict[ref]
            folium.Marker(
                location=[coords['Latitude'], coords['Longitude']],
                popup=ref,
                icon=folium.Icon(color="black", icon="stop")
            ).add_to(refinery_layer)

        folium.GeoJson(
        brazil,
        name="Brazil",
        style_function=lambda x: {
            "fillColor": "none",
            "color": "black",
            "weight": 4,
        }
    ).add_to(m)

    # # Fit map to Brazil’s bounds
    m.fit_bounds(brazil.total_bounds.reshape(2,2).tolist())

    # Add lines for mill-to-mill volumes (ethanol)
    for i, row in mill_to_mill_volumes.iterrows():
        mill_from = row['volumes']
        for mill_to, volume in row[1:].items():
            volume = pd.to_numeric(volume, errors='coerce')
            if volume > 0 and mill_from in mills_lat_lon_dict and mill_to in mills_lat_lon_dict:
                coords_from = [mills_lat_lon_dict[mill_from]['Latitude'], mills_lat_lon_dict[mill_from]['Longitude']]
                coords_to = [mills_lat_lon_dict[mill_to]['Latitude'], mills_lat_lon_dict[mill_to]['Longitude']]
                line_thickness = normalize_thickness(volume, min_ethanol_volume, max_ethanol_volume)
                folium.PolyLine(
                    locations=[coords_from, coords_to],
                    color="blue",
                    weight=line_thickness,  # Normalized line thickness
                    popup=f"{volume} ethanol from {mill_from} to {mill_to}"
                ).add_to(mill_mill_line_layer)

    # Add lines for mill-to-airport volumes (SAF)
    for i, row in mill_to_airport_volumes.iterrows():
        airport = row['volumes']  # Get the name of the airport
        if airport in airports_lat_lon_dict:  # Ensure the airport exists in the latitude/longitude data
            coords_to = [airports_lat_lon_dict[airport]['Latitude'], airports_lat_lon_dict[airport]['Longitude']]
            for mill, volume in row[2:].items():
                volume = pd.to_numeric(volume, errors='coerce')
                if volume > 0 and mill in mills_lat_lon_dict:  # Ensure the mill exists in the latitude/longitude data
                    coords_from = [mills_lat_lon_dict[mill]['Latitude'], mills_lat_lon_dict[mill]['Longitude']]
                    line_thickness = normalize_thickness(volume, min_saf_volume, max_saf_volume)
                    folium.PolyLine(
                        locations=[coords_from, coords_to],
                        color="green",
                        weight=line_thickness,  # Normalized line thickness
                        popup=f"{volume} SAF from {mill} to {airport}"
                    ).add_to(mill_airport_line_layer)

    print(mill_to_ref_volumes)

    # Add lines for mill-to-ref volumes (SAF)
    for i, row in mill_to_ref_volumes.iterrows():
        refinery = row['volumes']  # Get the name of the airport
        if refinery in refineries_lat_lon_dict:  # Ensure the airport exists in the latitude/longitude data
            coords_to = [refineries_lat_lon_dict[refinery]['Latitude'], refineries_lat_lon_dict[refinery]['Longitude']]
            for mill, volume in row[2:].items():
                volume = pd.to_numeric(volume, errors='coerce')
                if volume > 0 and mill in mills_lat_lon_dict:  # Ensure the mill exists in the latitude/longitude data
                    coords_from = [mills_lat_lon_dict[mill]['Latitude'], mills_lat_lon_dict[mill]['Longitude']]
                    # line_thickness = normalize_thickness(volume, min_saf_volume, max_saf_volume)
                    folium.PolyLine(
                        locations=[coords_from, coords_to],
                        color="purple",
                        weight=2,  # Normalized line thickness
                        popup=f"{volume} SAF from {mill} to {refinery}"
                    ).add_to(mill_to_ref_line_layer)

    # Add lines for mill-to-ref volumes (ethanol)
    for i, row in mill_to_ref_volumes_eth.iterrows():
        refinery = row['volumes']  # Get the name of the airport
        if refinery in refineries_lat_lon_dict:  # Ensure the airport exists in the latitude/longitude data
            coords_to = [refineries_lat_lon_dict[refinery]['Latitude'], refineries_lat_lon_dict[refinery]['Longitude']]
            for mill, volume in row[2:].items():
                volume = pd.to_numeric(volume, errors='coerce')
                if volume > 0 and mill in mills_lat_lon_dict:  # Ensure the mill exists in the latitude/longitude data
                    coords_from = [mills_lat_lon_dict[mill]['Latitude'], mills_lat_lon_dict[mill]['Longitude']]
                    # line_thickness = normalize_thickness(volume, min_saf_volume, max_saf_volume)
                    folium.PolyLine(
                        locations=[coords_from, coords_to],
                        color="blue",
                        weight=2,  # Normalized line thickness
                        popup=f"{volume} ethanol from {mill} to {refinery}"
                    ).add_to(mill_to_ref_eth_line_layer)

    print(ref_to_air_volumes)

    for i, row in ref_to_air_volumes.iterrows():
        airport = row['volumes']  # Get the name of the airport
        if airport in airports_lat_lon_dict:  # Ensure the airport exists in the latitude/longitude data
            coords_to = [airports_lat_lon_dict[airport]['Latitude'], airports_lat_lon_dict[airport]['Longitude']]
            for ref, volume in row[2:].items():
                volume = pd.to_numeric(volume, errors='coerce')
                if volume > 0 and ref in refineries_lat_lon_dict:  # Ensure the mill exists in the latitude/longitude data
                    coords_from = [refineries_lat_lon_dict[ref]['Latitude'], refineries_lat_lon_dict[ref]['Longitude']]
                    # line_thickness = normalize_thickness(volume, min_saf_volume, max_saf_volume)
                    folium.PolyLine(
                        locations=[coords_from, coords_to],
                        color="darkgreen",
                        weight=2,  # Normalized line thickness
                        popup=f"{volume} SAF from {ref} to {airport}"
                    ).add_to(ref_airport_line_layer)


    # Add layer control to toggle visibility of components
    LayerControl().add_to(m)

    # Add a legend to show the count of different types of mills and lines
    legend_html = f"""
    <div id="legend" style="position: fixed; bottom: 50px; left: 50px; width: 230px; height: 300px;
        background-color: rgba(255, 255, 255, 1); z-index:9999; font-size:14px;
        padding: 10px;">
        <h2>Legend</h2>
        <p><i class="fa fa-circle" style="color:green;"></i> Mills producing SAF ({total_mills_airport})</p>
        <p><i class="glyphicon glyphicon-play" style="color:blue;"></i>  Ethanol supplying Mills ({total_mills_mill})</p>
        <p><i class="glyphicon glyphicon-tint" style="color:lightblue;"></i> Unused Mills ({total_inactive_mills})</p>
        <p><i class="glyphicon glyphicon-stop" style="color:black;"></i> Refineries ({total_refs})</p>
        <p><i class="fa fa-plane" style="color:red;"></i> Airports ({total_airports})</p>
        <p><span style="background-color:blue; width:20px; height:5px; display:inline-block;"></span> Ethanol Supply</p>
        <p><span style="background-color:purple; width:20px; height:5px; display:inline-block;"></span> SAF Supply</p>
        <p><span style="background-color:darkgreen; width:20px; height:5px; display:inline-block;"></span> Blended SAF Supply</p>
        <button onclick="toggleLegend()" style="margin-top:10px;">Minimize</button>
    </div>

    <div id="legend-button" style="position: fixed; bottom: 55px; left: 55px; width: 20px; height: 20px;
        background-color: gray; z-index:10000; border-radius: 50%; display: none; cursor: pointer;" 
        onclick="toggleLegend()">
    </div>

    <script>
    function toggleLegend() {{
        var legend = document.getElementById('legend');
        var button = document.getElementById('legend-button');
        if (legend.style.display === 'none') {{
            legend.style.display = 'block';
            button.style.display = 'none';
        }} else {{
            legend.style.display = 'none';
            button.style.display = 'block';
        }}
    }}
    </script>
    """

    # Add the legend to the map
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save the map to an HTML file
    m.save(results_dir + '/mill_airport_map.html')

