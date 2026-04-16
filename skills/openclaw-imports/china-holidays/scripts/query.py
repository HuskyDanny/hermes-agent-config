#!/usr/bin/env python3
"""
中国法定节假日查询工具
数据来源: https://github.com/NateScarlet/holiday-cn
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Optional

HOLIDAY_DATA_URL = "https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json"

def get_holiday_data(year: int) -> dict:
    url = HOLIDAY_DATA_URL.format(year=year)
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e), "days": []}

def format_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return f"{date_str} ({weekdays[dt.weekday()]})"

def get_upcoming_holidays(days_ahead: int = 60) -> str:
    today = datetime.now()
    end_date = today + timedelta(days=days_ahead)
    
    years = {today.year}
    if end_date.year != today.year:
        years.add(end_date.year)
    
    holidays = []
    workdays = []
    
    for year in years:
        data = get_holiday_data(year)
        if "error" in data:
            continue
        for day in data.get("days", []):
            date_str = day["date"]
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if today <= dt <= end_date:
                info = {
                    "date": date_str,
                    "name": day.get("name", ""),
                    "is_off": day.get("isOffDay", False),
                    "formatted": format_date(date_str)
                }
                if info["is_off"]:
                    holidays.append(info)
                else:
                    workdays.append(info)
    
    output = [f"📅 未来 {days_ahead} 天节假日安排\n", f"今天: {today.strftime('%Y-%m-%d')}\n"]
    
    if holidays:
        output.append("\n🎉 放假安排:")
        current_holiday = None
        for h in sorted(holidays, key=lambda x: x["date"]):
            if current_holiday != h["name"]:
                current_holiday = h["name"]
                output.append(f"\n【{h['name']}】")
            output.append(f"  {h['formatted']}")
    else:
        output.append("\n😢 未来没有法定节假日")
    
    if workdays:
        output.append("\n\n💼 调休上班日:")
        for w in sorted(workdays, key=lambda x: x["date"]):
            output.append(f"  {w['formatted']} - {w['name']}调休")
    
    return "\n".join(output)

def is_workday(date_str: Optional[str] = None) -> str:
    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now()
        date_str = dt.strftime("%Y-%m-%d")
    
    data = get_holiday_data(dt.year)
    
    for day in data.get("days", []):
        if day["date"] == date_str:
            if day.get("isOffDay", False):
                return f"🎉 {date_str} 是【{day['name']}】放假"
            else:
                return f"💼 {date_str} 是【{day['name']}】调休上班日"
    
    if dt.weekday() >= 5:
        return f"😴 {date_str} 是普通周末休息日"
    else:
        return f"💼 {date_str} 是普通工作日"

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(is_workday(sys.argv[1]))
    else:
        print(get_upcoming_holidays())
