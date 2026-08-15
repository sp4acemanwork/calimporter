
import pandas as pd
from datetime import datetime, timedelta
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Button, Static
from textual.containers import Container, Vertical
from textual.binding import Binding
import os
import sys
import argparse
import warnings
import re

# shhhhh
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def parse_time_string(time_str, default_dt):
    """
    Parses a time string like '10:00AM' or '14:30' and returns a datetime object
    with the correct hour and minute, keeping the date from default_dt.
    """
    try:
        # Extract the hour and minute parts using regex
        # Matches numbers like 10, 00, 1, 30 etc.
        match = re.search(r'(\d{1,2}):(\d{2})', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))

            if 'PM' in time_str.upper() and hour < 12:
                hour += 12
            if 'AM' in time_str.upper() and hour == 12:
                hour = 0

            return default_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # Fallback for strings without colons like '10AM'
        match_no_colon = re.search(r'(\d{1,2})(AM|PM)?', time_str.upper())
        if match_no_colon:
            hour = int(match_no_colon.group(1))
            if 'PM' in match_no_colon.group(2) and hour < 12:
                hour += 12
            if 'AM' in match_no_colon.group(2) and hour == 12:
                hour = 0
            return default_dt.replace(hour=hour, minute=0, second=0, microsecond=0)

    except Exception:
        pass
    return default_dt


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


def perform_ics_conversion(file_path, output_dir):
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
        ics_content = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//CalendarConverter//EN"]

        day_map = {'Monday': 'MO', 'Tuesday': 'TU', 'Wednesday': 'WE', 'Thursday': 'TH', 'Friday': 'FR', 'Saturday': 'SA', 'Sunday': 'SU'}

        for _, row in df.iterrows():
            subject = str(row.get('Course Listing', row.get('Instructor', 'Course'))).replace('nan', '').strip()
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

            # Find first valid occurrence for DTSTART
            first_occurrence = None
            current_date = start_date
            while current_date <= end_date:
                if current_date.strftime('%A') in days_list:
                    first_occurrence = current_date
                    break
                current_date += timedelta(days=1)

            if not first_occurrence:
                continue

            # Use robust parsing for times
            dt_start = parse_time_string(start_time, first_occurrence)
            dt_end = parse_time_string(end_time, first_occurrence)

            # Ensure end time is at least 1 minute after start time if they are identical
            if dt_start == dt_end:
                dt_end += timedelta(minutes=1)

            # Format dates for ICS (YYYYMMDDTHHMMSSZ)
            # We assume UTC for simplicity in this converter
            dt_start_str = dt_start.strftime('%Y%m%dT%H%M%SZ')
            dt_end_str = dt_end.strftime('%Y%m%dT%H%M%SZ')

            # Construct RRULE
            by_days = ",".join([day_map[d] for d in days_list if d in day_map])
            # Format until string: YYYYMMDDT235900Z
            until_str = end_date.strftime('%Y%m%dT235900Z')

            ics_content.append("BEGIN:VEVENT")
            ics_content.append(f"SUMMARY:{subject} ({instructor})")
            ics_content.append(f"DTSTART:{dt_start_str}")
            ics_content.append(f"DTEND:{dt_end_str}")
            ics_content.append(f"RRULE:FREQ=WEEKLY;BYDAY={by_days};UNTIL={until_str}")
            ics_content.append(f"DESCRIPTION:Instructor: {instructor}")
            ics_content.append(f"LOCATION:{location}")
            ics_content.append("END:VEVENT")

        ics_content.append("END:VCALENDAR")

        output_file = os.path.join(output_dir, 'google_calendar_import.ics')
        with open(output_file, 'w') as f:
            f.write("\n".join(ics_content))

        return f"Success! Saved to: {output_file}\nEvents: {len(df)}"

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
                yield Button("Generate ICS (RRULE)", id="ics-btn")
            yield Static("", id="status-area")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "convert-btn":
            self.run_conversion()
        elif event.button.id == "ics-btn":
            self.run_ics_conversion()

    def run_conversion(self) -> None:
        file_path = self.query_one("#file-path").value
        output_dir = self.query_one("#output-dir").value
        status = self.query_one("#status-area")

        if not file_path or not output_dir:
            status.update("Error: Please provide both file path and output directory.")
            return

        status.update("Processing CSV...")
        result = perform_conversion(file_path, output_dir)
        status.update(result)

    def run_ics_conversion(self) -> None:
        file_path = self.query_one("#file-path").value
        output_dir = self.query_one("#output-dir").value
        status = self.query_one("#status-area")

        if not file_path or not output_dir:
            status.update("Error: Please provide both file path and output directory.")
            return

        status.update("Processing ICS (RRULE)...")
        result = perform_ics_conversion(file_path, output_dir)
        status.update(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Excel schedule to Google Calendar CSV or ICS.")
    parser.add_argument("input", nargs="?", help="Path to the input Excel file")
    parser.add_argument("output", nargs="?", help="Output directory")
    parser.add_argument("--ics", action="store_true", help="Generate ICS file instead of CSV")
    args = parser.parse_args()

    if args.input and args.output:
        if args.ics:
            result = perform_ics_conversion(args.input, args.output)
        else:
            result = perform_conversion(args.input, args.output)
        print(result)
    else:
        CalendarConverter().run()


