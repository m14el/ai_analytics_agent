"""
AI Analytics Agent — Google Sheets Integration
Exports analytics data to Google Sheets with formatting and charts.
"""
import logging
from typing import Dict, List, Optional
from config import settings

logger = logging.getLogger(__name__)


class GoogleSheetsExporter:
    def __init__(self):
        self.enabled = settings.google_sheets_enabled
        self.gc = None

    def _connect(self):
        if self.gc is None:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                settings.google_service_account_file, scope
            )
            self.gc = gspread.authorize(creds)

    def export_dashboard(self, summary: dict):
        """Export dashboard summary to Google Sheets."""
        if not self.enabled:
            logger.info("Google Sheets export disabled")
            return
        try:
            self._connect()
            try:
                sh = self.gc.open(settings.google_spreadsheet_name)
            except Exception:
                sh = self.gc.create(settings.google_spreadsheet_name)

            # Projects sheet
            self._write_projects_sheet(sh, summary.get("projects", []))
            # Stacks sheet
            self._write_stacks_sheet(sh, summary.get("stacks", []))
            logger.info("Google Sheets export completed")
        except Exception as e:
            logger.error(f"Google Sheets export failed: {e}")

    def _write_projects_sheet(self, sh, projects: list):
        try:
            ws = sh.worksheet("Проекты")
        except Exception:
            ws = sh.add_worksheet("Проекты", rows=100, cols=10)
        headers = ["Проект", "Стек", "Доход", "Расходы", "Прибыль", "Маржа %", "Статус"]
        rows = [headers]
        for p in projects:
            rows.append([
                p.get("project_name", ""), p.get("stack", ""),
                p.get("total_revenue", 0), p.get("total_costs", 0),
                p.get("profit", 0), p.get("margin", 0), p.get("status", ""),
            ])
        ws.update(rows, "A1")

    def _write_stacks_sheet(self, sh, stacks: list):
        try:
            ws = sh.worksheet("Стеки")
        except Exception:
            ws = sh.add_worksheet("Стеки", rows=50, cols=8)
        headers = ["Стек", "Проектов", "Доход", "Расходы", "Прибыль", "Маржа %", "Статус"]
        rows = [headers]
        for s in stacks:
            rows.append([
                s.get("stack", ""), s.get("project_count", 0),
                s.get("total_revenue", 0), s.get("total_costs", 0),
                s.get("profit", 0), s.get("margin", 0), s.get("status", ""),
            ])
        ws.update(rows, "A1")
