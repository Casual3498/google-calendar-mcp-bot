"""Russian language date/time parser."""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
import pytz


class RussianDateParser:
    """Parser for Russian language date and time expressions."""
    
    # Day names in Russian
    WEEKDAYS = {
        'понедельник': 0, 'пн': 0,
        'вторник': 1, 'вт': 1,
        'среда': 2, 'ср': 2,
        'четверг': 3, 'чт': 3,
        'пятница': 4, 'пт': 4,
        'суббота': 5, 'сб': 5,
        'воскресенье': 6, 'вс': 6
    }
    
    # Relative day expressions
    RELATIVE_DAYS = {
        'сегодня': 0,
        'завтра': 1,
        'послезавтра': 2,
        'вчера': -1,
        'позавчера': -2
    }
    
    # Month names in Russian
    MONTHS = {
        'января': 1, 'январь': 1,
        'февраля': 2, 'февраль': 2,
        'марта': 3, 'март': 3,
        'апреля': 4, 'апрель': 4,
        'мая': 5, 'май': 5,
        'июня': 6, 'июнь': 6,
        'июля': 7, 'июль': 7,
        'августа': 8, 'август': 8,
        'сентября': 9, 'сентябрь': 9,
        'октября': 10, 'октябрь': 10,
        'ноября': 11, 'ноябрь': 11,
        'декабря': 12, 'декабрь': 12
    }
    
    def __init__(self, timezone: str = 'UTC'):
        self.tz = pytz.timezone(timezone)
    
    def parse_date(self, text: str) -> Optional[datetime]:
        """Parse date from Russian text.
        
        Args:
            text: Text containing date reference
            
        Returns:
            datetime object or None if parsing failed
        """
        text = text.lower().strip()
        now = datetime.now(self.tz)
        
        # Check relative days (сегодня, завтра, etc.)
        # Sort by length (longest first) to match "позавчера" before "вчера"
        for word, delta in sorted(self.RELATIVE_DAYS.items(), key=lambda x: len(x[0]), reverse=True):
            if word in text:
                result = now + timedelta(days=delta)
                import logging
                logging.getLogger(__name__).info(f"Matched relative day: '{word}' -> delta={delta}, result={result}")
                return result
        
        # Check weekdays
        for day_name, weekday in self.WEEKDAYS.items():
            if day_name in text:
                current_weekday = now.weekday()
                days_ahead = weekday - current_weekday
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return now + timedelta(days=days_ahead)
        
        # Check date format: "15 января", "15 января 2024"
        month_pattern = r'(\d{1,2})\s+(' + '|'.join(self.MONTHS.keys()) + r')(?:\s+(\d{4}))?'
        match = re.search(month_pattern, text)
        if match:
            day = int(match.group(1))
            month = self.MONTHS[match.group(2)]
            year = int(match.group(3)) if match.group(3) else now.year
            try:
                return datetime(year, month, day, tzinfo=self.tz)
            except ValueError:
                pass
        
        # Check numeric date formats
        # DD.MM.YYYY or DD.MM
        date_pattern = r'(\d{1,2})\.(\d{1,2})(?:\.(\d{4}))?'
        match = re.search(date_pattern, text)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else now.year
            try:
                return datetime(year, month, day, tzinfo=self.tz)
            except ValueError:
                pass
        
        # Check "через N дней/дня/день"
        days_pattern = r'через\s+(\d+)\s+(?:день|дня|дней)'
        match = re.search(days_pattern, text)
        if match:
            days = int(match.group(1))
            return now + timedelta(days=days)
        
        return None
    
    def parse_time(self, text: str) -> Optional[Tuple[int, int]]:
        """Parse time from Russian text.
        
        Args:
            text: Text containing time reference
            
        Returns:
            Tuple of (hour, minute) or None if parsing failed
        """
        text = text.lower().strip()
        
        # Pattern: "10:00", "10-00", "10.00"
        time_pattern = r'(\d{1,2})[:.-](\d{2})'
        match = re.search(time_pattern, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:
                return (hour, minute)
        
        # Pattern: "10 часов", "10 ч"
        hour_pattern = r'(\d{1,2})\s*(?:часов|часа|час|ч)(?:\s*(\d{1,2}))?'
        match = re.search(hour_pattern, text)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            if 0 <= hour < 24 and 0 <= minute < 60:
                return (hour, minute)
        
        return None
    
    def parse_datetime(self, text: str, default_duration: int = 60) -> Optional[Tuple[datetime, datetime]]:
        """Parse date and time from Russian text.
        
        Args:
            text: Text containing date and time references
            default_duration: Default event duration in minutes
            
        Returns:
            Tuple of (start_datetime, end_datetime) or None if parsing failed
        """
        date = self.parse_date(text)
        time = self.parse_time(text)
        
        if date is None:
            date = datetime.now(self.tz)
        
        if time is None:
            # Default to 9:00 if no time specified
            time = (9, 0)
        
        hour, minute = time
        start_dt = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        end_dt = start_dt + timedelta(minutes=default_duration)
        
        return (start_dt, end_dt)
    
    def parse_duration(self, text: str) -> int:
        """Parse duration from Russian text.
        
        Args:
            text: Text containing duration reference
            
        Returns:
            Duration in minutes (default 60 if not found)
        """
        text = text.lower().strip()
        
        # Pattern: "1 час", "2 часа", "30 минут"
        hour_pattern = r'(\d+)\s*(?:часов|часа|час|ч)'
        minute_pattern = r'(\d+)\s*(?:минут|минуты|минута|мин|м)'
        
        hours = 0
        minutes = 0
        
        hour_match = re.search(hour_pattern, text)
        if hour_match:
            hours = int(hour_match.group(1))
        
        minute_match = re.search(minute_pattern, text)
        if minute_match:
            minutes = int(minute_match.group(1))
        
        total_minutes = hours * 60 + minutes
        return total_minutes if total_minutes > 0 else 60
