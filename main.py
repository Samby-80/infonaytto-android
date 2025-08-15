"""
Infonäyttö Pro - Complete Android Application
Main application file with all features integrated
"""

# main.py - This should be the main file for buildozer

import kivy
kivy.require('2.2.0')

from kivy.app import App
from kivy.clock import Clock
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore

# KivyMD imports
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.navigationdrawer import MDNavigationDrawer, MDNavigationDrawerMenu
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.list import OneLineListItem, MDList

import threading
import requests
import feedparser
import yfinance as yf
from datetime import datetime, timedelta, timezone
import zoneinfo
import json
import sqlite3
import os
from pathlib import Path

# Import our custom modules
from services import BackgroundService, NotificationManager, SettingsManager, DataManager
from services import ClockWidget, WeatherWidget

# Constants
WEEKDAYS_FI = ["Ma", "Ti", "Ke", "To", "Pe", "La", "Su"]
WEEKDAY_NAMES_FI = {
    "Monday": "Maanantai", "Tuesday": "Tiistai", "Wednesday": "Keskiviikko",
    "Thursday": "Torstai", "Friday": "Perjantai", "Saturday": "Lauantai", 
    "Sunday": "Sunnuntai"
}

WEATHER_ICONS = {
    "01d": "☀️", "01n": "🌙", "02d": "🌤️", "02n": "☁️",
    "03d": "☁️", "03n": "☁️", "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️", "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️", "13d": "❄️", "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️"
}

WEATHER_DESC_FI = {
    "01d": "Selkeä", "01n": "Selkeä", "02d": "Melko selkeä", "02n": "Melko selkeä",
    "03d": "Pilvistä", "03n": "Pilvistä", "04d": "Pilvistä", "04n": "Pilvistä",
    "09d": "Sadetta", "09n": "Sadetta", "10d": "Sadekuuroja", "10n": "Sadekuuroja",
    "11d": "Ukkosta", "11n": "Ukkosta", "13d": "Lunta", "13n": "Lunta",
    "50d": "Sumua", "50n": "Sumua"
}

FINNISH_HOLIDAYS = {
    (1, 1): "Uudenvuodenpäivä", (1, 6): "Loppiainen", (5, 1): "Vappu",
    (12, 6): "Itsenäisyyspäivä", (12, 24): "Jouluaatto", 
    (12, 25): "Joulupäivä", (12, 26): "Tapaninpäivä"
}

# Load name days
FINNISH_NAME_DAYS = {}
try:
    with open("nimipaivat.json", encoding="utf-8") as f:
        data = json.load(f)
        FINNISH_NAME_DAYS = {
            (int(item["month"]), int(item["day"])): ", ".join(item["names"])
            for item in data
        }
except Exception as e:
    print(f"Name days file not found: {e}")

class MainScreen(MDScreen):
    """Main dashboard screen with all info display components"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        
        # Initialize managers
        self.data_manager = DataManager()
        self.settings_manager = SettingsManager()
        
        # Build UI
        self.build_ui()
        
        # Start timers
        Clock.schedule_interval(self.update_time, 1)
        Clock.schedule_interval(self.update_data, 300)  # Every 5 minutes
        
        # Load initial data
        self.load_initial_data()
    
    def build_ui(self):
        """Build the complete user interface"""
        # Main layout
        main_layout = MDBoxLayout(orientation='vertical', spacing=5, padding=5)
        
        # Top toolbar
        toolbar = MDTopAppBar(
            title="Infonäyttö Pro",
            elevation=3,
            left_action_items=[["menu", lambda x: self.open_nav_drawer()]],
            right_action_items=[
                ["cog", lambda x: self.open_settings()],
                ["refresh", lambda x: self.refresh_all_data()],
                ["fullscreen", lambda x: self.toggle_fullscreen()]
            ]
        )
        main_layout.add_widget(toolbar)
        
        # Scrollable content
        scroll = MDScrollView()
        content = MDBoxLayout(orientation='vertical', spacing=10, 
                            adaptive_height=True, padding=10)
        
        # Time and date card
        self.time_card = self.create_time_card()
        content.add_widget(self.time_card)
        
        # Weather card
        self.weather_card = self.create_weather_card()
        content.add_widget(self.weather_card)
        
        # Horizontal layout for side panels and forecast
        horizontal_layout = MDBoxLayout(orientation='horizontal', spacing=10,
                                      size_hint_y=None, height=400)
        
        # Left side: World clocks and calendar
        left_panel = MDBoxLayout(orientation='vertical', spacing=10, 
                               size_hint_x=0.4)
        
        self.clocks_card = self.create_clocks_card()
        left_panel.add_widget(self.clocks_card)
        
        self.calendar_card = self.create_calendar_card()
        left_panel.add_widget(self.calendar_card)
        
        # Right side: Weather forecast
        self.forecast_card = self.create_forecast_card()
        
        horizontal_layout.add_widget(left_panel)
        horizontal_layout.add_widget(self.forecast_card)
        content.add_widget(horizontal_layout)
        
        # News and stocks
        self.news_card = self.create_news_card()
        content.add_widget(self.news_card)
        
        self.stocks_card = self.create_stocks_card()
        content.add_widget(self.stocks_card)
        
        scroll.add_widget(content)
        main_layout.add_widget(scroll)
        
        self.add_widget(main_layout)
    
    def create_time_card(self):
        """Create large time display card"""
        card = MDCard(size_hint_y=None, height=150, elevation=8,
                     md_bg_color=[0.07, 0.07, 0.07, 1])
        
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=5)
        
        self.time_label = MDLabel(
            text="--:--:--",
            theme_text_color="Custom",
            text_color=[0.69, 1, 0.62, 1],
            font_size="64dp",
            halign="center",
            bold=True
        )
        
        self.date_label = MDLabel(
            text="Ladataan...",
            theme_text_color="Primary",
            font_size="20dp",
            halign="center"
        )
        
        layout.add_widget(self.time_label)
        layout.add_widget(self.date_label)
        card.add_widget(layout)
        
        return card
    
    def create_weather_card(self):
        """Create current weather card"""
        card = MDCard(size_hint_y=None, height=200, elevation=8,
                     md_bg_color=[0.08, 0.08, 0.08, 1])
        
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Title
        title = MDLabel(text="🌤️ Säätiedot", font_size="18dp",
                       theme_text_color="Primary", halign="center", bold=True)
        layout.add_widget(title)
        
        # Weather content
        weather_layout = MDBoxLayout(orientation='horizontal', spacing=20,
                                   adaptive_height=True)
        
        # Temperature
        self.temp_label = MDLabel(
            text="--°C",
            theme_text_color="Custom",
            text_color=[0.56, 0.93, 0.56, 1],
            font_size="42dp",
            halign="center",
            bold=True,
            size_hint_x=0.4
        )
        
        # Description and details
        details_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.6)
        
        self.weather_icon = MDLabel(text="☀️", font_size="36dp", halign="center")
        self.weather_desc = MDLabel(text="Ladataan...", font_size="16dp",
                                  theme_text_color="Secondary", halign="center")
        self.weather_city = MDLabel(text="Helsinki", font_size="14dp",
                                  theme_text_color="Primary", halign="center")
        
        details_layout.add_widget(self.weather_icon)
        details_layout.add_widget(self.weather_desc)
        details_layout.add_widget(self.weather_city)
        
        weather_layout.add_widget(self.temp_label)
        weather_layout.add_widget(details_layout)
        
        layout.add_widget(weather_layout)
        card.add_widget(layout)
        
        return card
    
    def create_clocks_card(self):
        """Create world clocks card"""
        card = MDCard(size_hint_y=None, height=180, elevation=8,
                     md_bg_color=[0.08, 0.08, 0.08, 1])
        
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=8)
        
        title = MDLabel(text="🌍 Maailman ajat", font_size="16dp",
                       theme_text_color="Primary", halign="center", bold=True)
        layout.add_widget(title)
        
        self.clocks_layout = MDBoxLayout(orientation='vertical', spacing=3)
        layout.add_widget(self.clocks_layout)
        
        card.add_widget(layout)
        return card
    
    def create_calendar_card(self):
        """Create week calendar card"""
        card = MDCard(size_hint_y=None, height=200, elevation=8,
                     md_bg_color=[0.08, 0.08, 0.08, 1])
        
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=8)
        
        self.week_title = MDLabel(text="📅 Viikko --", font_size="16dp",
                                theme_text_color="Primary", halign="center", bold=True)
        layout.add_widget(self.week_title)
        
        self.calendar_layout = MDBoxLayout(orientation='vertical', spacing=2)
        layout.add_widget(self.calendar_layout)
        
        card.add_widget(layout)
        return card
    
    def create_forecast_card(self):
        """Create weather forecast card"""
        card = MDCard(size_hint_y=None, height=400, elevation=8, size_hint_x=0.6,
                     md_bg_color=[0.08, 0.08, 0.08, 1])
        
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=10)
        
        title = MDLabel(text="🌦️ Sääennuste", font_size="18dp",
                       theme_text_color="Primary", halign="center", bold=True)
        layout.add_widget(title)
        
        # Forecast grid
        self.forecast_layout = MDBoxLayout(orientation='horizontal', spacing=8)
        layout.add_widget(self.forecast_layout)
        
        card.add_widget(layout)
        return card
    
    def create_news_card(self):
        """Create news ticker card"""
        card = MDCard(size_hint_y=None, height=150, elevation=8,
                     md_bg_color=[1, 0.8, 0.82, 0.95])
        
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=8)
        
        title = MDLabel(text="📰 Uutiset", font_size="18dp",
                       theme_text_color="Custom", text_color=[0, 0, 0, 1],
                       halign="center", bold=True)
        layout.add_widget(title)
        
        # Scrollable news
        scroll = MDScrollView()
        self.news_layout = MDBoxLayout(orientation='vertical', spacing=3,
                                     adaptive_height=True)
        scroll.add_widget(self.news_layout)
        layout.add_widget(scroll)
        
        card.add_widget(layout)
        return card
    
    def create_stocks_card(self):
        """Create stocks ticker card"""
        card = MDCard(size_hint_y=None, height=150, elevation=8,
                     md_bg_color=[0.09, 0.09, 0.09, 1])
        
        layout = MDBoxLayout(orientation='vertical', padding=15, spacing=8)
        
        title = MDLabel(text="📈 Pörssikurssit", font_size="18dp",
                       theme_text_color="Primary", halign="center", bold=True)
        layout.add_widget(title)
        
        # Scrollable stocks
        scroll = MDScrollView()
        self.stocks_layout = MDBoxLayout(orientation='vertical', spacing=3,
                                       adaptive_height=True)
        scroll.add_widget(self.stocks_layout)
        layout.add_widget(scroll)
        
        card.add_widget(layout)
        return card
    
    def update_time(self, dt):
        """Update time display every second"""
        now = datetime.now()
        self.time_label.text = now.strftime("%H:%M:%S")
        
        # Update date once per minute
        if now.second == 0:
            day_name = WEEKDAY_NAMES_FI[now.strftime('%A')]
            self.date_label.text = f"{day_name} {now.strftime('%d.%m.%Y')}"
            self.update_world_clocks()
            self.update_calendar()
    
    def update_data(self, dt):
        """Update all data periodically"""
        threading.Thread(target=self._background_update, daemon=True).start()
    
    def _background_update(self):
        """Background data update"""
        try:
            # Update weather
            api_key = self.settings_manager.get('api_key')
            city = self.settings_manager.get('default_city', 'Helsinki')
            
            if api_key:
                weather_data = self.data_manager.fetch_weather_online(city, api_key)
                if weather_data:
                    Clock.schedule_once(lambda dt: self.update_weather_display(weather_data), 0)
            
            # Update other data sources
            self.update_news_data()
            self.update_stocks_data()
            
        except Exception as e:
            print(f"Background update error: {e}")
    
    def update_weather_display(self, weather_data):
        """Update weather UI elements"""
        if weather_data:
            self.temp_label.text = f"{weather_data['temperature']:.1f}°C"
            self.weather_desc.text = weather_data['description']
            self.weather_icon.text = weather_data['icon']
            self.weather_city.text = weather_data['city']
    
    def update_world_clocks(self):
        """Update world clock displays"""
        self.clocks_layout.clear_widgets()
        
        cities = [
            ("UTC", None),
            ("Tokyo", "Asia/Tokyo"),
            ("London", "Europe/London"),
            ("New York", "America/New_York")
        ]
        
        for name, tz in cities:
            try:
                if tz is None:
                    now = datetime.now(timezone.utc)
                else:
                    now = datetime.now(zoneinfo.ZoneInfo(tz))
                
                clock_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=25)
                
                city_label = MDLabel(text=name, size_hint_x=0.6, font_size="12dp",
                                   theme_text_color="Secondary")
                time_label = MDLabel(text=now.strftime('%H:%M'), size_hint_x=0.4, font_size="12dp",
                                   theme_text_color="Custom", text_color=[0.6, 0.87, 1, 1],
                                   halign="right")
                
                clock_layout.add_widget(city_label)
                clock_layout.add_widget(time_label)
                self.clocks_layout.add_widget(clock_layout)
                
            except Exception as e:
                print(f"Clock error for {name}: {e}")
    
    def update_calendar(self):
        """Update week calendar"""
        self.calendar_layout.clear_widgets()
        
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        week_num = monday.isocalendar()[1]
        
        self.week_title.text = f"📅 Viikko {week_num}"
        
        for i in range(7):
            date = monday + timedelta(days=i)
            is_today = date == today
            is_weekend = date.weekday() >= 5
            
            # Get name day
            name_day = FINNISH_NAME_DAYS.get((date.month, date.day), "")
            holiday = FINNISH_HOLIDAYS.get((date.month, date.day), "")
            info = holiday or name_day
            
            # Create day layout
            day_layout = MDBoxLayout(orientation='vertical', size_hint_y=None, 
                                   height=35 if not info else 45, spacing=1)
            
            # Day name and number
            day_text = f"{WEEKDAYS_FI[i]} {date.day}"
            
            # Color coding
            if is_today:
                text_color = [0.69, 1, 0.62, 1]  # Green
            elif holiday:
                text_color = [1, 0.42, 0.42, 1]  # Red
            elif is_weekend:
                text_color = [0.42, 0.42, 1, 1]  # Blue
            else:
                text_color = [1, 1, 1, 1]  # White
            
            day_label = MDLabel(text=day_text, font_size="11dp", size_hint_y=None, height=20,
                              theme_text_color="Custom", text_color=text_color)
            day_layout.add_widget(day_label)
            
            # Info text
            if info:
                info_label = MDLabel(text=info[:20] + ("..." if len(info) > 20 else ""),
                                   font_size="9dp", size_hint_y=None, height=15,
                                   theme_text_color="Custom", text_color=[0.8, 0.8, 0.8, 1])
                day_layout.add_widget(info_label)
            
            self.calendar_layout.add_widget(day_layout)
    
    def update_news_data(self):
        """Update news in background"""
        try:
            news_data = self.data_manager.fetch_news()
            if news_data:
                Clock.schedule_once(lambda dt: self.update_news_display(news_data), 0)
        except Exception as e:
            print(f"News update error: {e}")
    
    def update_news_display(self, news_data):
        """Update news UI"""
        self.news_layout.clear_widgets()
        for item in news_data[:5]:
            news_text = f"[{item['source']}] {item['title'][:80]}..."
            label = MDLabel(
                text=news_text,
                theme_text_color="Custom",
                text_color=[0, 0, 0, 1],
                size_hint_y=None,
                height=25,
                font_size="11dp"
            )
            self.news_layout.add_widget(label)
    
    def update_stocks_data(self):
        """Update stocks in background"""
        try:
            stocks_data = self.data_manager.fetch_stocks()
            if stocks_data:
                Clock.schedule_once(lambda dt: self.update_stocks_display(stocks_data), 0)
        except Exception as e:
            print(f"Stocks update error: {e}")
    
    def update_stocks_display(self, stocks_data):
        """Update stocks UI"""
        self.stocks_layout.clear_widgets()
        for item in stocks_data[:6]:
            change_color = [0.56, 0.93, 0.56, 1] if item['change'] >= 0 else [1, 0.71, 0.76, 1]
            arrow = "↗" if item['change'] >= 0 else "↘"
            
            stock_text = f"{item['name']} {item['price']:.2f} {arrow}{item['change']:+.2f}%"
            label = MDLabel(
                text=stock_text,
                theme_text_color="Custom",
                text_color=change_color,
                size_hint_y=None,
                height=20,
                font_size="11dp"
            )
            self.stocks_layout.add_widget(label)
    
    def load_initial_data(self):
        """Load cached data on startup"""
        # Load offline data first
        weather = self.data_manager.load_from_db('weather')
        if weather:
            self.update_weather_display(weather)
        
        news = self.data_manager.load_from_db('news')
        if news:
            self.update_news_display(news)
        
        stocks = self.data_manager.load_from_db('stocks')
        if stocks:
            self.update_stocks_display(stocks)
        
        # Update clocks and calendar immediately
        self.update_world_clocks()
        self.update_calendar()
    
    def open_settings(self):
        """Open settings dialog"""
        SettingsDialog(self).open()
    
    def open_nav_drawer(self):
        """Open navigation drawer (future feature)"""
        pass
    
    def refresh_all_data(self):
        """Manual refresh of all data"""
        self.update_data(None)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        # Implementation depends on Android API level
        pass

class SettingsDialog:
    """Settings dialog for configuration"""
    
    def __init__(self, parent):
        self.parent = parent
        self.settings_manager = parent.settings_manager
        self.dialog = None
    
    def open(self):
        """Open settings dialog"""
        content = MDBoxLayout(orientation='vertical', spacing=15, size_hint_y=None, height=400)
        
        # API Key
        api_label = MDLabel(text="OpenWeatherMap API-avain:", size_hint_y=None, height=30)
        self.api_field = MDTextField(
            text=self.settings_manager.get('api_key', ''),
            password=True,
            helper_text="Hanki ilmainen avain: openweathermap.org/api",
            helper_text_mode="persistent"
        )
        content.add_widget(api_label)
        content.add_widget(self.api_field)
        
        # City
        city_label = MDLabel(text="Oletuskaupunki:", size_hint_y=None, height=30)
        self.city_field = MDTextField(
            text=self.settings_manager.get('default_city', 'Helsinki'),
            helper_text="Esim: Helsinki, Turku, Tampere"
        )
        content.add_widget(city_label)
        content.add_widget(self.city_field)
        
        # Notifications
        notif_label = MDLabel(text="Ilmoitukset:", size_hint_y=None, height=30)
        content.add_widget(notif_label)
        
        notif_layout = MDBoxLayout(orientation='vertical', spacing=5, size_hint_y=None, height=100)
        
        weather_switch_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        weather_switch_layout.add_widget(MDLabel(text="Säävaroitukset"))
        self.weather_switch = MDSwitch(active=self.settings_manager.get('weather_alerts', True))
        weather_switch_layout.add_widget(self.weather_switch)
        
        nameday_switch_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        nameday_switch_layout.add_widget(MDLabel(text="Nimipäivämuistutukset"))
        self.nameday_switch = MDSwitch(active=self.settings_manager.get('nameday_notifications', True))
        nameday_switch_layout.add_widget(self.nameday_switch)
        
        holiday_switch_layout = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        holiday_switch_layout.add_widget(MDLabel(text="Juhlapäivämuistutukset"))
        self.holiday_switch = MDSwitch(active=self.settings_manager.get('holiday_notifications', True))
        holiday_switch_layout.add_widget(self.holiday_switch)
        
        notif_layout.add_widget(weather_switch_layout)
        notif_layout.add_widget(nameday_switch_layout)
        notif_layout.add_widget(holiday_switch_layout)
        content.add_widget(notif_layout)
        
        # Create dialog
        self.dialog = MDDialog(
            title="Asetukset",
            type="custom",
            content_cls=content,
            buttons=[
                MDRaisedButton(text="PERUUTA", on_release=self.close),
                MDRaisedButton(text="TALLENNA", on_release=self.save)
            ]
        )
        self.dialog.open()
    
    def save(self, *args):
        """Save settings"""
        self.settings_manager.set('api_key', self.api_field.text)
        self.settings_manager.set('default_city', self.city_field.text)
        self.settings_manager.set('weather_alerts', self.weather_switch.active)
        self.settings_manager.set('nameday_notifications', self.nameday_switch.active)
        self.settings_manager.set('holiday_notifications', self.holiday_switch.active)
        
        # Refresh data with new settings
        self.parent.refresh_all_data()
        
        self.close()
    
    def close(self, *args):
        """Close dialog"""
        if self.dialog:
            self.dialog.dismiss()

class InfonayttoApp(MDApp):
    """Main application class"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Infonäyttö Pro"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.accent_palette = "LightGreen"
        
        # Managers
        self.settings_manager = None
        self.data_manager = None
        self.background_service = None
        self.notification_manager = None
    
    def build(self):
        """Build the app"""
        # Request Android permissions
        if platform == 'android':
            self.request_android_permissions()
        
        # Initialize managers
        self.settings_manager = SettingsManager()
        self.data_manager = DataManager()
        
        # Create screen manager
        sm = MDScreenManager()
        
        # Add main screen
        main_screen = MainScreen()
        sm.add_widget(main_screen)
        
        return sm
    
    def on_start(self):
        """Called when app starts"""
        print("Infonäyttö Pro starting...")
        
        if platform == 'android':
            # Initialize Android-specific features
            self.setup_android_features()
        
        # Start background services
        self.start_background_services()
        
        print("Infonäyttö Pro started successfully!")
    
    def request_android_permissions(self):
        """Request necessary Android permissions"""
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.INTERNET,
                    Permission.ACCESS_NETWORK_STATE,
                    Permission.WAKE_LOCK,
                    Permission.RECEIVE_BOOT_COMPLETED,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.VIBRATE
                ])
                print("Android permissions requested")
            except Exception as e:
                print(f"Permission request error: {e}")
    
    def setup_android_features(self):
        """Setup Android-specific features"""
        try:
            from services import AndroidIntegration
            
            # Create notification channels
            AndroidIntegration.create_notification_channels()
            
            # Request battery optimization exemption
            AndroidIntegration.request_battery_optimization_exemption()
            
            print("Android features initialized")
        except Exception as e:
            print(f"Android setup error: {e}")
    
    def start_background_services(self):
        """Start background data and notification services"""
        try:
            # Start background service
            self.background_service = BackgroundService(self.data_manager, self.settings_manager)
            
            # Start notification manager
            self.notification_manager = NotificationManager(self.data_manager, self.settings_manager)
            
            # Schedule daily notification checks
            Clock.schedule_interval(
                lambda dt: self.notification_manager.check_daily_notifications(), 
                60  # Check every minute
            )
            
            print("Background services started")
        except Exception as e:
            print(f"Background service start error: {e}")
    
    def on_pause(self):
        """Called when app is paused"""
        print("App paused - background services continue")
        return True
    
    def on_resume(self):
        """Called when app resumes"""
        print("App resumed")
        # Update widgets when app becomes active
        if platform == 'android':
            try:
                ClockWidget.update_widget()
                WeatherWidget.update_widget(self.data_manager)
            except Exception as e:
                print(f"Widget update error: {e}")
    
    def on_stop(self):
        """Called when app stops"""
        print("App stopping...")
        if self.background_service:
            self.background_service.stop()

# Entry point
if __name__ == '__main__':
    try:
        InfonayttoApp().run()
    except Exception as e:
        print(f"App startup error: {e}")
        # Log error for debugging
        with open("error.log", "w") as f:
            import traceback
            f.write(traceback.format_exc())