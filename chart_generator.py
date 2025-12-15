import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
import streamlit.components.v1 as components
import seaborn as sns
import streamlit as st

import plotly.express as px

def create_heat_map(input_df, yaxis_label, xaxis_labels):
    all_axis_labels = []
    all_axis_labels.append(yaxis_label)
    all_axis_labels.extend(xaxis_labels)

    filtered_df = input_df[all_axis_labels]
    df_heat = filtered_df.set_index(yaxis_label)

    # Numeric matrix
    matrix = df_heat.values.astype(float)
    num_rows = len(df_heat)
    row_height = 0.25 
    fig_height = num_rows * row_height

    fig, ax = plt.subplots(figsize=(6, fig_height))
    heatmap = ax.imshow(matrix, cmap=plt.cm.get_cmap("Blues"), vmin=0, vmax=1, aspect='auto')

    ax.set_xticks(np.arange(len(df_heat.columns)))
    ax.set_yticks(np.arange(len(df_heat.index)))
    ax.set_xticklabels(df_heat.columns)
    ax.set_yticklabels(df_heat.index)

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    # Annotate each cell with its value
    for i in range(len(df_heat.index)):
        for j in range(len(df_heat.columns)):
            ax.text(j, i, matrix[i, j], ha='center', va='center', color="black")
    
    plt.tight_layout()

    # Convert figure to PNG buffer
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")

    # HTML scrollable container with embedded image
    html_code = f"""
    <div style="height:500px; overflow-y:scroll; border:1px solid #ccc; padding:10px;">
        <img src="data:image/png;base64,{encoded}" style="width:100%; height:auto;" />
    </div>
    """

    components.html(html_code, height=520, scrolling=False)


def create_distribution_view(data, current_data, current_data_label,title, xlabel, ylabel ,showCumulative=False):
    plt.figure(figsize=(10, 4))
    sns.kdeplot(data, fill=True, cumulative=showCumulative, color="royalblue", alpha=0.6)
    plt.axvline(current_data, color="red", linestyle="--", label=current_data_label)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    st.pyplot(plt.gcf())
    plt.clf()

def create_line_chart(df):
    fig = px.line(df, x='Date', y=f'Close', title="Closing Price - Last 3 Months")
    st.plotly_chart(fig, use_container_width=True)