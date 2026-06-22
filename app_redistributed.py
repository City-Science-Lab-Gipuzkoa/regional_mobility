import dash
from dash import dcc, html, Input, Output, State
import dash_leaflet as dl
import geopandas as gpd
import json
import pandas as pd
import plotly.graph_objects as go
import flask
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import squarify
import io
import base64

comarcas_dict = {
    "ALTO_DEBA": pd.read_csv(f'input_data/comarcas_pueblos/ALTO_DEBA.csv'),
    "BAJO_DEBA": pd.read_csv(f'input_data/comarcas_pueblos/BAJO_DEBA.csv'),
    "BAJO_BIDASOA": pd.read_csv(f'input_data/comarcas_pueblos/BAJO_BIDASOA.csv'),
    "DONOSTIALDEA": pd.read_csv(f'input_data/comarcas_pueblos/DONOSTIALDEA.csv'),
    "GOIERRI": pd.read_csv(f'input_data/comarcas_pueblos/GOIERRI.csv'),
    "TOLOSALDEA": pd.read_csv(f'input_data/comarcas_pueblos/TOLOSALDEA.csv'),
    "UROLA KOSTA": pd.read_csv(f'input_data/comarcas_pueblos/UROLA_KOSTA.csv'),
}

roads_gdf = gpd.read_file(f'input_data/ERREPIDEAK_CARRETERAS/ERREPIDEAK_CARRETERAS.shp')
roads_gdf = roads_gdf.to_crs(epsg=4326)
roads_geojson = json.loads(roads_gdf.to_json())
for feature in roads_geojson["features"]:
    feature["properties"]["color"] = "rgb(255,0,0,1)"

with open(f'input_data/roads.json', "w") as json_file:
    json.dump(roads_geojson, json_file, indent=4)

gdf = gpd.read_file(f'input_data/comarcas_gipuzkoa_monoparte/comarcas_gipuzkoa_monoparte.shp')
# Esto le asigna al shapefile, en el apartado "sankey", el archivo csv correspondiente. De esta forma, al hacer click en una comarca, se cargará el archivo csv correspondiente.
comarc_to_csv = {
    "TOLOSALDEA": "tolosaldea_sankey.csv",
    "DONOSTIALDEA": "donostialdea_sankey.csv",
    "ALTO DEBA": "debagoiena_sankey.csv",
    "BAJO DEBA": "debabarrena_sankey.csv",
    "UROLA KOSTA": "urola_kosta_sankey.csv",
    "GOIERRI": "goierri_sankey.csv",
    "BAJO BIDASOA": "bidasoa_sankey.csv",
}
gdf["sankey"] = gdf["COMARCA"].map(comarc_to_csv).fillna(f"input_data/sankey_graphs/comarcas_sankey.csv")
gdf = gdf.to_crs(epsg=4326)
geojson_data = json.loads(gdf.to_json())

# default_sankey_file = "C:/Users/iazcarateu/Desktop/CSL@Gipuzkoa/regional_mobility/sankey_graphs/comarcas_sankey.csv"
data_global = pd.read_csv(f"input_data/data_global.csv")

radar_data = [4.99, 5.99, 5.98, 7.95, 6.68, 8.69, 7.68]

def road_style(feature):
    return {"color": feature["properties"].get("color", "yellow"), "weight": 2}

dist = 60

mapbox_style = ""
app = dash.Dash(__name__, external_stylesheets=['/assets/style.css'])

app.layout = html.Div([

    html.Div([
        dl.Map(center=[43.22, -2.07], zoom=10, children=[
            dl.TileLayer(url=mapbox_style, attribution="Mapbox", maxZoom=10),

            # Add comarca polygons
            dl.GeoJSON(data=geojson_data, id="geojson",
                       options={"interactive": True,
                       "style":{"fillColor": "lightblue", "color":"lightgrey", "weight": 3, "fillOpacity": 0.1}},
                       hoverStyle={"weight": 3, "color": "white", "fillOpacity": 0.5},
                        children=[dl.Tooltip(id="tooltip", className="custom-tooltip")]
                       ),


            # Add roads layer
            dl.GeoJSON(
                data=roads_geojson, 
                id="roads-geojson",
                options={"interactive": False},
                # style=road_style,
                # # style=lambda feature: {"color": feature["properties"]["color"], "weight": 2},
                style={"color": feature["properties"].get("color", "yellow"),
                "weight": 1}
            ),
            # # Add roads layer
            # dl.GeoJSON(
            #     id="roads-geojson",
            #     options={"interactive": False}
            # ),

        ], style={'position': 'absolute', 'top': '0', 'left': '0', 'width': '100vw', 'height': '100vh', 'zIndex': '0'}),

    ]),

    html.Div([
        html.H2("30’ Gipuzkoa", style={'textAlign': 'right', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '70px'}),
        # html.Hr(style={'width': '50%', 'border': '1px solid white', 'margin': '5px auto', 'marginTop': '-25px'}),
        # html.H2("2025 ··· 2050", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '25px'}),
        html.H2("Join us in redefining the future of regional mobility", style={'textAlign': 'right', 'marginTop': '-50px', 'fontFamily': 'Arial', 'fontSize': '12px', 'fontStyle': 'italic'}),
    ], style={
        'position': 'absolute', 'top': '20px', 'left': '100px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center'
    }),

    # Button to reset Sankey to default
    html.Button([
        html.Img(
            src="/assets/gipuzkoa.png",  # Replace with your image path
            style={'width': '70px', 'marginRight': '-20px', 'marginLeft': '-20px', 'marginTop': '-5px', 'marginBottom': '-5px', 'verticalAlign': 'middle'}
        ),
    ],  id="reset-button", n_clicks=0, style={
        'position': 'absolute', 'top': '635px', 'left': '13%', 'transform': 'translateX(-50%)',
        'backgroundColor': 'black', 'color': 'white', 'padding': '10px 20px', 'fontSize': '16px',
        'border': '1px solid white', 'borderRadius': '5px', 'cursor': 'pointer', 'zIndex': '10'
    }),

    html.Div([
        dcc.Graph(id="sankey-graph", style={'width': '350px', 'height': '350px'})
    ], style={
        'position': 'absolute', 'bottom': '28%', 'left': '13%', 'transform': 'translateX(-50%)',
        'padding': '20px', 'borderRadius': '10px',
        'zIndex': '10', 'boxShadow': '2px 2px 10px rgba(0,0,0,0)'
    }),

    html.Div([
        dcc.Graph(id="treemap-graph", style={
            'width': '100%',
            'height': '100%',
            'backgroundColor': 'rgba(0,0,0,0)',  # Transparent background for graph
            'border': 'none',  # Remove border
            'padding': '0px',  # Remove padding
            'boxShadow': 'none',  # Remove any shadow if set
        })
    ], style={
        'position': 'absolute', 'bottom': '320px', 'left': '82%', 'transform': 'translateX(-50%)',
        'padding': '20px', 'borderRadius': '10px',
        'zIndex': '10', 'boxShadow': 'none',
        'backgroundColor': 'rgba(0,0,0,0)',
        # 📏 Ajustes de tamaño para hacerlo más pequeño
        'width': '360px',  # Reducido de 460px
        'height': '230px',  # Reducido de 300px

        # 📏 Ajustes mínimos y máximos para evitar que se haga muy grande o pequeño
        'minWidth': '260px',  
        'minHeight': '200px',  
        'maxWidth': '400px',  
        'maxHeight': '240px', 
        'overflow': 'hidden'  # Avoid any weird layout shifts
        # 'display': 'block',
    }),
    
    dcc.Store(id="tm_data", data={}),
    
    html.Div([
        dcc.Graph(id="radar-plot", style={'width': '650px', 'height': '650px'})
    ], style={
        'position': 'absolute', 'bottom': '-20%', 'left': '75%', 'transform': 'translateX(-50%)',
         'padding': '20px', 'borderRadius': '10px',
        'zIndex': '10', 'boxShadow': '2px 2px 10px rgba(0,0,0,0)'
    }),
    
    html.Button("Update Radar", id="dummy-input", style={'display': 'none'}),

    html.Img(
        src="/assets/collaborations_black.png",  # Place your image inside the 'assets' folder
        style={
            'position': 'absolute', 'bottom': '13px', 'left': '19%',  
            'width': '190px', 'height': 'auto', 'zIndex': '10'
        }
    ), 

    html.Img(
        src="/assets/Logo_black.png",  # Place your image inside the 'assets' folder
        style={
            'position': 'absolute', 'bottom': '-10px', 'left': '1%',  
            'width': '250px', 'height': 'auto', 'zIndex': '10'
        }
    ),

    ## CUADRADOS Y NOMBRES DE LAS INTERVENCIONES

    html.Div([
        html.H2("Designed by yourself:", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '25px'}),
    ], style={
        'position': 'absolute', 'top': f'calc(50px - {dist}px)', 'right': '440px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),

    html.Div([
        # Add any content you'd like inside the box here (for example, a title or description)
        html.H2(style={'color': 'white', 'fontSize': '30px', 'textAlign': 'center'}),
    ], style={
        'width': '200px',  # Adjust as needed
        'height': '100px',  # Adjust as needed
        'position': 'absolute',
        'top': f'calc(120px - {dist}px)',  # Adjust as needed
        'right': '430px',
        'transform': 'translateX(-50%)',
        'backgroundColor': 'rgba(0, 0, 0, 0.1)',  # High opacity black background
        'borderRadius': '15px',  # Round borders
        'border': '1px solid white',  # White border
        'padding': '20px',
        'zIndex': '5',  # Ensure it sits above the map and below the other content
    }),

    html.Div([
        # Add any content you'd like inside the box here (for example, a title or description)
        html.H2(style={'color': 'white', 'fontSize': '30px', 'textAlign': 'center'}),
    ], style={
        'width': '200px',  # Adjust as needed
        'height': '100px',  # Adjust as needed
        'position': 'absolute',
        'top': f'calc(120px - {dist}px)',  # Adjust as needed
        'right': '140px',
        'transform': 'translateX(-50%)',
        'backgroundColor': 'rgba(0, 0, 0, 0.1)',  # High opacity black background
        'borderRadius': '15px',  # Round borders
        'border': '1px solid white',  # White border
        'padding': '20px',
        'zIndex': '5',  # Ensure it sits above the map and below the other content
    }),

    html.Div([
        # Add any content you'd like inside the box here (for example, a title or description)
        html.H2(style={'color': 'white', 'fontSize': '30px', 'textAlign': 'center'}),
    ], style={
        'width': '120px',  # Adjust as needed
        'height': '100px',  # Adjust as needed
        'position': 'absolute',
        'top': f'calc(120px - {dist}px)',  # Adjust as needed
        'right': '-20px',
        'transform': 'translateX(-50%)',
        'backgroundColor': 'rgba(0, 0, 0, 0.1)',  # High opacity black background
        'borderRadius': '15px',  # Round borders
        'border': '1px solid white',  # White border
        'padding': '20px',
        'zIndex': '5',  # Ensure it sits above the map and below the other content
    }),

    html.Div([
        html.H2("30' Region", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px'}),
    ], 
    style={
        'position': 'absolute', 'top': f'calc(110px - {dist}px)', 'right': '510px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),
    html.Div([
        html.H2("On-Demand", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px'}),
        html.H2("PT System", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px', 'marginTop': '-10px'}),
    ], style={
        'position': 'absolute', 'top': f'calc(110px - {dist}px)', 'right': '390px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),
    html.Div([
        html.H2("LIFESTYLE", style={'textAlign': 'center', 'fontWeight': 'bold', 'fontStyle': 'italic', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px'}),
    ], style={
        'position': 'absolute', 'top': f'calc(215px - {dist}px)', 'right': '370px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),

    html.Div([
        html.H2("Industrial", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px'}),
        html.H2("Symbiosis", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px', 'marginTop': '-10px'}),
    ], 
    style={
        'position': 'absolute', 'top': f'calc(110px - {dist}px)', 'right': '220px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),
    html.Div([
        html.H2("Carpooling", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px'}),
    ], style={
        'position': 'absolute', 'top': f'calc(110px - {dist}px)', 'right': '100px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),
    html.Div([
        html.H2("WORK", style={'textAlign': 'center', 'fontWeight': 'bold', 'fontStyle': 'italic', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px'}),
    ], style={
        'position': 'absolute', 'top': f'calc(215px - {dist}px)', 'right': '70px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),

    html.Div([
        html.H2("EVs", style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px'}),
    ], style={
        'position': 'absolute', 'top': f'calc(110px - {dist}px)', 'right': '-85px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),
    html.Div([
        html.H2("ELECTRIFICATION", style={'textAlign': 'center', 'fontWeight': 'bold', 'fontStyle': 'italic', 'marginTop': '15px', 'fontFamily': 'Arial', 'fontSize': '13px'}),
    ], style={
        'position': 'absolute', 'top': f'calc(215px - {dist}px)', 'right': '-100px',
        'color': 'white',  # Styling
        'padding': '10px',
        'width': '430px', 'textAlign': 'center',
        'zIndex': '10',
    }),

    ## DROPDOWNS
        # Dropdown WORK
    html.Div([
        # Dropdown 1
        dcc.Dropdown(
            id='dropdown-simbiosis',
            options=[
                {'label': 'None', 'value': 'not_selected_simbiosis'},
                {'label': '+1000 workers', 'value': 'opt1_simb'},
                {'label': '+500 workers', 'value': 'opt2_simb'},
                {'label': '+200 workers', 'value': 'opt3_simb'}
            ],
            value='not_selected_simbiosis',
            clearable=False,
            style={
                'width': '100px',
                'fontSize': '14px',
                'borderRadius': '20px',  # Rounded corners
                'backgroundColor': 'rgba(173, 216, 230, 0.8)',  # Light blue with opacity
                'border': '2px solid #ADD8E6',  # Light blue border
                'color': 'black',  # Text color
                'padding': '0px',  # No padding
                'transition': 'all 0.3s ease',  # Smooth transition
                'textAlign': 'center',  # Center the text inside the dropdown
                'lineHeight': '15px',  # Reduced line height to make it thinner
                # 'marginTop': '10px',  # Space above the dropdown
            },
            className='cool-dropdown'
        ),

        # Dropdown 2
        dcc.Dropdown(
            id='dropdown-carpool',
            options=[
                {'label': 'None', 'value': 'not_selected_carpool'},
                {'label': '20%', 'value': 'opt1_pool'},
                {'label': '40%', 'value': 'opt2_pool'},
                {'label': '60%', 'value': 'opt3_pool'}
            ],
            value='not_selected_carpool',
            clearable=False,
            style={
                'width': '100px',
                'fontSize': '14px',
                'borderRadius': '20px',  # Rounded corners
                'backgroundColor': 'rgba(173, 216, 230, 0.8)',  # Light blue with opacity
                'border': '2px solid #ADD8E6',  # Light blue border
                'color': 'black',  # Text color
                'padding': '0px',  # No padding
                'transition': 'all 0.3s ease',  # Smooth transition
                'textAlign': 'center',  # Center the text inside the dropdown
                'lineHeight': '15px',  # Reduced line height to make it thinner
                # 'marginTop': '10px',  # Space above the dropdown
            },
            className='cool-dropdown'
        )
    ], style={
        'position': 'absolute',  # Position the dropdowns absolutely on the page
        'top': f'calc(180px - {dist}px)',  # Set the vertical position on the page
        'right': '270px',  # Set the horizontal position on the page (you can adjust this)
        'zIndex': '10',
        'display': 'flex',  # Use flex to align the dropdowns horizontally
        'alignItems': 'center',  # Vertically center the dropdowns
        'gap': '20px',  # Add some space between the dropdowns
    }),

    # Dropdown TECH
    html.Div([
        # Dropdown 1
        dcc.Dropdown(
            id='dropdown-ev',
            options=[
                {'label': 'None', 'value': 'not_selected_ev'},
                {'label': '20%', 'value': 'opt1_ev'},
                {'label': '40%', 'value': 'opt2_ev'},
                {'label': '60%', 'value': 'opt3_ev'}
            ],
            value='not_selected_ev',
            clearable=False,
            style={
                'width': '100px',
                'fontSize': '14px',
                'borderRadius': '20px',  # Rounded corners
                'backgroundColor': 'rgba(173, 216, 230, 0.8)',  # Light blue with opacity
                'border': '2px solid #ADD8E6',  # Light blue border
                'color': 'black',  # Text color
                'padding': '0px',  # No padding
                'transition': 'all 0.3s ease',  # Smooth transition
                'textAlign': 'center',  # Center the text inside the dropdown
                'lineHeight': '15px',  # Reduced line height to make it thinner
                # 'marginTop': '10px',  # Space above the dropdown
            },
            className='cool-dropdown'
        ),
    ], style={
        'position': 'absolute',  # Position the dropdowns absolutely on the page
        'top': f'calc(180px - {dist}px)',  # Set the vertical position on the page
        'right': '90px',  # Set the horizontal position on the page (you can adjust this)
        'zIndex': '10',
        'display': 'flex',  # Use flex to align the dropdowns horizontally
        'alignItems': 'center',  # Vertically center the dropdowns
        'gap': '20px',  # Add some space between the dropdowns
    }),

    # Dropdown LIFESTYLE
    html.Div([
        # Dropdown 1
        dcc.Dropdown(
            id='dropdown-30',
            options=[
                {'label': 'None', 'value': 'not_selected_30'},
                {'label': 'Basic Needs', 'value': 'opt1_30'},
                {'label': 'Basic Needs + Others', 'value': 'opt2_30'},
            ],
            value='not_selected_30',
            clearable=False,
            style={
                'width': '100px',
                'fontSize': '14px',
                'borderRadius': '20px',  # Rounded corners
                'backgroundColor': 'rgba(173, 216, 230, 0.8)',  # Light blue with opacity
                'border': '2px solid #ADD8E6',  # Light blue border
                'color': 'black',  # Text color
                'padding': '0px',  # No padding
                'transition': 'all 0.3s ease',  # Smooth transition
                'textAlign': 'center',  # Center the text inside the dropdown
                'lineHeight': '15px',  # Reduced line height to make it thinner
                # 'marginTop': '10px',  # Space above the dropdown
            },
            className='cool-dropdown'
        ),
        # Dropdown 2
        dcc.Dropdown(
            id='dropdown-ond',
            options=[
                {'label': 'None', 'value': 'not_selected_ond'},
                {'label': 'Level 1', 'value': 'opt1_ond'},
                {'label': 'Level 2', 'value': 'opt2_ond'},
            ],
            value='not_selected_ond',
            clearable=False,
            style={
                'width': '100px',
                'fontSize': '14px',
                'borderRadius': '20px',  # Rounded corners
                'backgroundColor': 'rgba(173, 216, 230, 0.8)',  # Light blue with opacity
                'border': '2px solid #ADD8E6',  # Light blue border
                'color': 'black',  # Text color
                'padding': '0px',  # No padding
                'transition': 'all 0.3s ease',  # Smooth transition
                'textAlign': 'center',  # Center the text inside the dropdown
                'lineHeight': '15px',  # Reduced line height to make it thinner
                # 'marginTop': '10px',  # Space above the dropdown
            },
            className='cool-dropdown'
        ),
    ], style={
        'position': 'absolute',  # Position the dropdowns absolutely on the page
        'top': f'calc(180px - {dist}px)',  # Set the vertical position on the page
        'right': '560px',  # Set the horizontal position on the page (you can adjust this)
        'zIndex': '10',
        'display': 'flex',  # Use flex to align the dropdowns horizontally
        'alignItems': 'center',  # Vertically center the dropdowns
        'gap': '20px',  # Add some space between the dropdowns
    }),

], style={'backgroundColor': 'black', 'overflow': 'hidden'})

## -------------------------------------- CALLBACKS -------------------------------------- ##


@app.callback(
    Output("radar-plot", "figure"),
    [
        Input("dropdown-simbiosis", "value"),
        Input("dropdown-carpool", "value"),
        Input("dropdown-ev", "value"),
        Input("dropdown-30", "value"),
        Input("dropdown-ond", "value"),
    ],
)
def update_radar(drop_simbiosis, drop_carpool, drop_ev, drop_30, drop_ond):
    global radar_data, data_global
    modified_radar_data = radar_data[:]
    co2 = modified_radar_data[0]
    air = modified_radar_data[1]
    health = modified_radar_data[2]
    live = modified_radar_data[3]
    access = modified_radar_data[4]
    non = modified_radar_data[5]
    local = modified_radar_data[6]

    s_co2, c_co2, lf_co2, ond_co2, ev_co2 = 1, 1, 1, 1, 1
    s_air, c_air, lf_air, ond_air, ev_air = 1, 1, 1, 1, 1
    s_health, c_health, lf_health, ond_health, ev_health = 1, 1, 1, 1, 1
    s_live, c_live, lf_live, ond_live, ev_live = 1, 1, 1, 1, 1
    s_access, c_access, lf_access, ond_access, ev_access = 1, 1, 1, 1, 1
    s_non, c_non, lf_non, ond_non, ev_non = 1, 1, 1, 1, 1
    s_local, c_local, lf_local, ond_local, ev_local = 1, 1, 1, 1, 1
    
    # SIMBIOSIS: CO2, AIR, CAR, HEALTH, LIVE, ACCESS, NON
    if drop_simbiosis == "non_selected_simbiosis":
        s_co2, s_air, s_health, s_live, s_access, s_non, s_local = 1, 1, 1, 1, 1, 1, 1
    elif drop_simbiosis == "opt1_simb":
        s_co2, s_air, s_health, s_live, s_access, s_non, s_local = 1.1, 1.05, 1.1, 1.1, 1.1, 1.1, 1
    elif drop_simbiosis == "opt2_simb":
        s_co2, s_air, s_health, s_live, s_access, s_non, s_local = 1.15, 1.1, 1.08, 1.08, 1.15, 1.1, 1
    elif drop_simbiosis == "opt3_simb":
        s_co2, s_air, s_health, s_live, s_access, s_non, s_local = 1.2, 1.15, 1.1, 1.16, 1.2, 1.15, 1
    
    # CARPOOL: CO2, AIR, CAR, HEALTH
    if drop_carpool == "non_selected_carpool":
        c_co2, c_air, c_health, c_live, c_access, c_non, c_local = 1, 1, 1, 1, 1, 1, 1
    elif drop_carpool == "opt1_pool":
        c_co2, c_air, c_health, c_live, c_access, c_non, c_local = 1.1, 1.1, 1.1, 1, 1, 1, 1
    elif drop_carpool == "opt2_pool":
        c_co2, c_air, c_health, c_live, c_access, c_non, c_local = 1.2, 1.15, 1.15, 1, 1, 1, 1
    elif drop_carpool == "opt3_pool":
        c_co2, c_air, c_health, c_live, c_access, c_non, c_local = 1.25, 1.22, 1.2, 1, 1, 1, 1

    #LIFESTYLE: CO2, AIR, CAR, HEALTH, LIVE, ACCESS, NON, LOCAL
    if drop_30 == "not_selected_30":
        lf_co2, lf_air, lf_health, lf_live, lf_access, lf_non, lf_local = 1, 1, 1, 1, 1, 1, 1
    elif drop_30 == "opt1_30":
        lf_co2, lf_air, lf_health, lf_live, lf_access, lf_non, lf_local = 1.08, 1.06, 1.08, 1.2, 1.1, 1.15, 1.2
    elif drop_30 == "opt2_30":
        lf_co2, lf_air, lf_health, lf_live, lf_access, lf_non, lf_local = 1.12, 1.08, 1.15, 1.3, 1.15, 1.2, 1.3

    #ON DEMAND: CO2, AIR, 
    if drop_ond == "not_selected_ond":
        ond_co2, ond_air, ond_health, ond_live, ond_access, ond_non, ond_local = 1, 1, 1, 1, 1, 1, 1
    elif drop_ond == "opt1_ond":
        ond_co2, ond_air, ond_health, ond_live, ond_access, ond_non, ond_local = 1.05, 1.05, 1.05, 1, 1.2, 1, 1.05
    elif drop_ond == "opt2_ond":
        ond_co2, ond_air, ond_health, ond_live, ond_access, ond_non, ond_local = 1.1, 1.1, 1.1, 1, 1.3, 1, 1.2

    #EV
    if drop_ev == "not_selected_ev":
        ev_co2, ev_air, ev_health, ev_live, ev_access, ev_non, ev_local = 1, 1, 1, 1, 1, 1, 1
    elif drop_ev == "opt1_ev":
        ev_co2, ev_air, ev_health, ev_live, ev_access, ev_non, ev_local = 1.1, 1.1, 1.1, 1, 1, 1, 1
    elif drop_ev == "opt2_ev":
        ev_co2, ev_air, ev_health, ev_live, ev_access, ev_non, ev_local = 1.2, 1.15, 1.15, 1, 1, 1, 1
    elif drop_ev == "opt3_ev":
        ev_co2, ev_air, ev_health, ev_live, ev_access, ev_non, ev_local = 1.3, 1.2, 1.2, 1, 1, 1, 1

    new_co2 = co2 * s_co2 * c_co2 * lf_co2 * ond_co2 * ev_co2
    new_air = air * s_air * c_air * lf_air * ond_air * ev_air
    new_health = health * s_health * c_health * lf_health * ond_health * ev_health
    new_live = live * s_live * c_live * lf_live * ond_live * ev_live
    new_access = access * s_access * c_access * lf_access * ond_access * ev_access
    new_non = non * s_non * c_non * lf_non * ond_non * ev_non
    new_local = local * s_local * c_local * lf_local * ond_local * ev_local
    
    modified_radar_data[0] = new_co2
    modified_radar_data[1] = new_air
    modified_radar_data[2] = new_health
    modified_radar_data[3] = new_live
    modified_radar_data[4] = new_access
    modified_radar_data[5] = new_non
    modified_radar_data[6] = new_local

    return generate_radar_chart(modified_radar_data)

# Function to Generate Radar Chart
def generate_radar_chart(radar_data):
    categories = [
        "Sustainable Mobility", "Air Quality", "Public Health", "Live-Work Harmony",
        "Access to Public Transit", "Non-Moving Time", "Local Business Growth"
    ]

    # Example Data (Replace with real data)
    site_changes_data = radar_data
    current_site_data = [4.99, 5.99, 5.98, 7.95, 6.68, 8.69, 7.68] # Uses the dynamic radar data

    # Close the shape
    site_changes_data += [site_changes_data[0]]
    current_site_data += [current_site_data[0]]
    categories += [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=current_site_data,
        theta=categories,
        fill='toself',
        name="Current Site",
        line=dict(color='rgba(255, 255, 255, 0)'),
        fillcolor='rgba(255, 255, 255, 0.5)'
    ))
    fig.add_trace(go.Scatterpolar(
        r=site_changes_data,
        theta=categories,
        mode='lines',
        name="Site with Changes",
        line=dict(color='yellow', width=2)
    ))

    fig.update_layout(
        polar=dict(
            bgcolor='black',
            radialaxis=dict(visible=True, showticklabels=False, gridcolor='gray', range=[0, 12]),
            angularaxis=dict(tickfont=dict(color="white"), gridcolor='gray')
        ),
        showlegend=True,
        legend=dict(
            font=dict(color="white"),
            x=-1.1,  # Moves legend to the right
            y=0.25,  # Moves legend to the bottom
            xanchor="left",
            yanchor="bottom",
        ),
        # paper_bgcolor='black',
        font=dict(color="white"),
        paper_bgcolor='rgba(0,0,0,0)',  # Fully transparent background
        plot_bgcolor='rgba(0,0,0,0)',  # Fully transparent plot area
        margin=dict(l=0, r=130, t=0, b=0)
    )

    return fig
    
@app.callback(
    [
        Output("sankey-graph", "figure"),
        Output("tm_data", "data"),
    ],
    [
        Input("geojson", "clickData"),
        Input("reset-button", "n_clicks"),
        State("sankey-graph", "figure"),
        Input("dropdown-simbiosis", "value"),  
        Input("dropdown-carpool", "value"),  
        Input("dropdown-ev", "value"),  
        Input("dropdown-30", "value"),  
        Input("dropdown-ond", "value"),  
    ],
)

def update_sankey(click_data, n_clicks, current_fig, drop_simbiosis, drop_carpool, drop_ev, drop_30, drop_ond):

    global data_global

    data_w = data_global[data_global['WORK'] == 1]
    data_nw = data_global[data_global['WORK'] == 0]
    # print(data_nw['cat'].value_counts())

    if drop_simbiosis == "not_selected_simb":
        data_w = data_w

    elif drop_simbiosis == "opt1_simb":

        filtered_data = data_w.sample(frac=0.2, random_state=42)

        # Iterar sobre el DataFrame filtrado
        for idx, row in filtered_data.iterrows():
            comarca = row['COMARCA_origen']
            # Verificar si el DataFrame de la comarca existe
            if comarca in comarcas_dict:
                comarca_df = comarcas_dict[comarca]
                
                # Filtrar para que 'name' no sea igual a 'name_origen'
                available_names = comarca_df[comarca_df['name_origen'] != row['name_origen']]['name_origen']
                
                if not available_names.empty:
                    new_name = np.random.choice(available_names.values)  # Seleccionar un nombre aleatorio
                    
                    # Asignar los nuevos valores
                    data_w.at[idx, 'name_destino'] = new_name
                    data_w.at[idx, 'COMARCA_destino'] = comarca
                    data_w.at[idx, 'cat'] = '<25'
                    data_w.at[idx, 'viajes_km'] = row['viajes'] * np.random.randint(2, 26)

    elif drop_simbiosis == "opt2_simb":
        filtered_data = data_w.sample(frac=0.3, random_state=42)

        # Iterar sobre el DataFrame filtrado
        for idx, row in filtered_data.iterrows():
            comarca = row['COMARCA_origen']
            # Verificar si el DataFrame de la comarca existe
            if comarca in comarcas_dict:
                comarca_df = comarcas_dict[comarca]
                
                # Filtrar para que 'name' no sea igual a 'name_origen'
                available_names = comarca_df[comarca_df['name_origen'] != row['name_origen']]['name_origen']
                
                if not available_names.empty:
                    new_name = np.random.choice(available_names.values)  # Seleccionar un nombre aleatorio
                    
                    # Asignar los nuevos valores
                    data_w.at[idx, 'name_destino'] = new_name
                    data_w.at[idx, 'COMARCA_destino'] = comarca
                    data_w.at[idx, 'cat'] = '<25'
                    data_w.at[idx, 'viajes_km'] = row['viajes'] * np.random.randint(2, 26)

    elif drop_simbiosis == "opt3_simb":

        filtered_data = data_w.sample(frac=0.5, random_state=42)

        # Iterar sobre el DataFrame filtrado
        for idx, row in filtered_data.iterrows():
            comarca = row['COMARCA_origen']
            # Verificar si el DataFrame de la comarca existe
            if comarca in comarcas_dict:
                comarca_df = comarcas_dict[comarca]
                
                # Filtrar para que 'name' no sea igual a 'name_origen'
                available_names = comarca_df[comarca_df['name_origen'] != row['name_origen']]['name_origen']
                
                if not available_names.empty:
                    new_name = np.random.choice(available_names.values)  # Seleccionar un nombre aleatorio
                    
                    # Asignar los nuevos valores
                    data_w.at[idx, 'name_destino'] = new_name
                    data_w.at[idx, 'COMARCA_destino'] = comarca
                    data_w.at[idx, 'cat'] = '<25'
                    data_w.at[idx, 'viajes_km'] = row['viajes'] * np.random.randint(2, 26)
    
    # OTHER

    if drop_30 == "not_selected_30":

        if drop_ond == "not_selected_ond":
            data_nw = data_nw
        elif drop_ond == "opt1_ond":

            # print(data_nw['cat'].value_counts())

            # Hacer que los de 'cat' <25, pasen de car a transit.
            mask = data_nw['cat'] == '<25'
            transferencia = data_nw.loc[mask, 'car'] * 0.3
            data_nw.loc[mask, 'car'] -= transferencia
            data_nw.loc[mask, 'transit'] += transferencia

        elif drop_ond == "opt2_ond": 

            # Hacer que los de 'cat' <25, pasen de car a transit.
            mask = data_nw['cat'] == '<25'
            transferencia = data_nw.loc[mask, 'car'] * 0.6
            data_nw.loc[mask, 'car'] -= transferencia
            data_nw.loc[mask, 'transit'] += transferencia
    
    elif drop_30 == "opt1_30":

        # Filtrar data_nw según las condiciones dadas
        filtered_data = data_nw[(data_nw['FREQUENT'] == 1) & (data_nw['cat'] == '>25')].copy()

        # Iterar sobre el DataFrame filtrado
        for idx, row in filtered_data.iterrows():
            comarca = row['COMARCA_origen']
            # Verificar si el DataFrame de la comarca existe
            if comarca in comarcas_dict:
                comarca_df = comarcas_dict[comarca]
                
                # Filtrar para que 'name' no sea igual a 'name_origen'
                available_names = comarca_df[comarca_df['name_origen'] != row['name_origen']]['name_origen']
                
                if not available_names.empty:
                    new_name = np.random.choice(available_names.values)  # Seleccionar un nombre aleatorio
                    
                    # Asignar los nuevos valores
                    data_nw.at[idx, 'name_destino'] = new_name
                    data_nw.at[idx, 'COMARCA_destino'] = comarca
                    data_nw.at[idx, 'cat'] = '<25'
                    data_nw.at[idx, 'viajes_km'] = row['viajes'] * np.random.randint(2, 26)

        if drop_ond == "not_selected_ond":
                data_nw = data_nw

        elif drop_ond == "opt1_ond":

            # Hacer que los de 'cat' <25, pasen de car a transit.
            mask = data_nw['cat'] == '<25'
            transferencia = data_nw.loc[mask, 'car'] * 0.3
            data_nw.loc[mask, 'car'] -= transferencia
            data_nw.loc[mask, 'transit'] += transferencia
        
        elif drop_ond == "opt2_ond": 

            # Hacer que los de 'cat' <25, pasen de car a transit.
            mask = data_nw['cat'] == '<25'
            transferencia = data_nw.loc[mask, 'car'] * 0.6
            data_nw.loc[mask, 'car'] -= transferencia
            data_nw.loc[mask, 'transit'] += transferencia

    elif drop_30 == "opt2_30":

        # LA DIFERENCIA ESTA AQUI. ANTES COGÍA TAMBIEN LOS DE FREQUENT 1, AHORA COJO TODOS. NO SOLO BASIC NEEDS, TAMBIEN OTROS DESTINOS.
        filtered_data = data_nw[(data_nw['cat'] == '>25')].copy()

        # Iterar sobre el DataFrame filtrado
        for idx, row in filtered_data.iterrows():
            comarca = row['COMARCA_origen']
            # Verificar si el DataFrame de la comarca existe
            if comarca in comarcas_dict:
                comarca_df = comarcas_dict[comarca]
                
                # Filtrar para que 'name' no sea igual a 'name_origen'
                available_names = comarca_df[comarca_df['name_origen'] != row['name_origen']]['name_origen']
                
                if not available_names.empty:
                    new_name = np.random.choice(available_names.values)  # Seleccionar un nombre aleatorio
                    
                    # Asignar los nuevos valores
                    data_nw.at[idx, 'name_destino'] = new_name
                    data_nw.at[idx, 'COMARCA_destino'] = comarca
                    data_nw.at[idx, 'cat'] = '<25'
                    data_nw.at[idx, 'viajes_km'] = row['viajes'] * np.random.randint(2, 26)
        
        if drop_ond == "not_selected_ond":

            data_nw = data_nw

        elif drop_ond == "opt1_ond":

            # Hacer que los de 'cat' <25, pasen de car a transit.
            mask = data_nw['cat'] == '<25'
            transferencia = data_nw.loc[mask, 'car'] * 0.3
            data_nw.loc[mask, 'car'] -= transferencia
            data_nw.loc[mask, 'transit'] += transferencia
        
        elif drop_ond == "opt2_ond": 

            # Hacer que los de 'cat' <25, pasen de car a transit.
            mask = data_nw['cat'] == '<25'
            transferencia = data_nw.loc[mask, 'car'] * 0.6
            data_nw.loc[mask, 'car'] -= transferencia
            data_nw.loc[mask, 'transit'] += transferencia


    ## PREPARE THE OUTPUT FILES
    
    # Juntar datasets data_w y data_nw
    df = pd.concat([data_w, data_nw], ignore_index=True)

    df_treemap = df.groupby(['cat'], as_index=False).agg({'viajes_km': 'sum'})
    df_json = df_treemap.to_json(orient='split')
    # data_for_table = df.to_dict("records")

    # Generar los datos para el Sankey, tanto el default, como los de las 7 comarcas
    comarcas_sankey = df.groupby(['COMARCA_origen', 'COMARCA_destino'], as_index=False).agg({'viajes': 'sum'})
    unique_comarcas = comarcas_sankey['COMARCA_origen'].unique()
    comarcas_sankey['COMARCA_origen'] = comarcas_sankey['COMARCA_origen'] + "_O"
    comarcas_sankey['COMARCA_destino'] = comarcas_sankey['COMARCA_destino'] + "_D"
    comarcas_sankey.to_csv(f'output_data/sankey_graphs_2/comarcas_sankey.csv')

    comarca_datasets = {}
    for comarca in unique_comarcas:
        comarca_datasets[comarca] = df[(df['COMARCA_origen'] == comarca) & (df['COMARCA_destino'] == comarca)]

    tolosaldea_dataset = comarca_datasets['TOLOSALDEA']
    tolosaldea_dataset['name_origen'] = tolosaldea_dataset['name_origen'] + "_O"
    tolosaldea_dataset['name_destino'] = tolosaldea_dataset['name_destino'] + "_D"
    tolosaldea_dataset = tolosaldea_dataset.groupby(['name_origen', 'name_destino'], as_index=False).agg({'viajes': 'sum'})
    tolosaldea_dataset.to_csv(f'output_datasankey_graphs_2/tolosaldea_sankey.csv')

    bidasoa_dataset = comarca_datasets['BAJO_BIDASOA']
    bidasoa_dataset['name_origen'] = bidasoa_dataset['name_origen'] + "_O"
    bidasoa_dataset['name_destino'] = bidasoa_dataset['name_destino'] + "_D"
    bidasoa_dataset = bidasoa_dataset.groupby(['name_origen', 'name_destino'], as_index=False).agg({'viajes': 'sum', 'car': 'sum', 'transit': 'sum', 'walk': 'sum'})
    bidasoa_dataset.to_csv(f'output_data/sankey_graphs_2/bidasoa_sankey.csv')

    urola_dataset = comarca_datasets['UROLA_KOSTA']
    urola_dataset['name_origen'] = urola_dataset['name_origen'] + "_O"
    urola_dataset['name_destino'] = urola_dataset['name_destino'] + "_D"
    urola_dataset = urola_dataset.groupby(['name_origen', 'name_destino'], as_index=False).agg({'viajes': 'sum'})
    urola_dataset.to_csv(f'output_data/sankey_graphs_2/urola_kosta_sankey.csv')

    debagoiena_dataset = comarca_datasets['ALTO_DEBA']
    debagoiena_dataset['name_origen'] = debagoiena_dataset['name_origen'] + "_O"
    debagoiena_dataset['name_destino'] = debagoiena_dataset['name_destino'] + "_D"
    debagoiena_dataset = debagoiena_dataset.groupby(['name_origen', 'name_destino'], as_index=False).agg({'viajes': 'sum'})
    debagoiena_dataset.to_csv(f'output_data/sankey_graphs_2/debagoiena_sankey.csv')

    goierri_dataset = comarca_datasets['GOIERRI']
    goierri_dataset['name_origen'] = goierri_dataset['name_origen'] + "_O"
    goierri_dataset['name_destino'] = goierri_dataset['name_destino'] + "_D"
    goierri_dataset = goierri_dataset.groupby(['name_origen', 'name_destino'], as_index=False).agg({'viajes': 'sum'})
    goierri_dataset.to_csv(f'output_data/sankey_graphs_2/goierri_sankey.csv')

    donostialdea_dataset = comarca_datasets['DONOSTIALDEA']
    donostialdea_dataset['name_origen'] = donostialdea_dataset['name_origen'] + "_O"
    donostialdea_dataset['name_destino'] = donostialdea_dataset['name_destino'] + "_D"
    donostialdea_dataset = donostialdea_dataset.groupby(['name_origen', 'name_destino'], as_index=False).agg({'viajes': 'sum'})
    donostialdea_dataset.to_csv(f'output_data/sankey_graphs_2/donostialdea_sankey.csv')

    debabarrena_dataset = comarca_datasets['BAJO_DEBA']
    debabarrena_dataset['name_origen'] = debabarrena_dataset['name_origen'] + "_O"
    debabarrena_dataset['name_destino'] = debabarrena_dataset['name_destino'] + "_D"
    debabarrena_dataset = debabarrena_dataset.groupby(['name_origen', 'name_destino'], as_index=False).agg({'viajes': 'sum'})
    debabarrena_dataset.to_csv(f'output_data/sankey_graphs_2/debabarrena_sankey.csv')

    # print(df.head())

    # ctx = dash.callback_context  # Check which input triggered the callback

    # triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # # If the reset button is clicked, reset to default Sankey
    # if triggered_id == "reset-button":
    #     return [
    #         generate_sankey_chart(f"output_data/sankey_graphs_2/comarcas_sankey.csv", "Trips in GIPUZKOA"),
    #         df_json
    #     ]

    # # If a dropdown is changed, keep the current figure (do NOT use click_data)
    # if triggered_id in ["dropdown-simbiosis", "dropdown-carpool", "dropdown-ev", "dropdown-30", "dropdown-ond"]:
    #     return [
    #         current_fig if current_fig else generate_sankey_chart(f"output_data/sankey_graphs_2/comarcas_sankey.csv", "Trips in GIPUZKOA"),
    #         df_json
    #     ]

    # # If a polygon is clicked, load its associated Sankey CSV
    # if click_data and "properties" in click_data:
    #     feature = click_data["properties"]
    #     sankey_file = feature.get("sankey", None)
    #     region_name = feature.get("COMARC_EUS", "Unknown Region")  # Get the region name from properties

    #     if sankey_file:
    #         sankey_path = f"output_data/sankey_graphs_2/{sankey_file}"
    #         return [
    #             generate_sankey_chart(sankey_path, f"Trips in {region_name}"),
    #             df_json
    #         ]  # Update the title with region name  

    # return [
    #     current_fig if current_fig else generate_sankey_chart(f"output_data/sankey_graphs_2/comarcas_sankey.csv", "Trips in GIPUZKOA"),
    #     df_json
    # ]

    """Updates the Sankey diagram based on polygon selection or reset button"""
    ctx = dash.callback_context

    # If button is clicked, reset to default Sankey
    if ctx.triggered and ctx.triggered[0]['prop_id'] == 'reset-button.n_clicks':
        return [
            generate_sankey_chart(f"output_data/sankey_graphs_2/comarcas_sankey.csv", "Trips in GIPUZKOA"),
            df_json
        ]

    # If a polygon is clicked, load its associated Sankey CSV
    if click_data and "properties" in click_data:
        feature = click_data["properties"]
        sankey_file = feature.get("sankey", None)
        region_name = feature.get("COMARC_EUS", "Unknown Region")  # Get the region name from properties
        
        if sankey_file:
            # print(sankey_file)
            sankey_path = f"output_data/sankey_graphs_2/{sankey_file}"
            return [
                generate_sankey_chart(sankey_path, f"Trips in {region_name}"),
                df_json
            ]  # Update the title with region name  
    
    return [
        current_fig if current_fig else generate_sankey_chart(f"output_data/sankey_graphs_2/comarcas_sankey.csv", "Trips in GIPUZKOA"), 
        df_json
    ]

def generate_sankey_chart(csv_file, title="Trips in GIPUZKOA"):
    """Generates a Sankey chart from a CSV file with an optional title"""
    try:
        df = pd.read_csv(csv_file)

        if 'name_origen' in df.columns:
            # Create node labels
            labels = list(pd.unique(df[['name_origen', 'name_destino']].values.ravel('K')))
            
            # Map nodes to indices
            source_indices = [labels.index(src) for src in df['name_origen']]
            target_indices = [labels.index(dst) for dst in df['name_destino']]
        else:
            # Create node labels
            labels = list(pd.unique(df[['COMARCA_origen', 'COMARCA_destino']].values.ravel('K')))
            
            # Map nodes to indices
            source_indices = [labels.index(src) for src in df['COMARCA_origen']]
            target_indices = [labels.index(dst) for dst in df['COMARCA_destino']]
        
        # Create Sankey diagram
        fig = go.Figure(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="white", width=0.5),
                label=labels
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=df['viajes']
            )
        ))

        # Set the title for the Sankey chart
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,  # Center title horizontally
                # y=1.2,  # Move title higher above the graph
                font=dict(size=20, color="white", family="Arial"),
                xanchor="center",
                yanchor="top"
            ),
            font=dict(color="white", size=12),  # Adjust text color for readability
            hoverlabel=dict(font=dict(color="white")),  # Keep hover text readable
            paper_bgcolor='rgba(0,0,0,0)',  # Fully transparent background
            plot_bgcolor='rgba(0,0,0,0)',  # Fully transparent plot area
            margin=dict(l=10, r=10, t=80, b=10)  # Reduce margins for better overlay
        )
        
        return fig

    except Exception as e:
        return {"data": [], "layout": {"title": f"Error loading CSV: {str(e)}"}}

@app.callback(
    Output("treemap-graph", "figure"),
    Input("tm_data", "data"),  
)

def update_treemap(df_json):
    if not df_json:
        return dash.no_update  # Avoids errors if df is empty

    df = pd.read_json(df_json, orient='split')
    print(df)
    # df = pd.DataFrame(data_for_table)

    # Ensure 'cat' and 'viajes' exist in the dataframe
    if 'cat' not in df.columns or 'viajes_km' not in df.columns:
        raise ValueError("Missing required columns: 'cat' and 'viajes_km'")

    color_map = {
        "<2": "rgb(144, 238, 144)",
        "<25": "rgb(173, 216, 230)",
        ">25": "rgb(255, 182, 193)"
    }

    # Crear el Treemap
    fig = px.treemap(
        df,
        path=['cat'],  # Agrupación basada en la columna 'cat'
        values="viajes_km",  # Tamaño de las cajas
        color="cat",  # Colorear según la categoría en 'cat'
        color_discrete_map=color_map  # Asignar colores específicos
    )

    fig.update_traces(
        tiling=dict(packing='squarify'),  # Use Squarify layout for treemap
        # tiling=dict(padding=5)
    )

    # Update layout for better visualization
    fig.update_layout(
        title=dict(
            text="Kms by Distance Mode",
            x=0.5,  # Centered title
            font=dict(size=20, color="white", family="Arial")
        ),
        font=dict(color="white", size=12),
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        plot_bgcolor='rgba(0,0,0,0)',  # Transparent plot area
        margin=dict(t=30, l=0, r=0, b=0),
        showlegend=False,  # Disable the legend
        xaxis=dict(showgrid=False, zeroline=False),  # Remove x-axis grid and zero line
        yaxis=dict(showgrid=False, zeroline=False),  # Remove y-axis grid and zero line
        coloraxis_colorbar=dict(
            title="",  # Nuevo título para la barra de color
            titlefont=dict(size=14, color="white"),  # Tamaño y color del título
            tickfont=dict(color="white")  # Color de los valores de la barra
        )
    )

    return fig

    # ------------------------------

    # fig = px.bar(
    #     df,
    #     x="cat",  # Categories on the x-axis
    #     y="viajes_km",  # Values (number of trips) on the y-axis
    #     color="viajes_km",  # Color intensity based on the number of trips
    #     color_continuous_scale="Blues",  # Choose a color scheme
    #     # labels={'cat': 'Category', 'viajes_km': 'Number of Trips'}  # Axis labels
    # )
    
    # # Update layout for transparency and aesthetics
    # fig.update_layout(
    #     title=dict(
    #         text="Kms per distance mode",
    #         x=0.5,  # Centered title
    #         font=dict(size=20, color="white", family="Arial")
    #     ),
    #     font=dict(color="white", size=12),
    #     paper_bgcolor='rgba(0,0,0,0)',  # Transparent background for the paper
    #     plot_bgcolor='rgba(0,0,0,0)',  # Transparent background for the plot area
    #     # showlegend=False,
    #     xaxis_title=None,  # Remove x-axis title
    #     yaxis_title=None,  # Remove y-axis title
    #     legend_title=None,  # Remove legend title
    # )

    # return fig

@app.callback(
    [
        Output("roads-geojson", "data"),
    ],
    [
        Input("dropdown-simbiosis", "value"),  
        Input("dropdown-carpool", "value"), 
        Input("dropdown-30", "value"),  
        Input("dropdown-ond", "value"),  
    ],
)

def update_roads(drop_simbiosis, drop_carpool, drop_life, drop_ondemand):

    updated_roads = roads_geojson.copy()

    if drop_simbiosis == "not_selected_simbiosis":
        return [updated_roads]
    elif drop_simbiosis == 'opt1_simb':
        # for feature in updated_roads["features"]:
        #     feature["properties"]["color"] = "rgb(255,255,0,1)"
        [feature["properties"].update({"color": "rgb(255,255,0,1)"}) for feature in updated_roads["features"]]

        with open(f'input_data/roads_2.json', "w") as json_file:
            json.dump(updated_roads, json_file, indent=4)
        return [updated_roads]

    return [updated_roads]

if __name__ == '__main__':
    # app.run_server(debug=True, dev_tools_ui=False, dev_tools_props_check=False)
    # app.run_server(debug=True)
    app.run(debug=True)