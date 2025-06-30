import html
import re
from pathlib import Path

import pandas as pd

# Load the CSV with assigned categories
df = pd.read_csv("src/attribute_definitions_original.csv")

# Ensure output directory exists
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Group by category
grouped = df.groupby("Category")


def sanitize_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "_", text.replace(" ", "_"))


# Template parts for reuse
def build_html_header(title, include_search=False, include_back_to_top=False):
    header = """
<html>
<head>
<meta charset='utf-8'>
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 40px;
        background-color: #f9f9f9;
    }
    h2 {
        color: #333;
    }
    a {
        text-decoration: none;
        color: #004466;
        margin-right: 20px;
    }
    input[type="text"] {
        width: 300px;
        padding: 10px;
        margin: 20px 0;
        font-size: 16px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        background-color: #fff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    th, td {
        padding: 12px 16px;
        border: 1px solid #ddd;
        text-align: left;
        vertical-align: top;
    }
    th {
        background-color: #004466;
        color: #fff;
        position: sticky;
        top: 0;
        z-index: 1;
    }
    tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    tr:hover {
        background-color: #e6f7ff;
    }
    .container {
        overflow-x: auto;
    }
    #backToTopBtn {
        display: none;
        position: fixed;
        bottom: 40px;
        right: 40px;
        z-index: 99;
        font-size: 16px;
        border: none;
        outline: none;
        background-color: #333;
        color: white;
        cursor: pointer;
        padding: 10px 16px;
        border-radius: 8px;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
    }
    #backToTopBtn:hover {
        background-color: #555;
    }
</style>
"""
    if include_search or include_back_to_top:
        header += """
<script>
    function filterTable() {
        let input = document.getElementById("searchBox").value.toLowerCase();
        let rows = document.querySelectorAll("table tr:not(:first-child)");
        rows.forEach(row => {
            let text = row.textContent.toLowerCase();
            row.style.display = text.includes(input) ? "" : "none";
        });
    }

    window.onscroll = function() { scrollFunction(); };

    function scrollFunction() {
        let btn = document.getElementById("backToTopBtn");
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            btn.style.display = "block";
        } else {
            btn.style.display = "none";
        }
    }

    function topFunction() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
</script>
"""
    header += f"</head><body>\n<h2>{title}</h2>\n"
    if include_search:
        header += '<input type="text" id="searchBox" onkeyup="filterTable()" placeholder="Search attributes...">\n'
    return header


def build_html_table(data):
    # Define tone → background color
    tone_colors = {
        "Positive": "#d4edda",  # light green
        "Neutral": "#fff3cd",  # light yellow
        "Negative": "#f8d7da",  # light red/pink
    }

    table = """
<div class="container">
<table>
    <tr>
        <th>#</th>
        <th>Name</th>
        <th>Description</th>
    </tr>
"""
    for _, row in data.iterrows():
        tone = str(row.get("Tone", "")).capitalize()
        color = tone_colors.get(tone, "white")

        table += (
            "<tr>"
            f"<td>{int(row['#'])}</td>"
            f"<td style='background-color: {color}; font-weight: bold;'>{html.escape(row['Name'])}</td>"
            f"<td>{html.escape(str(row['Description']))}</td>"
            "</tr>\n"
        )
    table += "</table></div>\n"
    return table


# Build main HTML with search + links + full table + back to top
main_html = build_html_header(
    "TEW Worker Attributes and Definitions",
    include_search=True,
    include_back_to_top=True,
)

# Category Navigation
main_html += "<div style='margin-top: 20px;'><strong>Jump to Category:</strong></div>\n"
main_html += "<div style='margin-top: 10px; margin-bottom: 20px;'>\n"
for category in sorted(grouped.groups.keys()):
    if pd.notna(category):
        link = f"category_{sanitize_filename(category)}.html"
        main_html += f'<a href="{link}">{html.escape(category)}</a>\n'
main_html += "</div>\n"

# Main Table
main_html += build_html_table(df)

# Back to top button
main_html += '<button onclick="topFunction()" id="backToTopBtn" title="Go to top">⬆ Top</button>\n'
main_html += "</body></html>"

# Save main page
with open(
    output_dir / "index.html", "w", encoding="utf-8"
) as f:  ## maybe for nav purposes on Github pages, I need to call this one index.html
    f.write(main_html)

# Generate subcategory pages (simple)
for category, group in grouped:
    if pd.isna(category):
        continue
    sub_html = build_html_header(f"Category: {html.escape(category)}")
    sub_html += '<div><a href="index.html">← Back to Main Page</a></div><br>\n'
    sub_html += build_html_table(group)
    sub_html += "</body></html>"
    filename = f"category_{sanitize_filename(category)}.html"
    with open(output_dir / filename, "w", encoding="utf-8") as f:
        f.write(sub_html)
