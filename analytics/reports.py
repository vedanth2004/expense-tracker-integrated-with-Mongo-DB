# analytics/reports.py
import io
import csv
import math
import datetime
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch

from database import mongo_manager
from analytics.ai_insights import AIInsights


# Helper: converts various date inputs to datetime
def _to_datetime(d):
    if d is None:
        return None
    if isinstance(d, str):
        try:
            return datetime.datetime.fromisoformat(d)
        except Exception:
            return datetime.datetime.strptime(d, "%Y-%m-%d")
    if isinstance(d, datetime.date) and not isinstance(d, datetime.datetime):
        return datetime.datetime.combine(d, datetime.time.min)
    return d  # already datetime


# Helper: format large numbers with commas
def _fmt(x):
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return str(x)


# Generate matplotlib charts and return PNG bytes
def _create_charts(exp_df: pd.DataFrame, inc_df: pd.DataFrame):
    imgs = {}

    # Chart 1: Expense by Category (pie)
    if not exp_df.empty:
        by_cat = exp_df.groupby("category")["amount"].sum().sort_values(ascending=False)
        plt.figure(figsize=(6, 4))
        # show only top 8 categories, aggregate rest as "Other"
        top = by_cat.head(8)
        others = by_cat.iloc[8:].sum() if len(by_cat) > 8 else 0
        if others > 0:
            top["Other"] = others
        plt.pie(top.values, labels=top.index, autopct="%1.1f%%", startangle=140)
        plt.title("Expense Distribution by Category")
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        imgs["pie"] = buf.getvalue()
        plt.close()
    else:
        imgs["pie"] = None

    # Chart 2: Monthly Expense Trend (line)
    if not exp_df.empty:
        tmp = exp_df.copy()
        tmp["month"] = tmp["date"].dt.to_period("M").dt.to_timestamp()
        monthly = tmp.groupby("month")["amount"].sum().reset_index()
        plt.figure(figsize=(8, 3.5))
        plt.plot(monthly["month"], monthly["amount"], marker="o", linewidth=2)
        plt.fill_between(monthly["month"], monthly["amount"], alpha=0.1)
        plt.title("Monthly Expense Trend")
        plt.xlabel("Month")
        plt.ylabel("Amount")
        plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:,.0f}"))
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        imgs["trend"] = buf.getvalue()
        plt.close()
    else:
        imgs["trend"] = None

    # Chart 3: Top Categories (bar)
    if not exp_df.empty:
        by_cat = exp_df.groupby("category")["amount"].sum().sort_values(ascending=False).head(10)
        plt.figure(figsize=(8, 3.5))
        by_cat.plot(kind="barh")
        plt.gca().invert_yaxis()
        plt.xlabel("Amount")
        plt.title("Top Spending Categories")
        plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        imgs["bar"] = buf.getvalue()
        plt.close()
    else:
        imgs["bar"] = None

    # Chart 4: Income vs Expense (bar)
    if not exp_df.empty or not inc_df.empty:
        total_exp = exp_df["amount"].sum() if not exp_df.empty else 0.0
        total_inc = inc_df["amount"].sum() if not inc_df.empty else 0.0
        plt.figure(figsize=(6, 3))
        categories = ["Income", "Expense"]
        values = [total_inc, total_exp]
        plt.bar(categories, values, color=["#2ca02c", "#d62728"])
        plt.title("Income vs Expense")
        plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        imgs["inc_exp"] = buf.getvalue()
        plt.close()
    else:
        imgs["inc_exp"] = None

    return imgs


class Reports:
    def generate_csv(self, user_id: str, start: Optional[datetime.date] = None, end: Optional[datetime.date] = None) -> bytes:
        start_dt = _to_datetime(start)
        end_dt = _to_datetime(end)
        expenses = mongo_manager.list_expenses(user_id, limit=100000)
        incomes = mongo_manager.list_income(user_id, limit=100000)

        def _in_range(row_date):
            if not row_date:
                return False
            dt = _to_datetime(row_date)
            if start_dt and dt < start_dt:
                return False
            if end_dt and dt > (end_dt + datetime.timedelta(days=1)):
                return False
            return True

        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow([
            "record_type", "date", "category_or_source", "amount", "currency", "note", "created_at"
        ])

        for r in expenses:
            rd = r.get("date")
            if (not start_dt and not end_dt) or _in_range(rd):
                writer.writerow([
                    "expense",
                    r.get("date"),
                    r.get("category", ""),
                    _fmt(r.get("amount", 0.0)),
                    r.get("currency", ""),
                    r.get("note", ""),
                    r.get("created_at", "")
                ])

        for r in incomes:
            rd = r.get("date")
            if (not start_dt and not end_dt) or _in_range(rd):
                writer.writerow([
                    "income",
                    r.get("date"),
                    r.get("source", ""),
                    _fmt(r.get("amount", 0.0)),
                    r.get("currency", ""),
                    "",
                    r.get("created_at", "")
                ])

        return out.getvalue().encode("utf-8")

    def generate_pdf(self, user_id: str, start: Optional[datetime.date], end: Optional[datetime.date]) -> bytes:
        start_dt = _to_datetime(start)
        end_dt = _to_datetime(end)
        expenses = mongo_manager.list_expenses(user_id, limit=100000)
        incomes = mongo_manager.list_income(user_id, limit=100000)

        exp_df = pd.DataFrame(expenses)
        inc_df = pd.DataFrame(incomes)
        if not exp_df.empty:
            exp_df["amount"] = exp_df["amount"].astype(float)
            exp_df["date"] = pd.to_datetime(exp_df["date"], errors="coerce")
        else:
            exp_df = pd.DataFrame(columns=["category", "amount", "date", "note", "currency"])
        if not inc_df.empty:
            inc_df["amount"] = inc_df["amount"].astype(float)
            inc_df["date"] = pd.to_datetime(inc_df["date"], errors="coerce")
        else:
            inc_df = pd.DataFrame(columns=["source", "amount", "date", "currency"])

        if start_dt:
            exp_df = exp_df[exp_df["date"] >= start_dt]
            inc_df = inc_df[inc_df["date"] >= start_dt]
        if end_dt:
            end_plus = end_dt + datetime.timedelta(days=1)
            exp_df = exp_df[exp_df["date"] < end_plus]
            inc_df = inc_df[inc_df["date"] < end_plus]

        total_exp = exp_df["amount"].sum() if not exp_df.empty else 0.0
        total_inc = inc_df["amount"].sum() if not inc_df.empty else 0.0
        balance = total_inc - total_exp
        imgs = _create_charts(exp_df, inc_df)

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=LETTER)
        width, height = LETTER
        margin = 40
        y = height - margin
        section_spacing = 20  # space between sections

        # --- COVER PAGE ---
        user = mongo_manager.get_user_by_id(user_id) or {}
        name = user.get("name", "User")

        c.setFont("Helvetica-Bold", 18)
        c.drawString(margin, y, f"Expense Tracker Report - {name}")
        y -= 25
        c.setFont("Helvetica", 11)
        range_text = f"Range: {start_dt.date() if start_dt else 'Beginning'} → {end_dt.date() if end_dt else 'Now'}"
        c.drawString(margin, y, range_text)
        y -= 16
        c.drawString(margin, y, f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        y -= 30

        c.setFont("Helvetica-Bold", 13)
        c.drawString(margin, y, "Summary Overview")
        y -= 18
        c.setFont("Helvetica", 11)
        c.drawString(margin, y, f"Total Income  : ₹{_fmt(total_inc)}")
        y -= 14
        c.drawString(margin, y, f"Total Expense : ₹{_fmt(total_exp)}")
        y -= 14
        c.drawString(margin, y, f"Balance       : ₹{_fmt(balance)}")
        y -= section_spacing

        # --- DASHBOARD CHARTS ---
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y, "Dashboard Charts")
        y -= 20

        def draw_chart(img_data, width_inch, height_inch, title=None, spacing=10):
            nonlocal y
            if not img_data:
                return
            chart_height = height_inch * inch + spacing
            if y - chart_height < 60:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 11)
            if title:
                c.setFont("Helvetica-Bold", 12)
                c.drawString(margin, y, title)
                y -= 14
            img = ImageReader(io.BytesIO(img_data))
            c.drawImage(img, margin, y - height_inch * inch, width=width_inch * inch, height=height_inch * inch, preserveAspectRatio=True, mask='auto')
            y -= chart_height + section_spacing  # extra spacing after chart

        chart_sequence = [
            ("Income vs Expense", imgs.get("inc_exp")),
            ("Expense Distribution by Category", imgs.get("pie")),
            ("Monthly Expense Trend", imgs.get("trend")),
            ("Top Spending Categories", imgs.get("bar")),
        ]

        for title, img_data in chart_sequence:
            draw_chart(img_data, width_inch=6.5, height_inch=2.6, title=title)

        # --- TRANSACTIONS ---
        def draw_table(title, df, fields):
            nonlocal y
            if y < 120:
                c.showPage()
                y = height - margin
            c.setFont("Helvetica-Bold", 13)
            c.drawString(margin, y, title)
            y -= 16
            c.setFont("Helvetica", 9)
            headers = [f.capitalize() for f in fields]
            x_pos = [margin, margin + 90, margin + 250, margin + 330, margin + 420]
            for i, h in enumerate(headers):
                c.drawString(x_pos[i], y, h)
            y -= 12
            for _, r in df.sort_values("date", ascending=False).iterrows():
                if y < 60:
                    c.showPage()
                    y = height - margin
                    c.setFont("Helvetica", 9)
                    # redraw table header
                    c.setFont("Helvetica-Bold", 13)
                    c.drawString(margin, y, title)
                    y -= 16
                    c.setFont("Helvetica", 9)
                    for i, h in enumerate(headers):
                        c.drawString(x_pos[i], y, h)
                    y -= 12
                date_s = r.get("date")
                if isinstance(date_s, pd.Timestamp):
                    date_s = date_s.strftime("%Y-%m-%d")
                c.drawString(x_pos[0], y, str(date_s))
                c.drawString(x_pos[1], y, str(r.get(fields[1], ""))[:25])
                c.drawRightString(x_pos[2] + 30, y, _fmt(r.get("amount", 0.0)))
                c.drawString(x_pos[3], y, str(r.get("currency", "")))
                if len(fields) > 4:
                    c.drawString(x_pos[4], y, str(r.get(fields[4], ""))[:40])
                y -= 11
            y -= section_spacing  # space after table

        draw_table("Expense Transactions", exp_df, ["date", "category", "amount", "currency", "note"])
        draw_table("Income Transactions", inc_df, ["date", "source", "amount", "currency"])

        # --- AI Insights ---
        if y < 120:
            c.showPage()
            y = height - margin
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin, y, "AI Insights Summary")
        y -= 20
        c.setFont("Helvetica", 10)

        ai = AIInsights()
        try:
            insight_text, insight_err = ai.analyze_finance(
                user_id,
                f"Summarize spending between {start_dt.date() if start_dt else 'beginning'} and {end_dt.date() if end_dt else 'now'} and give top 5 recommendations."
            )
            if insight_err:
                c.drawString(margin, y, f"AI unavailable: {insight_err}")
            else:
                wrap_width = 95
                for paragraph in insight_text.split("\n"):
                    for i in range(0, len(paragraph), wrap_width):
                        if y < 60:
                            c.showPage()
                            y = height - margin
                            c.setFont("Helvetica", 10)
                        c.drawString(margin, y, paragraph[i:i+wrap_width])
                        y -= 12
        except Exception as e:
            c.drawString(margin, y, f"AI Insights Error: {e}")

        c.save()
        buf.seek(0)
        return buf.getvalue()
