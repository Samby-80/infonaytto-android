[app]

# (str) Sovelluksen nimi
title = Infonäyttö

# (str) Paketti nimi
package.name = infonaytto

# (str) Paketti domain (käännetty DNS muoto)
package.domain = org.example

# (str) Lähdekoodi sijainti
source.dir = .

# (list) Mukaan otettavat tiedostopäätteet
source.include_exts = py,png,jpg,kv,atlas,json,txt

# (str) Sovelluksen versio
version = 1.0

# (str) Sovelluksen versio (Android)
version.regex = __version__ = ['"]([^'"]*)['"']
version.filename = %(source.dir)s/main.py

# (list) Sovelluksen riippuvuudet
# Huom: requests sisältää automaattisesti urllib3, certifi, charset-normalizer, idna
requirements = python3,kivy,requests

# (str) Presplash tausta
presplash.filename = %(source.dir)s/presplash.png

# (str) Ikoni 
icon.filename = %(source.dir)s/icon.png

# (str) Tuettu suunta (portrait, landscape tai all)
orientation = portrait

# (bool) Ilmoita jos sovellus tukee Android Auto
osx.python_version = 3

# (bool) Koko näyttö
fullscreen = 0

#
# Android specific
#

# (bool) Ilmoita jos tämä on kamera-sovellus
android.camera = 0

# (list) Luvat
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

# (int) Target Android API, pitäisi olla viimeisimmän API taso.
android.api = 33

# (int) Minimum API sovelluksesi on yhteensopiva (vaikuttaa APK kokoon!)
android.minapi = 21

# (str) Android NDK versio käytettäväksi
android.ndk = 25b

# (str) Android SDK versio käytettäväksi
android.sdk = 33

# (str) python-for-android fork käytettäväksi
# p4a.fork = kivy

# (str) python-for-android branch käytettäväksi
# p4a.branch = master

# (str) python-for-android git clone directory (jos tyhjä, väliaikainen kansio käytetään)
# p4a.source_dir =

# (str) Nimi bootstrap:lle käytettäväksi sekä reseptien listalle
# p4a.bootstrap = sdl2

# (str) Nimi reseptille
# p4a.recipe_dir =

# (str) xml tiedosto, joka sisältää saatavilla olevat permissions (käytetty Android-ille)
# p4a.permission_file =

# (str) Bootstrap käytettäväksi app:lle
# p4a.bootstrap = sdl2

# (str) Käytetään olemassa olevaa android repository
# android.ant_path =

# (str) Jos False, sovellus ei käynnisty splash screenillä
# android.presplash_color = #FFFFFF

# (str) Adaptive icon tausta väri (käytetään jos icon.adaptive_foreground on määritelty)
# android.adaptive_icon_background_color = "#FFFFFF"

# (str) Adaptive icon foreground (käytetään jos icon.adaptive_background on määritelty)
# android.adaptive_icon_foreground = %(source.dir)s/data/icon_foreground.png

# (list) Gradle riippuvuudet jotka lisätään
# android.gradle_dependencies =

# (bool) Käytä automaattista backup järjestelmää (Android API level 23+)
android.allow_backup = True

# (str) XML tiedosto jossa privat volume backup säännöt (Android API level 29+)
# android.backup_rules =

# (str) Jos totta, tämä on 'private' sovellus ja saa Android Auto permission
# android.private_volume = False

# (str) Android logcat suodattimet käytettäväksi
# android.logcat_filters = *:S python:D

# (bool) Android logcat vain debug release
# android.logcat_pid_only = False

# (str) Android entry point, oletuksena main.py
# android.entrypoint = main.py

# (str) Android app theme (@android:style/Theme.NoTitleBar oletus)
# android.theme = @android:style/Theme.NoTitleBar

# (list) Pattern to whitelist for the whole project
# android.whitelist =

# (str) Path to a custom whitelist file
# android.whitelist_src =

# (str) Path to a custom blacklist file
# android.blacklist_src =

# (bool) Jos true, aloita debug moodissa
debug = 0

[buildozer]

# (int) Log level (0 = vain virheet, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Näytä viestit (0 = ei näytetä, 1 = vain virheet, 2 = kaikki viestit)
warn_on_root = 1

# (str) Path to build artifact storage, oletuksena $HOME/.buildozer
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin
