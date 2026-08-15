import pandas as pd
from datetime import datetime, timedelta
import textual
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import Container, Vertical
from textual.binding import Binding
import os
import sys
import argparse
import warnings

# shhhhh
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def perform_conversion(file_path, output_dir):
    try:
        df_raw = pd.read_excel(file_path, header=None)

        header_idx = None
        for i, row in df_raw.iterrows():
            if 'Meeting Patterns' in row.values:
                header_idx = i
                break

        if header_idx is None:
            return "Error: Could not find a row containing 'Meeting Patterns'."

        df = pd.read_excel(file_path, header=header_idx)
        events = []

        for _, row in df.iterrows():
            subject = str(row.get('Course Listing', row.get('Instructor', 'Course')))
            subject = subject.replace('nan', '').strip()
            instructor = str(row.get('Instructor', 'N/A')).replace('nan', '').strip()
            meeting_patterns = str(row.get('Meeting Patterns', ''))
            start_date_raw = row.get('Start Date')
            end_date_raw = row.get('End Date')

            if pd.isna(start_date_raw) or pd.isna(end_date_raw) or '|' not in meeting_patterns or subject == 'nan':
                continue

            try:
                start_date = pd.to_datetime(start_date_raw)
                end_date = pd.to_datetime(end_date_raw)
            except:
                continue

            parts = [p.strip() for p in meeting_patterns.split('|')]
            days_list = []
            start_time = ""
            end_time = ""
            location = ""

            for part in parts:
                if '/' in part:
                    days_list = [d.strip() for d in part.split('/')]
                elif '-' in part and ('AM' in part or 'PM' in part):
                    times = [t.strip() for t in part.split('-')]
                    if len(times) == 2:
                        start_time = times[0]
                        end_time = times[1]
                elif part in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                    days_list = [part]
                else:
                    location = part

            if not days_list:
                days_list = [start_date.strftime('%A')]

            current_date = start_date
            while current_date <= end_date:
                day_name = current_date.strftime('%A')
                if day_name in days_list:
                    events.append({
                        'Subject': f"{subject} ({instructor})",
                        'Start Date': current_date.strftime('%m/%d/%Y'),
                        'Start Time': start_time,
                        'End Date': current_date.strftime('%m/%d/%Y'),
                        'End Time': end_time,
                        'Description': f"Instructor: {instructor}",
                        'Location': location
                    })
                current_date += timedelta(days=1)

        if events:
            output_df = pd.DataFrame(events)
            cols = ['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'Description', 'Location']
            output_df = output_df[cols]

            output_file = os.path.join(output_dir, 'google_calendar_import.csv')
            output_df.to_csv(output_file, index=False)
            return f"Success! Saved to: {output_file}\nEvents: {len(events)}"
        else:
            return "No events were identified."

    except Exception as e:
        return f"Error: {str(e)}"


class CalendarConverter(App):
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
    ]
    CSS = """
    Screen {
    background: $surface;
    }

    #main-container {
        padding: 1 2;
        margin: 1;
    }

    #input-section {
        layout: vertical;
        margin-bottom: 2;
    }

    Input {
        margin-bottom: 1;
    }

    #status-area {
        height: 1fr;
        border: solid $primary;
        padding: 1 2;
        background: $panel;
        color: $text-muted;
    }

    Button {
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            yield Static("Google Calendar Converter", id="title")
            with Vertical(id="input-section"):
                yield Input(placeholder="Excel File Path (e.g., View_My_Courses.xlsx)", id="file-path")
                yield Input(placeholder="Output Directory (e.g., .)", id="output-dir")
                yield Button("Convert to CSV", id="convert-btn")
            yield Static("", id="status-area")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "convert-btn":
            self.run_conversion()

    def run_conversion(self) -> None:
        file_path = self.query_one("#file-path").value
        output_dir = self.query_one("#output-dir").value
        status = self.query_one("#status-area")

        if not file_path or not output_dir:
            status.update("Error: Please provide both file path and output directory.")
            return

        status.update("Processing...")
        result = perform_conversion(file_path, output_dir)
        status.update(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Excel schedule to Google Calendar CSV.")
    parser.add_argument("input", nargs="?", help="Path to the input Excel file")
    parser.add_argument("output", nargs="?", help="Output directory")
    args = parser.parse_args()

    if args.input and args.output:
        result = perform_conversion(args.input, args.output)
        print(result)
    else:
        CalendarConverter().run()
