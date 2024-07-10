from datetime import datetime
import sqlite3
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd
import dash_auth
import os
from dash import dcc
from flask import Flask

# Function to convert hh:mm:ss to mm:ss format
def convert_to_mm_ss(timecode):
    parts = timecode.split(':')
    if len(parts) == 3:
        # Convert hours to minutes and add to existing minutes
        total_minutes = int(parts[0]) * 60 + int(parts[1])
        return f"{total_minutes:02}:{parts[2]}"
    elif len(parts) == 2:
        return timecode
    else:
        raise ValueError("Invalid timecode format")


# 1. List `.db` files in the current folder
db_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.db')]

# Define username and password pairs for authentication
VALID_USERNAME_PASSWORD_PAIRS = {
    'cdtestdevs': 'testing123!'
}

# Create the Flask server
flask_server = Flask(__name__)
flask_server.secret_key = '49727fb39994d242cd3bc90d2ee723e1'  # Set your secret key here

app = dash.Dash(__name__, server=flask_server, external_stylesheets=[dbc.themes.SPACELAB])

# Add authentication
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

db_path = 'cd_gpt3_5_definitions.db'
conn = sqlite3.connect(db_path)
query = "SELECT * FROM descriptions"  # Adjust if your table name or structure is different
df = pd.read_sql_query(query, conn)

conn.close()

app.layout = html.Div([

    html.Div([  # Container for video and DataTable
        html.Div([  # Video and Video ID Display
            html.Iframe(id='video-frame', src="https://www.youtube.com/embed/XC7BeLRm7ak",
                        width="480", height="360", style={'display': 'block', 'margin': 'auto'}),
            html.Br(),  # Space between the video and the video_id display

            # Dropdown for selecting database files
            dcc.Dropdown(
                id='db-selector',
                options=[{'label': db_name, 'value': db_name} for db_name in db_files],
                value=db_files[0],  # Default value is the first db file
                style={
                    'width': '50%',  # Set a fixed width
                    'maxWidth': '400px',  # Optional: You can also set a maximum width
                    'margin': '0 auto'  # Center the dropdown with auto margins
                }
            ),

            html.Div(id='video-id-display'),
            html.Br(),  # Space between the video_id display and the DataTable
        ], style={'flex': '3'}),  # Adjust the flex factor as needed

    ], style={'display': 'flex', 'flexDirection': 'row'}),

    html.Div([  # DataTable
        dash_table.DataTable(
            id='descriptions-table',
            columns=[
                {"name": i, "id": i, "editable": True if i in ['start_timecode', 'end_timecode'] else False}
                for i in df.columns if i != 'document_name'
            ],
            data=df.to_dict('records'),
            editable=True,
            filter_action="native",
            sort_action="native",
            sort_mode='multi',
            selected_rows=[],
            page_action='native',
            page_current= 0,
            page_size=len(df),
            fixed_rows={'headers': True},
            style_table={'overflowY': 'scroll', 'maxHeight': '500px', 'overflowX': 'scroll',
                         'width': '100%', 'minWidth': '100%'},
            style_cell={'height': '32px', 'textAlign': 'left', 'padding': '5px',
                        'overflow': 'hidden', 'textOverflow': 'ellipsis'},
            style_cell_conditional=[{'if': {'column_id': c}, 'maxWidth': '200px'} for c in df.columns],
        )
    ], style={'width': '100%'})
], style={'padding': '20px'})


@app.callback(
    Output('descriptions-table', 'data'),
    [Input('db-selector', 'value')]
)
def update_table(selected_db):
    # Connect to the new database
    conn = sqlite3.connect(selected_db)
    query = "SELECT * FROM descriptions"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Update and return the new data for the DataTable
    return df.to_dict('records')

@app.callback(
    Output('video-frame', 'src'),
    [Input('descriptions-table', 'active_cell'),
     Input('descriptions-table', 'derived_virtual_data')]
)
def update_video_src(active_cell, derived_virtual_data):
    if not active_cell or not derived_virtual_data:
        return dash.no_update

    active_row_index = active_cell['row']
    active_row = derived_virtual_data[active_row_index]

    video_id = active_row.get('video_id')
    start_timecode = active_row.get('start_timecode').strip('[]')
    end_timecode = active_row.get('end_timecode').strip('[]')

    if not video_id or not start_timecode or not end_timecode:
        return dash.no_update

    # Convert start and end timecodes to mm:ss format if necessary
    start_timecode = convert_to_mm_ss(start_timecode)
    end_timecode = convert_to_mm_ss(end_timecode)

    # Split the converted timecodes to calculate total seconds
    start_minutes, start_seconds = map(int, start_timecode.split(':'))
    start_total_seconds = start_minutes * 60 + start_seconds

    end_minutes, end_seconds = map(int, end_timecode.split(':'))
    end_total_seconds = end_minutes * 60 + end_seconds

    # Append a unique timestamp to the URL to prevent caching
    timestamp = datetime.now().timestamp()
    new_src = f"https://www.youtube.com/embed/{video_id}?start={start_total_seconds}&end={end_total_seconds}&autoplay=1&rel=0&controls=1&modestbranding=1&{timestamp}"

    return new_src
@app.callback(
    Output('video-id-display', 'children'),
    [Input('descriptions-table', 'active_cell'),
     Input('descriptions-table', 'derived_virtual_data')]
)
def display_video_id_and_timecode(active_cell, derived_virtual_data):
    if active_cell and derived_virtual_data:
        # Get the index of the active cell's row
        row_idx = active_cell['row']
        # Get the data for the active row from the sorted/filtered table
        active_row = derived_virtual_data[row_idx]

        # Extract the video ID and start timecode from the active row
        video_id = active_row['video_id']
        start_timecode = active_row['start_timecode']

        # Return the formatted string with video ID and start timecode
        return f"Video ID: {video_id}, Start Timecode: {start_timecode}"
    
    # Default message when no cell is active
    return "Click on a table row to select a video clip and start/end timecodes."


# Run the Dash application
if __name__ == '__main__':
    app.run_server(debug=True)
server = app.server
