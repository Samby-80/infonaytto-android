# main.py - Infonäyttö Android-sovellus
# Muunnettu alkuperäisestä Python tkinter -sovelluksesta Kivy-frameworkille

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.metrics import dp

import requests
import json
from datetime import datetime, timedelta
import threading

# Suomalainen data - kopiotu alkuperäisestä sovelluksesta
FINNISH_NAME_DAYS = {
    "1-1": "Uudenvuodenpäivä", "1-2": "Aapeli", "1-3": "Elmo", "1-6": "Harri, Loppiainen",
    "1-19": "Heikki", "2-14": "Voitto, Valentin", "3-19": "Juuso, Josefiina, Minna Canthin päivä",
    "4-9": "Elias, Mikael Agricolan päivä", "5-1": "Valpuri, Vappu", 
    "5-12": "Lotta, J.V. Snellmannin päivä", "6-4": "Toivo, Puolustusvoimain lippujuhlan päivä",
    "6-24": "Johannes, Juhani", "7-6": "Esa, Eino Leinon päivä", 
    "10-10": "Aleksi, Aleksis Kiven päivä", "11-6": "Mimosa, ruotsalaisuuden päivä",
    "12-6": "Niilo, Niko, Itsenäisyyspäivä", "12-8": "Kyllikki, Jean Sibeliuksen päivä",
    "12-24": "Aatami, Eeva, Jouluaatto", "12-25": "Joulupäivä", "12-26": "Tapani, Tapaninpäivä"
}

FINNISH_HOLIDAYS = {
    "1-1": "Uudenvuodenpäivä", "1-6": "Loppiainen", "5-1": "Vappu",
    "12-6": "Itsenäisyyspäivä", "12-24": "Jouluaatto", "12-25": "Joulupäivä", "12-26": "Tapaninpäivä"
}

WEEKDAYS_FI = ["Ma", "Ti", "Ke", "To", "Pe", "La", "Su"]
WEEKDAYS_FULL = ["Maanantai", "Tiistai", "Keskiviikko", "Torstai", "Perjantai", "Lauantai", "Sunnuntai"]

class InfonayttoApp(App):
    def build(self):
        # Aseta taustaväri tummansiniseksi kuten alkuperäisessä
        Window.clearcolor = (0.051, 0.067, 0.090, 1)  # #0d1117
        
        # Pääasettelu - vaaka-asettelu kuten alkuperäisessä
        root = BoxLayout(orientation='horizontal', padding=dp(5), spacing=dp(5))
        
        # Vasen paneeli - Maailman kellot ja kalenteri
        left_panel = BoxLayout(orientation='vertical', size_hint_x=0.35, spacing=dp(10))
        
        # Maailman kellot
        clock_title = Label(text="🌍 Maailman ajat", size_hint_y=0.1, 
                           color=(0.345, 0.651, 1, 1), font_size=dp(14))
        left_panel.add_widget(clock_title)
        
        self.world_clocks = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(2))
        left_panel.add_widget(self.world_clocks)
        
        # Viikkokalenteri
        self.week_header = Label(text="Viikko", size_hint_y=0.08, 
                                color=(0.941, 0.678, 0.306, 1), font_size=dp(12))
        left_panel.add_widget(self.week_header)
        
        self.calendar_days = BoxLayout(orientation='vertical', size_hint_y=0.42, spacing=dp(1))
        left_panel.add_widget(self.calendar_days)
        
        root.add_widget(left_panel)
        
        # Keskipaneeli - Pääsisältö
        center_panel = BoxLayout(orientation='vertical', size_hint_x=0.55, spacing=dp(5))
        
        # Aika - iso fontti kuten alkuperäisessä
        self.time_label = Label(text='00:00:00', font_size=dp(50),
                               color=(0.49, 0.827, 0.988, 1), size_hint_y=0.2)
        center_panel.add_widget(self.time_label)
        
        # Päivämäärä
        self.date_label = Label(text='Lataa päivämäärä...', font_size=dp(18),
                               color=(0.941, 0.965, 0.988, 1), size_hint_y=0.08)
        center_panel.add_widget(self.date_label)
        
        # Sää - alkuperäisen layout mukaan
        weather_box = BoxLayout(orientation='vertical', size_hint_y=0.25, spacing=dp(5))
        
        self.weather_city = Label(text='Helsinki 00:00', font_size=dp(16),
                                 color=(0.941, 0.965, 0.988, 1))
        weather_box.add_widget(self.weather_city)
        
        weather_info = BoxLayout(orientation='horizontal', spacing=dp(10))
        self.weather_temp = Label(text='--°C', font_size=dp(36),
                                 color=(0.247, 0.725, 0.314, 1), size_hint_x=0.4)
        self.weather_desc = Label(text='Ladataan säätä...', font_size=dp(16),
                                 color=(0.345, 0.651, 1, 1), size_hint_x=0.6)
        weather_info.add_widget(self.weather_temp)
        weather_info.add_widget(self.weather_desc)
        weather_box.add_widget(weather_info)
        
        center_panel.add_widget(weather_box)
        
        # Sääennuste - 4 päivää vaakasuoraan kuten alkuperäisessä
        forecast_box = BoxLayout(orientation='horizontal', size_hint_y=0.25, spacing=dp(5))
        self.forecast_days = []
        
        for i in range(4):
            day_layout = BoxLayout(orientation='vertical', spacing=dp(2))
            
            day_name = Label(text='', font_size=dp(10), size_hint_y=0.25, color=(1, 1, 1, 1))
            day_icon = Label(text='☀️', font_size=dp(24), size_hint_y=0.35)
            day_temps = Label(text='', font_size=dp(9), size_hint_y=0.3, color=(1, 1, 1, 1))
            day_desc = Label(text='', font_size=dp(7), size_hint_y=0.1, color=(1, 1, 1, 1))
            
            day_layout.add_widget(day_name)
            day_layout.add_widget(day_icon)
            day_layout.add_widget(day_temps)
            day_layout.add_widget(day_desc)
            
            self.forecast_days.append((day_name, day_icon, day_temps, day_desc))
            forecast_box.add_widget(day_layout)
        
        center_panel.add_widget(forecast_box)
        
        # Uutisticker alareunassa kuten alkuperäisessä
        self.news_ticker = Label(text='Ladataan uutisia...', font_size=dp(10),
                                color=(0, 0, 0, 1), size_hint_y=0.1,
                                canvas=None)
        # Keltainen tausta kuten alkuperäisessä
        with self.news_ticker.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.996, 0.953, 0.780, 1)  # #fef3c7
            self.news_bg = Rectangle(size=self.news_ticker.size, pos=self.news_ticker.pos)
        
        self.news_ticker.bind(size=self.update_news_bg, pos=self.update_news_bg)
        center_panel.add_widget(self.news_ticker)
        
        root.add_widget(center_panel)
        
        # Oikea paneeli - Asetuspainikkeet
        right_panel = BoxLayout(orientation='vertical', size_hint_x=0.1, spacing=dp(10))
        
        location_btn = Button(text='📍', font_size=dp(16), size_hint_y=0.1)
        location_btn.bind(on_press=self.show_location_settings)
        
        settings_btn = Button(text='⚙', font_size=dp(16), size_hint_y=0.1)
        settings_btn.bind(on_press=self.show_settings)
        
        right_panel.add_widget(location_btn)
        right_panel.add_widget(settings_btn)
        right_panel.add_widget(Label())  # Tyhjä tila
        
        root.add_widget(right_panel)
        
        # Sovelluksen asetukset
        self.city = 'Helsinki,FI'
        self.api_key = '57a87377456310ddb9cab55388e7ca6c'  # Alkuperäisestä koodista
        
        # Käynnistä päivitykset kuten alkuperäisessä
        Clock.schedule_interval(self.update_time_and_date, 1)
        Clock.schedule_interval(self.update_weather, 1800)  # 30 min
        Clock.schedule_interval(self.update_news, 300)      # 5 min
        Clock.schedule_once(self.initial_updates, 2)
        
        self.update_world_clocks()
        self.update_calendar()
        
        return root
    
    def update_news_bg(self, instance, value):
        """Päivitä uutistickerin taustan koko"""
        self.news_bg.size = instance.size
        self.news_bg.pos = instance.pos
    
    def update_time_and_date(self, dt):
        """Päivitä aika ja päivämäärä - kuten alkuperäisessä"""
        now = datetime.now()
        self.time_label.text = now.strftime('%H:%M:%S')
        
        weekday = WEEKDAYS_FULL[now.weekday()]
        self.date_label.text = f"{weekday} {now.strftime('%d.%m.%Y')}"
    
    def update_world_clocks(self, dt=None):
        """Päivitä maailman kellot - kuten alkuperäisessä"""
        self.world_clocks.clear_widgets()
        
        cities = [
            ("UTC", 0),
            ("Tokyo", 9),
            ("Bangkok", 7),  
            ("Rome", 1),
            ("London", 0),
            ("New York", -5)
        ]
        
        utc_now = datetime.utcnow()
        
        for city, offset in cities:
            city_time = utc_now + timedelta(hours=offset)
            time_str = city_time.strftime('%H:%M')
            
            clock_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(25))
            
            city_label = Label(text=city, size_hint_x=0.6, font_size=dp(10),
                              color=(0.933, 0.933, 0.933, 1), halign='left')
            time_label = Label(text=time_str, size_hint_x=0.4, font_size=dp(11),
                              color=(0.533, 0.8, 1, 1), halign='right')
            
            city_label.text_size = (None, None)
            time_label.text_size = (None, None)
            
            clock_row.add_widget(city_label)
            clock_row.add_widget(time_label)
            self.world_clocks.add_widget(clock_row)
        
        # Aikatauluta seuraava päivitys
        Clock.schedule_once(self.update_world_clocks, 60)
    
    def update_calendar(self):
        """Päivitä viikkokalenteri - kuten alkuperäisessä"""
        self.calendar_days.clear_widgets()
        
        today = datetime.now().date()
        monday = today - timedelta(days=today.weekday())
        
        # Viikkonumero
        week_number = monday.isocalendar()[1]
        self.week_header.text = f"Viikko {week_number}"
        
        for i in range(7):
            date = monday + timedelta(days=i)
            day_widget = self.create_calendar_day(date, today)
            self.calendar_days.add_widget(day_widget)
    
    def create_calendar_day(self, date, today):
        """Luo kalenteripäivä - kuten alkuperäisessä"""
        day_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
        
        is_today = date == today
        is_weekend = date.weekday() >= 5
        key = f"{date.month}-{date.day}"
        holiday = FINNISH_HOLIDAYS.get(key, "")
        name_day = FINNISH_NAME_DAYS.get(key, "")
        
        # Värit kuten alkuperäisessä
        if is_today:
            text_color = (0.565, 0.933, 0.565, 1)  # Vihreä
        elif holiday:
            text_color = (1, 0.419, 0.419, 1)      # Punainen
        elif is_weekend:
            text_color = (0.419, 0.419, 1, 1)      # Sininen
        else:
            text_color = (0.8, 0.8, 0.8, 1)        # Harmaa
        
        weekday = WEEKDAYS_FI[date.weekday()]
        day_text = f"{weekday} {date.day}"
        
        day_label = Label(text=day_text, size_hint_x=0.35, font_size=dp(9),
                         color=text_color, halign='left')
        day_label.text_size = (None, None)
        
        # Nimipäivä tai juhlapyhä
        info_text = holiday if holiday else name_day
        if info_text and len(info_text) > 20:
            info_text = info_text[:20] + "..."
        
        info_label = Label(text=info_text, size_hint_x=0.65, font_size=dp(7),
                          color=text_color, halign='left')
        info_label.text_size = (None, None)
        
        day_layout.add_widget(day_label)
        day_layout.add_widget(info_label)
        
        return day_layout
    
    def initial_updates(self, dt):
        """Käynnistä alkupäivitykset taustalla"""
        threading.Thread(target=self.fetch_weather, daemon=True).start()
        threading.Thread(target=self.fetch_forecast, daemon=True).start()
        threading.Thread(target=self.fetch_news, daemon=True).start()
    
    def fetch_weather(self):
        """Hae säätiedot - kuten alkuperäisessä"""
        try:
            location = self.city.split(',')[0] if ',' in self.city else self.city
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.api_key}&units=metric&lang=fi"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                temp = data['main']['temp']
                desc = data['weather'][0]['description'].capitalize()
                city_name = data.get('name', location)
                
                current_time = datetime.now().strftime('%H:%M')
                
                Clock.schedule_once(lambda dt: self.update_weather_ui(city_name, current_time, temp, desc), 0)
            else:
                Clock.schedule_once(lambda dt: self.update_weather_ui(location, '', None, 'Ei säätietoja'), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_weather_ui('', '', None, f'Virhe: {str(e)[:20]}'), 0)
    
    def update_weather_ui(self, city, time_str, temp, desc):
        """Päivitä sään käyttöliittymä"""
        self.weather_city.text = f"{city} {time_str}"
        if temp is not None:
            self.weather_temp.text = f"{temp:.1f}°C"
        self.weather_desc.text = desc
    
    def fetch_forecast(self):
        """Hae sääennuste - kuten alkuperäisessä"""
        try:
            location = self.city.split(',')[0] if ',' in self.city else self.city
            url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={self.api_key}&units=metric&lang=fi"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                forecasts = self.process_forecast(data)
                Clock.schedule_once(lambda dt: self.update_forecast_ui(forecasts[:4]), 0)
        except Exception as e:
            pass  # Hiljainen virhe, ennuste ei ole kriittinen
    
    def process_forecast(self, data):
        """Käsittele ennustedata - kuten alkuperäisessä"""
        daily_temps = {}
        icons_at_noon = {}
        
        for entry in data['list']:
            dt = datetime.fromtimestamp(entry['dt'])
            date_str = dt.date().isoformat()
            
            if dt.date() <= datetime.now().date():
                continue
            
            tmin = entry['main']['temp_min']
            tmax = entry['main']['temp_max']
            icon = entry['weather'][0]['icon']
            desc = entry['weather'][0]['description'].capitalize()
            
            if date_str not in daily_temps:
                daily_temps[date_str] = {'min': tmin, 'max': tmax}
            else:
                daily_temps[date_str]['min'] = min(daily_temps[date_str]['min'], tmin)
                daily_temps[date_str]['max'] = max(daily_temps[date_str]['max'], tmax)
            
            if dt.hour == 12:  # Keskipäivän data
                icons_at_noon[date_str] = (icon, desc)
        
        forecasts = []
        for date_str in sorted(daily_temps.keys())[:4]:
            date_obj = datetime.fromisoformat(date_str).date()
            temps = daily_temps[date_str]
            icon_data = icons_at_noon.get(date_str, ('01d', 'Selkeä'))
            
            forecasts.append({
                'date': date_obj,
                'temp_min': temps['min'],
                'temp_max': temps['max'],
                'icon': icon_data[0],
                'description': icon_data[1]
            })
        
        return forecasts
    
    def update_forecast_ui(self, forecasts):
        """Päivitä ennusteen käyttöliittymä"""
        icon_map = {
            '01d': '☀️', '01n': '🌙', '02d': '⛅', '02n': '☁️',
            '03d': '☁️', '03n': '☁️', '04d': '☁️', '04n': '☁️',
            '09d': '🌧️', '09n': '🌧️', '10d': '🌦️', '10n': '🌧️',
            '11d': '⛈️', '11n': '⛈️', '13d': '❄️', '13n': '❄️',
            '50d': '🌫️', '50n': '🌫️'
        }
        
        for i, forecast in enumerate(forecasts):
            if i < len(self.forecast_days):
                day_name, day_icon, day_temps, day_desc = self.forecast_days[i]
                
                weekday = WEEKDAYS_FI[forecast['date'].weekday()]
                day_name.text = f"{weekday} {forecast['date'].day}"
                
                day_icon.text = icon_map.get(forecast['icon'], '☀️')
                
                day_temps.text = f"Ylin {round(forecast['temp_max'])}°C\nAlin {round(forecast['temp_min'])}°C"
                day_desc.text = forecast['description'][:15]
    
    def fetch_news(self):
        """Hae uutiset - simuloidaan kuten alkuperäisessä"""
        try:
            # Simuloidaan uutisia
            mock_news = [
                "[YLE] Säätiedotus - Sää vaihtelee eri puolilla maata",
                "[CNN] Technology sector shows continued growth trends",
                "[BBC] Global cooperation increases in climate initiatives",
                "[YLE] Tutkimus: Mielenkiintoisia löydöksiä tehtiin"
            ]
            news_text = " • ".join(mock_news)
            Clock.schedule_once(lambda dt: setattr(self.news_ticker, 'text', news_text), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self.news_ticker, 'text', 'Uutisia ei saatavilla'), 0)
    
    def update_weather(self, dt):
        """Säätietojen päivitysaikataulutus"""
        threading.Thread(target=self.fetch_weather, daemon=True).start()
        threading.Thread(target=self.fetch_forecast, daemon=True).start()
    
    def update_news(self, dt):
        """Uutisten päivitysaikataulutus"""
        threading.Thread(target=self.fetch_news, daemon=True).start()
    
    def show_location_settings(self, instance):
        """Näytä sijaintiasetukset"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        content.add_widget(Label(text='Vaihda kaupunki:', size_hint_y=0.3))
        
        text_input = TextInput(text=self.city, multiline=False, size_hint_y=0.4)
        content.add_widget(text_input)
        
        buttons = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=dp(10))
        save_btn = Button(text='Tallenna')
        cancel_btn = Button(text='Peruuta')
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        popup = Popup(title='Kaupungin vaihto', content=content, size_hint=(0.8, 0.6))
        
        def save_city(instance):
            new_city = text_input.text.strip()
            if new_city:
                self.city = new_city
                popup.dismiss()
                threading.Thread(target=self.fetch_weather, daemon=True).start()
                threading.Thread(target=self.fetch_forecast, daemon=True).start()
        
        save_btn.bind(on_press=save_city)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def show_settings(self, instance):
        """Näytä yleiset asetukset"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        content.add_widget(Label(text='Infonäyttö Android\nVersio 1.0\n\nPerustuuu alkuperäiseen Python-sovellukseen.', 
                                size_hint_y=0.7, halign='center'))
        
        close_btn = Button(text='Sulje', size_hint_y=0.3)
        content.add_widget(close_btn)
        
        popup = Popup(title='Tietoja', content=content, size_hint=(0.8, 0.6))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

# Pääsovellus
InfonayttoApp().run()
