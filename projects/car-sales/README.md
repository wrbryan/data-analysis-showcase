# Car Sales Dashboard

An interactive car sales data visualization dashboard built with Python, Dash, and Plotly.

## Features

- **Interactive Filtering**: Filter data by manufacturer and specific models
- **Multiple Chart Types**:
  - Pie chart showing top models by sales
  - Vertical bar chart of model sales
  - Horizontal bar chart of model sales
  - Scatter plot of horsepower vs fuel efficiency with model labels
- **Responsive Design**: Built with Dash Bootstrap Components for clean, modern UI
- **Real-time Updates**: Charts update dynamically based on filter selections

## Data

The dashboard uses car sales data including:
- Manufacturer and model information
- Sales figures (in thousands)
- Vehicle specifications (horsepower, fuel efficiency, etc.)
- Pricing data

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/car-sales-dashboard.git
cd car-sales-dashboard
```

2. Install dependencies:
```bash
pip install dash dash-bootstrap-components pandas plotly
```

3. Run the application:
```bash
python car_sales_app.py
```

4. Open your browser to `http://127.0.0.1:8050/`

## Usage

1. Select manufacturers from the dropdown to filter the data
2. Choose specific models from the auto-populated model dropdown
3. View the interactive charts that update based on your selections
4. Hover over data points for detailed information

## Project Structure

```
car_sales_project/
├── car_sales_app.py          # Main Dash application
├── util_car.py              # Data processing utilities
├── Car_sales.csv            # Dataset
├── components_car/          # Reusable chart components
│   ├── dropdown_car.py      # Filter dropdowns
│   ├── pie_car.py          # Pie chart component
│   ├── bar_car.py          # Vertical bar chart
│   ├── bar_h_car.py        # Horizontal bar chart
│   └── scatter_car.py      # Scatter plot
└── README.md               # This file
```

## Technologies Used

- **Dash**: Web framework for building data apps
- **Plotly**: Interactive charting library
- **Pandas**: Data manipulation and analysis
- **Dash Bootstrap Components**: UI components and styling