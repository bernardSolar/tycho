from datetime import datetime
import sqlite3

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import pandas as pd

def generate_tooltips(dataframe):
    return [
        {'description': {'value': str(row['description']), 'type': 'markdown'}}
        if 'description' in row else {}
        for row in dataframe.to_dict('records')
    ]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])
server = app.server

db_path = 'CLIPS_ALL_VIDEOS.db'
conn = sqlite3.connect(db_path)
query = "SELECT * FROM descriptions"  # Adjust if your table name or structure is different
df = pd.read_sql_query(query, conn)

conn.close()

tooltip_data = generate_tooltips(df)

app.layout = html.Div([
    html.Div([  # Container for video and DataTable
        html.Div([  # Video and Video ID Display
            html.Iframe(id='video-frame', src="https://www.youtube.com/embed/NNf8tXs1wbQ",
                        width="640", height="480", style={'display': 'block', 'margin': 'auto'}),
            html.Br(),  # Space between the video and the video_id display
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
            tooltip_data=tooltip_data,
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
    Output('video-frame', 'src'),
    [Input('descriptions-table', 'active_cell'),
     Input('descriptions-table', 'derived_virtual_data')]
)
def update_video_src(active_cell, derived_virtual_data):
    # Step 1: Check for Active Cell and Derived Virtual Data
    if not active_cell or not derived_virtual_data:
        return dash.no_update

    active_row_index = active_cell['row']
    active_row = derived_virtual_data[active_row_index]

    video_id = active_row.get('video_id')
    start_timecode = active_row.get('start_timecode').strip('[]')
    end_timecode = active_row.get('end_timecode').strip('[]')

    if not video_id or not start_timecode or not end_timecode:
        return dash.no_update

    minutes, seconds = map(int, start_timecode.split(':'))
    start_seconds = minutes * 60 + seconds

    minutes, seconds = map(int, end_timecode.split(':'))
    end_seconds = minutes * 60 + seconds

    # Append a unique timestamp to the URL to prevent caching
    timestamp = datetime.now().timestamp()
    new_src = f"https://www.youtube.com/embed/{video_id}?start={start_seconds}&end={end_seconds}&autoplay=1&rel=0&controls=1&modestbranding=1&{timestamp}"

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
    return "Click on a table row to display the video ID and start timecode."


# Run the Dash application
if __name__ == '__main__':
    app.run_server(debug=True)
