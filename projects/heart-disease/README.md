# Heart Disease Dashboard

An interactive heart disease data visualization dashboard built with Python, Dash, and Plotly.

## Features

- **Interactive Filtering**: Filter records by sex and chest pain type
- **Multiple Chart Types**:
  - Pie chart showing disease vs no-disease counts
  - Vertical bar chart of average cholesterol by chest pain type
  - Horizontal bar chart of average max heart rate by chest pain type
  - Scatter plot of age vs cholesterol by disease outcome
- **Responsive Design**: Built with Dash Bootstrap Components for clean, modern UI
- **Real-time Updates**: Charts update dynamically based on filter selections

## Data

The dashboard uses clinical heart dataset features including:
- Demographics (age, sex)
- Symptoms and ECG-related measures (cp, restecg, oldpeak, slope)
- Vital and lab-style indicators (trestbps, chol, thalach)
- Heart disease target outcome label

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/heart-disease-dashboard.git
cd heart-disease-dashboard
```

2. Install dependencies:
```bash
pip install dash dash-bootstrap-components pandas plotly
```

3. Run the application:
```bash
python heart_analysis_app.py
```

4. Open your browser to `http://127.0.0.1:8050/`

## Usage

1. Select sex categories from the dropdown to filter the data
2. Choose chest pain categories from the auto-populated dropdown
3. View the interactive charts that update based on your selections
4. Hover over data points for detailed information

## Project Structure

```
heart_disease_project/
├── heart_analysis_app.py    # Main Dash application
├── util_heart.py            # Data processing utilities
├── heart.csv                # Dataset
├── components_heart/        # Reusable chart components
│   ├── background_heart.py  # Background wrapper
│   ├── dropdown_heart.py    # Filter dropdowns
│   ├── pie_heart.py         # Disease distribution pie chart
│   ├── bar_heart.py         # Average cholesterol chart
│   ├── bar_h_heart.py       # Average max heart rate chart
│   └── scatter_heart.py     # Age vs cholesterol scatter plot
└── README.md               # This file
```

## Technologies Used

- **Dash**: Web framework for building data apps
- **Plotly**: Interactive charting library
- **Pandas**: Data manipulation and analysis
- **Dash Bootstrap Components**: UI components and styling