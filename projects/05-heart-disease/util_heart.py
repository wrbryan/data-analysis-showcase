import pandas as pd

SEX_LABELS = {0: "Female", 1: "Male"}
CP_LABELS = {
    0: "Typical Angina",
    1: "Atypical Angina",
    2: "Non-anginal Pain",
    3: "Asymptomatic"
}
TARGET_LABELS = {0: "No Disease", 1: "Disease"}

CATEGORY_LABELS = {
    "sex": "Sex",
    "cp": "Chest Pain Type",
    "fbs": "Fasting Blood Sugar",
    "restecg": "Resting ECG",
    "exang": "Exercise-Induced Angina",
    "slope": "ST Slope",
    "ca": "Major Vessels (ca)",
    "thal": "Thalassemia",
    "target": "Heart Disease Outcome"
}

CATEGORY_VALUE_MAPS = {
    "sex": SEX_LABELS,
    "cp": CP_LABELS,
    "fbs": {0: "Normal", 1: "High (> 120 mg/dl)"},
    "restecg": {0: "Normal", 1: "ST-T Abnormality", 2: "LV Hypertrophy"},
    "exang": {0: "No", 1: "Yes"},
    "slope": {0: "Upsloping", 1: "Flat", 2: "Downsloping"},
    "thal": {0: "Unknown", 1: "Fixed Defect", 2: "Normal", 3: "Reversible Defect"},
    "target": TARGET_LABELS
}


def _get_filtered_df(path, sexes=None, cp_values=None):
    df = pd.read_csv(path)

    numeric_columns = [
        "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
        "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"
    ]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if sexes:
        df = df[df["sex"].isin(sexes)]
    if cp_values:
        df = df[df["cp"].isin(cp_values)]

    df["sex_label"] = df["sex"].map(SEX_LABELS).fillna("Unknown")
    df["cp_label"] = df["cp"].map(CP_LABELS).fillna("Unknown")
    df["target_label"] = df["target"].map(TARGET_LABELS).fillna("Unknown")

    for col in CATEGORY_LABELS:
        label_col = f"{col}_label"
        value_map = CATEGORY_VALUE_MAPS.get(col)
        if value_map:
            df[label_col] = df[col].map(value_map).fillna(df[col].astype("Int64").astype(str))
        else:
            df[label_col] = df[col].astype("Int64").astype(str)

    return df

def get_target_distribution(path, sexes=None, cp_values=None):
    df = _get_filtered_df(path, sexes, cp_values)
    return (
        df.groupby("target_label", as_index=False)["target"]
        .count()
        .rename(columns={"target": "count"})
    )


def get_category_options():
    return [{"label": label, "value": key} for key, label in CATEGORY_LABELS.items()]


def get_category_distribution(path, category, sexes=None, cp_values=None):
    df = _get_filtered_df(path, sexes, cp_values)
    category_label_col = f"{category}_label"
    result = (
        df.groupby(category_label_col, as_index=False)[category]
        .count()
        .rename(columns={category_label_col: "category_label", category: "count"})
        .sort_values("count", ascending=False)
    )
    return result


def get_target_by_category(path, category, sexes=None, cp_values=None):
    df = _get_filtered_df(path, sexes, cp_values)
    category_label_col = f"{category}_label"
    grouped = (
        df.groupby(category_label_col, as_index=False)
        .agg(
            cases=("target", "count"),
            disease_rate=("target", "mean")
        )
        .rename(columns={category_label_col: "category_label"})
    )
    grouped["disease_rate"] = grouped["disease_rate"] * 100
    return grouped.sort_values("disease_rate", ascending=False)


def get_full_data(path, sexes=None, cp_values=None):
    return _get_filtered_df(path, sexes, cp_values)


def get_cp_values(path, sexes=None):
    df = _get_filtered_df(path, sexes, None)
    values = sorted(df["cp"].dropna().astype(int).unique())
    return [int(v) for v in values]


def get_cp_grouped_data(path, sexes=None, cp_values=None):
    df = _get_filtered_df(path, sexes, cp_values)
    return (
        df.groupby("cp_label", as_index=False)
        .agg(
            avg_chol=("chol", "mean"),
            avg_trestbps=("trestbps", "mean"),
            avg_thalach=("thalach", "mean"),
            count=("cp", "count")
        )
        .sort_values("count", ascending=False)
    )

def get_sex_values(path):
    df = pd.read_csv(path)
    values = sorted(pd.to_numeric(df["sex"], errors="coerce").dropna().astype(int).unique())
    return [int(v) for v in values]