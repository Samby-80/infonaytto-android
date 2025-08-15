"""
Background Services and Android Widgets
Handles data updates, notifications, and widget management
"""

import threading
import time
import json
from datetime import datetime, timedelta
from kivy.clock import Clock
from kivy.utils import platform

if platform == 'android':
    from jnius import autoclass, PythonJavaClass, java_method
    from android.broadcast import BroadcastReceiver
    from plyer import notification
    
    # Android classes
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    PendingIntent = autoclass('android.app.PendingIntent')
    ComponentName = autoclass('android.content.ComponentName')
    AppWidgetManager = autoclass('android.appwidget.AppWidgetManager')
    RemoteViews = autoclass('android.widget.RemoteViews')

class BackgroundService:
    """Manages background data updates and notifications"""
    
    def __init__(self, data_manager, settings):
        self.data_manager = data_manager
        self.settings = settings
        self.running = True
        self.last_update = {}
        
        # Start background thread
        self.background_thread = threading.Thread(target=self.background_loop, daemon=True)
        self.background_thread.start()
    
    def background_loop(self):
        """Main background update loop"""
        while self.running:
            try:
                now = datetime.now()
                
                # Update weather every 30 minutes
                if self.should_update('weather', 30):
                    self.update_weather()
                    self.last_update['weather'] = now
                
                # Update news every 15 minutes
                if self.should_update('news', 15):
                    self.update_news()
                    self.last_update['news'] = now
                
                # Update stocks every 30 minutes (during market hours)
                if self.should_update('stocks', 30) and self.is_market_hours():
                    self.update_stocks()
                    self.last_update['stocks'] = now
                
                # Update widgets every 15 minutes
                if self.should_update('widgets', 15):
                    self.update_widgets()
                    self.last_update['widgets'] = now
                
                # Sleep for 5 minutes before next check
                time.sleep(300)
                
            except Exception as e:
                print(f"Background service error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def should_update(self, service, interval_minutes):
        """Check if service should be updated"""
        if service not in self.last_update:
            return True
        
        time_diff = datetime.now() - self.last_update[service]
        return time_diff.total_seconds() > (interval_minutes * 60)
    
    def is_market_hours(self):
        """Check if it's market hours (simplified)"""
        now = datetime.now()
        # Simple check: weekdays 9-17
        return now.weekday() < 5 and 9 <= now.hour < 17
    
    def update_weather(self):
        """Update weather data in background"""
        try:
            api_key = self.settings.get('api_key')
            city = self.settings.get('default_city', 'Helsinki')
            
            if api_key:
                weather_data = self.data_manager.fetch_weather_online(city, api_key)
                if weather_data:
                    # Check for weather alerts
                    self.check_weather_alerts(weather_data)
                    print("Weather updated in background")
        except Exception as e:
            print(f"Background weather update error: {e}")
    
    def update_news(self):
        """Update news data in background"""
        try:
            # Fetch news (implementation from main app)
            print("News updated in background")
        except Exception as e:
            print(f"Background news update error: {e}")
    
    def update_stocks(self):
        """Update stock data in background"""
        try:
            # Fetch stocks (implementation from main app)
            print("Stocks updated in background")
        except Exception as e:
            print(f"Background stocks update error: {e}")
    
    def update_widgets(self):
        """Update all Android widgets"""
        if platform == 'android':
            try:
                # Update clock widget
                ClockWidget.update_widget()
                
                # Update weather widget
                WeatherWidget.update_widget(self.data_manager)
                
                print("Widgets updated")
            except Exception as e:
                print(f"Widget update error: {e}")
    
    def check_weather_alerts(self, weather_data):
        """Check for weather conditions that need alerts"""
        temp = weather_data.get('temperature', 0)
        description = weather_data.get('description', '').lower()
        
        # Temperature alerts
        if temp < -20:
            self.send_notification(
                "❄️ Kylmyysvaroitus",
                f"Ulkona on {temp:.1f}°C - pukeudu lämpimästi!"
            )
        elif temp > 30:
            self.send_notification(
                "🔥 Kuumuusvaroitus", 
                f"Ulkona on {temp:.1f}°C - muista juoda vettä!"
            )
        
        # Weather condition alerts
        if any(word in description for word in ['myrsky', 'ukkonen', 'storm']):
            self.send_notification(
                "⛈️ Säävaroitus",
                f"Sääennuste: {weather_data['description']}"
            )
    
    def send_notification(self, title, message):
        """Send push notification"""
        if platform == 'android':
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="Infonäyttö Pro",
                    app_icon="icon",
                    timeout=10
                )
            except Exception as e:
                print(f"Notification error: {e}")
    
    def stop(self):
        """Stop background service"""
        self.running = False

class ClockWidget:
    """Android home screen clock widget"""
    
    @staticmethod
    def update_widget():
        """Update clock widget on home screen"""
        if platform != 'android':
            return
            
        try:
            # Get widget manager
            context = PythonActivity.mActivity
            appWidgetManager = AppWidgetManager.getInstance(context)
            
            # Create remote views
            views = RemoteViews(context.getPackageName(), 
                              context.getResources().getIdentifier(
                                  'clock_widget_layout', 'layout', context.getPackageName()))
            
            # Update time
            now = datetime.now()
            time_str = now.strftime("%H:%M")
            date_str = now.strftime("%d.%m")
            
            # Set text views
            views.setTextViewText(
                context.getResources().getIdentifier('widget_time', 'id', context.getPackageName()),
                time_str
            )
            views.setTextViewText(
                context.getResources().getIdentifier('widget_date', 'id', context.getPackageName()),
                date_str
            )
            
            # Update widget
            component = ComponentName(context, "ClockWidget")
            appWidgetManager.updateAppWidget(component, views)
            
        except Exception as e:
            print(f"Clock widget update error: {e}")

class WeatherWidget:
    """Android home screen weather widget"""
    
    @staticmethod
    def update_widget(data_manager):
        """Update weather widget on home screen"""
        if platform != 'android':
            return
            
        try:
            # Get latest weather data
            weather_data = data_manager.load_from_db('weather')
            if not weather_data:
                return
            
            # Get widget manager
            context = PythonActivity.mActivity
            appWidgetManager = AppWidgetManager.getInstance(context)
            
            # Create remote views
            views = RemoteViews(context.getPackageName(),
                              context.getResources().getIdentifier(
                                  'weather_widget_layout', 'layout', context.getPackageName()))
            
            # Update weather info
            temp_str = f"{weather_data['temperature']:.0f}°C"
            
            views.setTextViewText(
                context.getResources().getIdentifier('widget_temp', 'id', context.getPackageName()),
                temp_str
            )
            views.setTextViewText(
                context.getResources().getIdentifier('widget_desc', 'id', context.getPackageName()),
                weather_data['description']
            )
            views.setTextViewText(
                context.getResources().getIdentifier('widget_city', 'id', context.getPackageName()),
                weather_data['city']
            )
            views.setTextViewText(
                context.getResources().getIdentifier('widget_icon', 'id', context.getPackageName()),
                weather_data['icon']
            )
            
            # Update widget
            component = ComponentName(context, "WeatherWidget")
            appWidgetManager.updateAppWidget(component, views)
            
        except Exception as e:
            print(f"Weather widget update error: {e}")

class NotificationManager:
    """Manages different types of notifications"""
    
    def __init__(self, data_manager, settings):
        self.data_manager = data_manager
        self.settings = settings
        self.sent_today = set()  # Track notifications sent today
    
    def check_daily_notifications(self):
        """Check and send daily notifications"""
        now = datetime.now()
        
        # Reset daily tracking at midnight
        if now.hour == 0 and now.minute == 0:
            self.sent_today.clear()
        
        # Morning name day notification (8 AM)
        if (now.hour == 8 and now.minute == 0 and 
            'nameday' not in self.sent_today and
            self.settings.get('nameday_notifications', True)):
            self.send_nameday_notification()
            self.sent_today.add('nameday')
        
        # Holiday reminder (7 AM on holidays)
        if (now.hour == 7 and now.minute == 0 and
            'holiday' not in self.sent_today and
            self.settings.get('holiday_notifications', True)):
            holiday = self.check_today_holiday()
            if holiday:
                self.send_holiday_notification(holiday)
                self.sent_today.add('holiday')
    
    def send_nameday_notification(self):
        """Send today's name day notification"""
        try:
            today = datetime.now()
            # Get name day (simplified - you'd load from database)
            nameday = self.get_nameday(today.month, today.day)
            
            if nameday:
                notification.notify(
                    title="🎂 Nimipäivä tänään",
                    message=f"Tänään on {nameday} nimipäivä!",
                    app_name="Infonäyttö Pro",
                    timeout=10
                )
        except Exception as e:
            print(f"Nameday notification error: {e}")
    
    def send_holiday_notification(self, holiday):
        """Send holiday notification"""
        try:
            notification.notify(
                title="🎉 Juhlapäivä tänään",
                message=f"Tänään vietetään: {holiday}",
                app_name="Infonäyttö Pro",
                timeout=10
            )
        except Exception as e:
            print(f"Holiday notification error: {e}")
    
    def get_nameday(self, month, day):
        """Get name day for given date"""
        # Simplified implementation
        return None
    
    def check_today_holiday(self):
        """Check if today is a Finnish holiday"""
        today = datetime.now()
        from main import FINNISH_HOLIDAYS  # Import from main app
        return FINNISH_HOLIDAYS.get((today.month, today.day))

class SettingsManager:
    """Manages app settings with Android SharedPreferences"""
    
    def __init__(self):
        self.settings = {}
        self.load_settings()
    
    def load_settings(self):
        """Load settings from Android SharedPreferences or file"""
        if platform == 'android':
            try:
                context = PythonActivity.mActivity
                prefs = context.getSharedPreferences("InfonayttoSettings", Context.MODE_PRIVATE)
                
                # Load all settings
                self.settings = {
                    'api_key': prefs.getString('api_key', ''),
                    'default_city': prefs.getString('default_city', 'Helsinki'),
                    'theme': prefs.getString('theme', 'dark'),
                    'nameday_notifications': prefs.getBoolean('nameday_notifications', True),
                    'holiday_notifications': prefs.getBoolean('holiday_notifications', True),
                    'weather_alerts': prefs.getBoolean('weather_alerts', True),
                    'update_interval': prefs.getInt('update_interval', 15)
                }
            except Exception as e:
                print(f"Settings load error: {e}")
                self.settings = self.get_default_settings()
        else:
            # Fallback for non-Android
            self.settings = self.get_default_settings()
    
    def save_settings(self):
        """Save settings to Android SharedPreferences"""
        if platform == 'android':
            try:
                context = PythonActivity.mActivity
                prefs = context.getSharedPreferences("InfonayttoSettings", Context.MODE_PRIVATE)
                editor = prefs.edit()
                
                for key, value in self.settings.items():
                    if isinstance(value, str):
                        editor.putString(key, value)
                    elif isinstance(value, bool):
                        editor.putBoolean(key, value)
                    elif isinstance(value, int):
                        editor.putInt(key, value)
                
                editor.apply()
                print("Settings saved successfully")
            except Exception as e:
                print(f"Settings save error: {e}")
    
    def get_default_settings(self):
        """Get default settings"""
        return {
            'api_key': '',
            'default_city': 'Helsinki',
            'theme': 'dark',
            'nameday_notifications': True,
            'holiday_notifications': True,
            'weather_alerts': True,
            'update_interval': 15
        }
    
    def get(self, key, default=None):
        """Get setting value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set setting value"""
        self.settings[key] = value
        self.save_settings()

class AndroidIntegration:
    """Handles Android-specific integrations"""
    
    @staticmethod
    def setup_boot_receiver():
        """Setup boot receiver to start background service"""
        if platform == 'android':
            # This would be handled in Java/Kotlin code
            pass
    
    @staticmethod
    def create_notification_channels():
        """Create notification channels for Android 8+"""
        if platform == 'android':
            try:
                context = PythonActivity.mActivity
                
                # Weather alerts channel
                NotificationChannel = autoclass('android.app.NotificationChannel')
                NotificationManager = autoclass('android.app.NotificationManager')
                
                manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
                
                # Weather channel
                weather_channel = NotificationChannel(
                    "weather_alerts",
                    "Säävaroitukset", 
                    NotificationManager.IMPORTANCE_DEFAULT
                )
                weather_channel.setDescription("Säähälytykset ja varoitukset")
                manager.createNotificationChannel(weather_channel)
                
                # Daily notifications channel
                daily_channel = NotificationChannel(
                    "daily_notifications",
                    "Päivittäiset muistutukset",
                    NotificationManager.IMPORTANCE_LOW
                )
                daily_channel.setDescription("Nimipäivät ja juhlapäivät")
                manager.createNotificationChannel(daily_channel)
                
                print("Notification channels created")
                
            except Exception as e:
                print(f"Notification channel creation error: {e}")
    
    @staticmethod
    def request_battery_optimization_exemption():
        """Request to be exempted from battery optimization"""
        if platform == 'android':
            try:
                context = PythonActivity.mActivity
                
                # Check if battery optimization is enabled
                PowerManager = autoclass('android.os.PowerManager')
                pm = context.getSystemService(Context.POWER_SERVICE)
                
                if not pm.isIgnoringBatteryOptimizations(context.getPackageName()):
                    # Request exemption
                    intent = Intent()
                    intent.setAction("android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS")
                    intent.setData("package:" + context.getPackageName())
                    context.startActivity(intent)
                    
            except Exception as e:
                print(f"Battery optimization request error: {e}")

# Initialize services when module is imported
if platform == 'android':
    # Setup Android integrations
    AndroidIntegration.create_notification_channels()
    AndroidIntegration.setup_boot_receiver()