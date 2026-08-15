# Google Calendar Converter

A Textual-based CLI tool to convert course schedule Excel files into CSV files compatible with Google Calendar imports.

## Features
- **Textual UI**: Interactive interface to select input files and output directories.
- **Pattern Parsing**: Automatically handles complex meeting patterns like `Monday/Tuesday 10:00AM-11:00AM | Room 101`.
- **Batch Processing**: Generates all instances of a course across its duration based on start and end dates.
- **Error Handling**: Validates file paths and handles missing headers gracefully.

## Prerequisites
- Python 3.8+
- `pandas`
- `openpyxl`
- `textual`

## Installation
```bash
pip install pandas openpyxl textual
```

## Usage
1. Run the script:
   ```bash
   python main.py
   ```
2. Enter the path to your `.xlsx` file when prompted.
3. Enter the directory where you want to save the `.csv` file.
4. Click the **Convert to CSV** button.

## Excel Requirements
The input Excel file should have a header row containing at least:
- **Course Listing** or **Instructor** (used for the event title)
- **Meeting Patterns** (e.g., `Monday/Tuesday 09:00AM-10:00AM | Room 101`)
- **Start Date**
- **End Date**

## Conversion Logic
The script parses the "Meeting Patterns" column:
- Splits by `|` to separate days, times, and locations.
- Handles `/` for multiple days (e.g., `Monday/Wednesday`).
- Handles `-` for time ranges (e.g., `09:00AM-10:00AM`).
- If no days are specified, it defaults to the day of the week for the Start Date.
