# ==============================================
# GenBF Kit Survey Results - Sankey Diagram Generator
# Feature: Load data from Excel table (compatible with old Plotly versions)
# Compatibility: Python 3.8+, Plotly 4.0+, Kaleido 0.2.1+, Pandas 1.3+
# ==============================================

# Step 1: Import libraries (with missing package prompts)
try:
    import plotly.graph_objects as go
    import pandas as pd
    import os
    from typing import List, Tuple, Dict

    print("✅ Required libraries imported successfully.")
except ImportError as e:
    missing_lib = str(e).split("No module named ")[-1].strip("'")
    print(f"❌ Missing library: {missing_lib}")
    print(f"ℹ️  Install command: pip install {missing_lib}")
    print("   Full environment setup: pip install plotly kaleido pandas openpyxl")
    exit()


# Step 2: Load and validate Excel table data
def load_excel_data(excel_path: str) -> Tuple[List[str], List[int], List[int], List[int], List[str]]:
    """
    Load survey data from Excel table and validate format.
    Args:
        excel_path: Path to your Excel file (e.g., "questionnaire_data.xlsx")
    Returns:
        labels: Node labels (questions + Yes/No)
        source: Flow start indices
        target: Flow end indices
        value: Flow values (respondent counts)
        node_colors: Colors for all nodes (questions + Yes/No)
    """
    # Check if Excel file exists
    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found at: {excel_path}")
        print("ℹ️  Please confirm the file path is correct (check folder structure).")
        exit()

    # Read Excel table (supports .xlsx format; use 'engine="xlrd"' for .xls)
    try:
        df = pd.read_excel(
            excel_path,
            engine="openpyxl",  # For .xlsx files (install with 'pip install openpyxl')
            header=0  # First row as column names
        )
        print(f"✅ Successfully loaded Excel file: {excel_path}")
    except Exception as e:
        print(f"❌ Failed to read Excel file: {str(e)}")
        print(
            "ℹ️  For .xls files, replace 'engine=\"openpyxl\"' with 'engine=\"xlrd\"' (install with 'pip install xlrd').")
        exit()

    # Validate required columns (ensure Excel has these columns)
    required_cols = ["Question", "Yes/1", "No/0", "Total_number"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"❌ Excel file missing required columns: {', '.join(missing_cols)}")
        print(f"ℹ️  Excel must have columns: {', '.join(required_cols)}")
        exit()

    # Validate data type and logic (prevent non-numeric counts)
    df["Yes/1"] = pd.to_numeric(df["Yes/1"], errors="coerce")
    df["No/0"] = pd.to_numeric(df["No/0"], errors="coerce")
    df["Total_number"] = pd.to_numeric(df["Total_number"], errors="coerce")

    # Check for NaN values (invalid numeric data)
    if df[["Yes/1", "No/0", "Total_number"]].isnull().any().any():
        print("❌ Excel has invalid data (non-numeric values in count columns).")
        print("ℹ️  Ensure 'Yes/1', 'No/0', 'Total_number' columns only contain numbers.")
        exit()

    # Check if Yes + No = Total (data consistency)
    df["Check_Total"] = df["Yes/1"] + df["No/0"]
    if not (df["Check_Total"] == df["Total_number"]).all():
        print("❌ Data inconsistency: Yes/1 + No/0 ≠ Total_number in some rows.")
        print("Inconsistent rows:")
        print(df[df["Check_Total"] != df["Total_number"]][["Question", "Yes/1", "No/0", "Total_number", "Check_Total"]])
        exit()

    # Extract core data from DataFrame
    question_labels = df["Question"].tolist()  # Get question names from "Question" column
    yes_counts = df["Yes/1"].tolist()  # Get Yes counts from "Yes/1" column
    no_counts = df["No/0"].tolist()  # Get No counts from "No/0" column
    num_questions = len(question_labels)

    # Define Yes/No endpoint labels (fixed)
    end_labels = ["Yes (Recognition)", "No (Non-recognition)"]
    all_labels = question_labels + end_labels  # All nodes: questions + Yes/No

    # Generate flow data (source → target → value)
    source: List[int] = []
    target: List[int] = []
    value: List[int] = []

    for i in range(num_questions):
        # Flow 1: Current question → Yes (Yes count)
        source.append(i)  # Question index (0,1,...,num_questions-1)
        target.append(num_questions)  # Yes endpoint index (fixed: last-1)
        value.append(int(yes_counts[i]))  # Cast to int (avoid float display)

        # Flow 2: Current question → No (No count)
        source.append(i)  # Question index
        target.append(num_questions + 1)  # No endpoint index (fixed: last)
        value.append(int(no_counts[i]))  # Cast to int

    # Define academic-friendly colors for each question (match your original color scheme)
    question_color_map: Dict[str, str] = {
        "Q_1": "#2300CA",  # Dark blue
        "Q_2": "#840097",  # Purple
        "Q_3": "#F5A0A3",  # Light pink
        "Q_4": "#F4DB00",  # Yellow
        "Q_5": "#26DB00",  # Bright green
        "Q_6": "#3176B5",  # Medium blue
        "Q_7": "#D40B11"  # Dark red
    }

    # Assign colors to questions (use default gray if question not in map)
    question_colors = []
    for q_label in question_labels:
        # Extract question ID (e.g., "Q_1" from "Q_1: No Change...")
        q_id = q_label.split(":")[0].strip() if ":" in q_label else q_label.strip()
        question_colors.append(question_color_map.get(q_id, "#808080"))  # Default: gray

    # Combine question colors + Yes/No colors
    node_colors = question_colors + ["#00BFA5", "#9E9E9E"]  # Yes: Teal, No: Light gray

    print(f"✅ Data validation passed: {num_questions} questions loaded.")
    return all_labels, source, target, value, node_colors


# Step 3: Helper function - Hex to RGBA (for link transparency)
def hex_to_rgba(hex_color: str, alpha: float = 0.5) -> str:
    """Convert 6-digit hex color to RGBA with adjustable transparency."""
    hex_color = hex_color.lstrip("#")
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
    except ValueError:
        print(f"⚠️  Invalid hex color: {hex_color}, using default gray instead.")
        return f"rgba(128, 128, 128, {alpha})"


# Step 4: Create and export Sankey diagram (compatible with old Plotly)
def create_sankey_from_excel(excel_path: str) -> str:
    """
    Main function to generate Sankey diagram from Excel data (old Plotly compatible).
    Returns: Path to output folder (for external reference)
    """
    # Load data from Excel
    labels, source, target, value, node_colors = load_excel_data(excel_path)

    # Generate link colors (inherit question colors with 50% transparency)
    link_colors: List[str] = []
    for s in source:
        # Link color = corresponding question's color (since source is question index)
        question_color = node_colors[s]
        link_colors.append(hex_to_rgba(question_color, alpha=0.5))

    # Create Sankey diagram (REMOVE 'labelfont' to fit old Plotly versions)
    fig = go.Figure(data=[go.Sankey(
        # Node configuration (old Plotly compatible: no 'labelfont' in node)
        node=dict(
            pad=25,  # Spacing between nodes (avoid label overlap)
            thickness=30,  # Node thickness (clear visual distinction)
            line=dict(
                color="black",  # Node border (sharp contrast)
                width=0.8  # Border width
            ),
            color=node_colors,  # Assign pre-defined colors
            label=labels  # Show node labels (from Excel "Question" column)
        ),

        # Link configuration (REMOVE 'labelfont' to fix error)
        link=dict(
            source=source,
            target=target,
            value=value,
            color=link_colors,
            label=[str(v) for v in value],  # Display respondent count on links (old Plotly supports 'label')
            hovertemplate=(
                "Question: %{source.label}<br>"
                "Response: %{target.label}<br>"
                "Respondents: %{label}<br>"
                "<extra></extra>"  # Hide default Plotly extra info
            )
        )
    )])

    # Layout optimization (global font setting for old Plotly)
    fig.update_layout(
        title=dict(
            text="GenBF Kit Functional Requirements Survey Results - Sankey Diagram",
            font=dict(family="Arial", size=16, weight="bold"),
            x=0.5,  # Center title
            y=0.98
        ),
        # Global font: controls all text (node labels, link labels) for old Plotly
        font=dict(
            family="Arial",
            size=10  # Readable size for all text (compatible with old versions)
        ),
        width=1300,  # Wide enough for long question labels
        height=750,  # Tall enough to avoid node overlap
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=100, r=100, t=120, b=100),  # Prevent label cutoff
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )

    # Export to multiple formats (create output folder)
    output_dir = "sankey_from_excel_output"
    os.makedirs(output_dir, exist_ok=True)

    # Export formats (academic use: SVG/PNG/PDF)
    export_configs = [
        ("svg", "vector (lossless, ideal for journals)", 2),
        ("png", "raster (300 DPI, presentations)", 3),
        ("pdf", "vector (academic submission standard)", 1),
        ("jpg", "compressed (reports)", 3)
    ]

    for fmt, desc, scale in export_configs:
        file_path = os.path.join(output_dir, f"GenBFKit_Sankey.{fmt}")
        try:
            fig.write_image(
                file_path,
                format=fmt,
                scale=scale,
                width=1300,
                height=750
            )
            print(f"✅ Exported {desc}: {file_path}")
        except Exception as e:
            print(f"❌ Failed to export {fmt}: {str(e)}")

    # Show interactive diagram
    print("\nℹ️  Opening interactive diagram in browser...")
    fig.show()

    # Return output directory path (for external reference)
    return output_dir


# Step 5: Run main function (configure Excel path here)
if __name__ == "__main__":
    print("=" * 60)
    print("GenBF Kit Sankey Diagram Generator (Excel Data Import)")
    print("=" * 60)

    # ---------------------- Configure Excel Path Here ----------------------
    # Note: "data/questionnaire_data.xlsx" means:
    # - There is a folder named "data" in the same directory as this script
    # - The Excel file is inside the "data" folder
    EXCEL_FILE_PATH = "data/questionnaire_data.xlsx"
    # ----------------------------------------------------------------------

    # Call function and get output directory path
    output_dir = create_sankey_from_excel(EXCEL_FILE_PATH)

    # Print completion message (now output_dir is valid)
    print(f"\n✅ Process completed! Check '{output_dir}' folder for files.")
    # Optional: Print full path of output folder (more user-friendly)
    full_output_path = os.path.abspath(output_dir)
    print(f"ℹ️  Full path of output folder: {full_output_path}")