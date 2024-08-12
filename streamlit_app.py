import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import defaultdict
import io
import re

# Initialize session state for tracking plotting status and stored plots
if 'stored_plots' not in st.session_state:
    st.session_state.stored_plots = []
if 'is_plotting' not in st.session_state:
    st.session_state.is_plotting = False
if 'current_id' not in st.session_state:
    st.session_state.current_id = None

# Define a color palette with a range of colors
color_palette = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
    '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#1f77b4', '#ff7f0e',
    '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
]

# Function to extract data from the uploaded file
def extract_data(file):
    data = defaultdict(lambda: defaultdict(list))
    try:
        buffer = io.StringIO(file.read().decode('utf-8'))
        lines = buffer.readlines()

        can_id_pattern = re.compile(r'ID:\s*(0x[0-9A-Fa-f]+)')
        data_bytes_pattern = re.compile(r'Data Bytes:\s*(.*)')
        measurement_pattern = re.compile(r'(\w+):\s*(.*)')

        current_id = None
        for line in lines:
            id_match = can_id_pattern.search(line)
            if id_match:
                current_id = id_match.group(1)
                continue

            bytes_match = data_bytes_pattern.search(line)
            if bytes_match and current_id:
                data_bytes = bytes_match.group(1)
                values = [int(b, 16) for b in data_bytes.split()]
                data[current_id]['Data Bytes'].append(values)
                continue

            measurement_match = measurement_pattern.search(line)
            if measurement_match and current_id:
                key, value = measurement_match.groups()
                try:
                    value = float(value.replace('A', '').replace('rpm', '').replace('deg', '').replace('Nm', ''))
                except ValueError:
                    continue
                data[current_id][key].append(value)

    except Exception as e:
        st.error(f"Error reading the file: {e}")
    return data

# Function to plot data using Plotly
def plot_data(selected_id, selected_measurement, data, chart_type):
    st.session_state.is_plotting = True
    with st.spinner('Plotting data...'):
        # Simulate plotting time for demonstration
        import time
        time.sleep(2)
        
        if not selected_measurement:
            st.write("No measurement selected for plotting.")
            st.session_state.is_plotting = False
            return

        measurement = selected_measurement
        values = data[selected_id][measurement]
        if values:
            df = pd.DataFrame({
                'Index': list(range(len(values))),
                'Value': values
            })

            # Determine color for this plot
            color_index = len(st.session_state.stored_plots) % len(color_palette)
            color = color_palette[color_index]

            if chart_type == 'Line Chart':
                fig = px.line(df, x='Index', y='Value', title=f'Line Chart for {measurement}', 
                              line_shape='linear', color_discrete_sequence=[color])
            elif chart_type == 'Bar Chart':
                fig = px.bar(df, x='Index', y='Value', title=f'Bar Chart for {measurement}', 
                             color_discrete_sequence=[color])
            elif chart_type == 'Scatter Plot':
                fig = px.scatter(df, x='Index', y='Value', title=f'Scatter Plot for {measurement}', 
                                color_discrete_sequence=[color])
            elif chart_type == 'Area Chart':
                fig = px.area(df, x='Index', y='Value', title=f'Area Chart for {measurement}', 
                              color_discrete_sequence=[color])
            elif chart_type == 'Histogram':
                fig = px.histogram(df, x='Value', title=f'Histogram for {measurement}', 
                                   color_discrete_sequence=[color])
            elif chart_type == 'Box Plot':
                fig = px.box(df, y='Value', title=f'Box Plot for {measurement}', 
                             color_discrete_sequence=[color])
            elif chart_type == 'Heatmap':
                df['Index'] = df['Index'].astype(str)
                fig = px.density_heatmap(df, x='Index', y='Value', title=f'Heatmap for {measurement}', 
                                        color_continuous_scale='Viridis')
            elif chart_type == 'Pie Chart':
                df = df.groupby('Value').size().reset_index(name='Count')
                fig = px.pie(df, values='Count', names='Value', title=f'Pie Chart for {measurement}')
            else:
                st.write(f"Unsupported chart type: {chart_type}")
                st.session_state.is_plotting = False
                return

            fig.update_layout(width=700, height=400)

            # Store the plot in session state
            st.session_state.stored_plots.append(fig)
        
        st.session_state.is_plotting = False

# Main function to handle the Streamlit app logic
def main():
    st.set_page_config(layout="centered", page_icon="📈", page_title="CAN Bus Data Plotter")
    st.title("CAN Bus Data Plotter")

    uploaded_file = st.file_uploader("Upload a CAN bus data file", type="txt")

    if uploaded_file is not None:
        data = extract_data(uploaded_file)

        if data:
            unique_ids = list(data.keys())
            st.write("Unique CAN IDs:")
            st.write(sorted(unique_ids))

            selected_id = st.selectbox("Select CAN ID to plot", unique_ids)
            
            # Check if selected ID has changed and clear stored plots if necessary
            if st.session_state.current_id != selected_id:
                st.session_state.stored_plots = []
                st.session_state.current_id = selected_id

            if selected_id:
                measurements = data[selected_id]
                measurement_names = [key for key in measurements.keys() if key != 'Data Bytes']
                
                st.write("Select measurement to plot:")
                selected_measurement = st.radio("Measurement", measurement_names, key="measurement_selection")

                chart_type = st.selectbox("Select chart type", [
                    'Line Chart', 'Bar Chart', 'Scatter Plot', 'Area Chart',
                    'Histogram', 'Box Plot', 'Heatmap', 'Pie Chart'
                ])

                if st.session_state.is_plotting:
                    st.write("Please wait, the graph is being plotted...")
                else:
                    if selected_measurement:
                        plot_data(selected_id, selected_measurement, data, chart_type)
                    else:
                        st.write("Select a measurement to plot.")

            # Display all stored plots
            if st.session_state.stored_plots:
                st.write("Previously plotted graphs:")
                for fig in st.session_state.stored_plots:
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No data found or file is empty.")

if __name__ == "__main__":
    main()
