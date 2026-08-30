import pandas as pd

def get_grouped_data(PATH, manufacturers=None, models=None):
    df = pd.read_csv(PATH)
    df['Sales_in_thousands'] = pd.to_numeric(df['Sales_in_thousands'], errors='coerce')
    if manufacturers:
        if isinstance(manufacturers, list):
            df = df[df['Manufacturer'].isin(manufacturers)]
        elif manufacturers != 'All':
            df = df[df['Manufacturer'] == manufacturers]
    if models:
        if isinstance(models, list):
            df = df[df['Model'].isin(models)]
        elif models != 'All':
            df = df[df['Model'] == models]
    sales_sum = df.groupby("Manufacturer")["Sales_in_thousands"].sum().sort_values(ascending=False)
    sales_sum = sales_sum.reset_index()
    top = sales_sum.head(5)
    return top

def get_full_data(PATH, manufacturers=None, models=None):
    df = pd.read_csv(PATH)
    df['Sales_in_thousands'] = pd.to_numeric(df['Sales_in_thousands'], errors='coerce')
    df['Price_in_thousands'] = pd.to_numeric(df['Price_in_thousands'], errors='coerce')
    df['Horsepower'] = pd.to_numeric(df['Horsepower'], errors='coerce')
    df['Fuel_efficiency'] = pd.to_numeric(df['Fuel_efficiency'], errors='coerce')
    if manufacturers:
        if isinstance(manufacturers, list):
            df = df[df['Manufacturer'].isin(manufacturers)]
        elif manufacturers != 'All':
            df = df[df['Manufacturer'] == manufacturers]
    if models:
        if isinstance(models, list):
            df = df[df['Model'].isin(models)]
        elif models != 'All':
            df = df[df['Model'] == models]

    # Create abbreviated manufacturer names
    manufacturer_abbrev = {
        'Mercedes-Benz': 'MB',
        'Land Rover': 'LR',
        'Rolls-Royce': 'RR',
        'Aston Martin': 'AM',
        'Bentley': 'Bent',
        'Porsche': 'Porsch',
        'Volkswagen': 'VW',
        'Chevrolet': 'Chevy',
        'Chrysler': 'Chrys',
        'Oldsmobile': 'Olds',
        'Pontiac': 'Pont',
        'Saturn': 'Sat',
        'Lincoln': 'Linc',
        'Cadillac': 'Caddy',
        'Infiniti': 'Inf',
        'Lexus': 'Lex',
        'Acura': 'Acu',
        'Honda': 'Hon',
        'Toyota': 'Toy',
        'Nissan': 'Niss',
        'Mazda': 'Maz',
        'Subaru': 'Sub',
        'Mitsubishi': 'Mits',
        'Hyundai': 'Hyun',
        'Kia': 'Kia',
        'Volvo': 'Vol',
        'Saab': 'Saab',
        'Audi': 'Aud',
        'BMW': 'BMW',
        'Jaguar': 'Jag',
        'Ferrari': 'Ferr',
        'Lamborghini': 'Lamb',
        'Maserati': 'Mas',
        'Buick': 'Buick',
        'Dodge': 'Dodge',
        'Ford': 'Ford',
        'GMC': 'GMC',
        'Hummer': 'Humm',
        'Isuzu': 'Isuz',
        'Jeep': 'Jeep',
        'Mercury': 'Merc',
        'Plymouth': 'Plym',
        'Suzuki': 'Suz'
    }

    df['Manufacturer_Abbrev'] = df['Manufacturer'].map(manufacturer_abbrev).fillna(df['Manufacturer'])
    df['Model_Label'] = df['Manufacturer_Abbrev'] + ' ' + df['Model']

    return df


def get_models(PATH, manufacturers=None):
    df = pd.read_csv(PATH)
    if manufacturers:
        if isinstance(manufacturers, list):
            df = df[df['Manufacturer'].isin(manufacturers)]
        elif manufacturers != 'All':
            df = df[df['Manufacturer'] == manufacturers]
    return sorted(df['Model'].unique())


def get_models_grouped_data(PATH, manufacturers=None, models=None):
    df = pd.read_csv(PATH)
    df['Sales_in_thousands'] = pd.to_numeric(df['Sales_in_thousands'], errors='coerce')
    if manufacturers:
        if isinstance(manufacturers, list):
            df = df[df['Manufacturer'].isin(manufacturers)]
        elif manufacturers != 'All':
            df = df[df['Manufacturer'] == manufacturers]
    if models:
        if isinstance(models, list):
            df = df[df['Model'].isin(models)]
        elif models != 'All':
            df = df[df['Model'] == models]

    # Create abbreviated manufacturer names
    manufacturer_abbrev = {
        'Mercedes-Benz': 'MB',
        'Land Rover': 'LR',
        'Rolls-Royce': 'RR',
        'Aston Martin': 'AM',
        'Bentley': 'Bent',
        'Porsche': 'Porsch',
        'Volkswagen': 'VW',
        'Chevrolet': 'Chevy',
        'Chrysler': 'Chrys',
        'Oldsmobile': 'Olds',
        'Pontiac': 'Pont',
        'Saturn': 'Sat',
        'Lincoln': 'Linc',
        'Cadillac': 'Caddy',
        'Infiniti': 'Inf',
        'Lexus': 'Lex',
        'Acura': 'Acu',
        'Honda': 'Hon',
        'Toyota': 'Toy',
        'Nissan': 'Niss',
        'Mazda': 'Maz',
        'Subaru': 'Sub',
        'Mitsubishi': 'Mits',
        'Hyundai': 'Hyun',
        'Kia': 'Kia',
        'Volvo': 'Vol',
        'Saab': 'Saab',
        'Audi': 'Aud',
        'BMW': 'BMW',
        'Jaguar': 'Jag',
        'Ferrari': 'Ferr',
        'Lamborghini': 'Lamb',
        'Maserati': 'Mas',
        'Buick': 'Buick',
        'Dodge': 'Dodge',
        'Ford': 'Ford',
        'GMC': 'GMC',
        'Hummer': 'Humm',
        'Isuzu': 'Isuz',
        'Jeep': 'Jeep',
        'Mercury': 'Merc',
        'Plymouth': 'Plym',
        'Suzuki': 'Suz'
    }

    df['Manufacturer_Abbrev'] = df['Manufacturer'].map(manufacturer_abbrev).fillna(df['Manufacturer'])
    df['Model_Label'] = df['Manufacturer_Abbrev'] + ' ' + df['Model']

    sales_sum = df.groupby("Model_Label")["Sales_in_thousands"].sum().sort_values(ascending=False)
    sales_sum = sales_sum.reset_index()
    top = sales_sum.head(10)  # Show top 10 models to avoid too many slices
    return top

def get_manufacturers(PATH):
    df = pd.read_csv(PATH)
    return sorted(df['Manufacturer'].unique())