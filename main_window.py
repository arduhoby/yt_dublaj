from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QComboBox, QCheckBox, QGroupBox, QTextEdit
from PyQt5.QtCore import Qt
from downloader import Downloader
import os # Added for os.startfile
import config_manager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader & Player")
        self.resize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Input Area
        self.input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube URL yapıştırın...")
        
        self.resolution_combo = QComboBox() # Renamed from self.res_combo
        self.resolution_combo.addItems(["720p", "360p", "480p", "1080p", "En İyi"])
        
        self.download_button = QPushButton("İndir ve Oynat") # Renamed from self.download_btn
        self.download_button.clicked.connect(self.start_download)
        
        self.input_layout.addWidget(self.url_input)
        self.input_layout.addWidget(self.resolution_combo) # Used new name
        self.input_layout.addWidget(self.download_button) # Used new name

        self.layout.addLayout(self.input_layout) # Used self.layout

        # Dubbing Language Selector
        self.dubbing_label = QLabel("Dublaj:")
        self.dubbing_combo = QComboBox()
        self.dubbing_combo.addItems(["Dublaj Yok", "Türkçe Dublaj", "İngilizce Dublaj"])
        
        dubbing_layout = QHBoxLayout()
        dubbing_layout.addWidget(self.dubbing_label)
        dubbing_layout.addWidget(self.dubbing_combo)
        dubbing_layout.addStretch()
        self.layout.addLayout(dubbing_layout)

        # TTS Engine Settings
        settings_group = QGroupBox("TTS Motor Ayarları")
        settings_layout = QVBoxLayout()
        
        # TTS Engine Selector
        engine_layout = QHBoxLayout()
        engine_label = QLabel("TTS Motor:")
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems(["Edge-TTS (Ücretsiz)", "ElevenLabs (Premium)"])
        self.tts_engine_combo.currentIndexChanged.connect(self.on_tts_engine_changed)
        engine_layout.addWidget(engine_label)
        engine_layout.addWidget(self.tts_engine_combo)
        engine_layout.addStretch()
        settings_layout.addLayout(engine_layout)
        
        # API Key Input (for ElevenLabs)
        api_layout = QHBoxLayout()
        self.api_key_label = QLabel("API Key:")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("ElevenLabs API Key...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(self.api_key_label)
        api_layout.addWidget(self.api_key_input)
        settings_layout.addLayout(api_layout)
        
        # Custom Voice IDs Option
        self.custom_voices_checkbox = QCheckBox("Özel Voice ID'leri Kullan")
        self.custom_voices_checkbox.stateChanged.connect(self.on_custom_voices_changed)
        settings_layout.addWidget(self.custom_voices_checkbox)
        
        # Custom Voice ID Inputs
        self.custom_voice_labels = []
        self.custom_voice_inputs = {}
        
        voice_types = [
            ("tr_male", "Türkçe Erkek Voice ID:"),
            ("tr_female", "Türkçe Kadın Voice ID:"),
            ("en_male", "İngilizce Erkek Voice ID:"),
            ("en_female", "İngilizce Kadın Voice ID:")
        ]
        
        for voice_key, label_text in voice_types:
            voice_layout = QHBoxLayout()
            label = QLabel(label_text)
            input_field = QLineEdit()
            input_field.setPlaceholderText("Voice ID...")
            voice_layout.addWidget(label)
            voice_layout.addWidget(input_field)
            settings_layout.addLayout(voice_layout)
            
            self.custom_voice_labels.append(label)
            self.custom_voice_inputs[voice_key] = input_field
        
        # Save Settings Button
        self.save_settings_button = QPushButton("Ayarları Kaydet")
        self.save_settings_button.clicked.connect(self.save_settings)
        settings_layout.addWidget(self.save_settings_button)
        
        settings_group.setLayout(settings_layout)
        self.layout.addWidget(settings_group)

        # Status/Log Area
        log_label = QLabel("Durum ve Loglar:")
        self.layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        self.layout.addWidget(self.log_area)
        
        # Cancel Button
        self.cancel_button = QPushButton("İptal")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        self.layout.addWidget(self.cancel_button)
        
        # Store paths and config
        self.current_video_path = None
        self.config = config_manager.load_config()
        self.load_settings_to_ui()
        self.downloader = None
        
        # Initial log message
        self.add_log("Hazır")

    def start_download(self):
        url = self.url_input.text()
        resolution = self.resolution_combo.currentText() # Used new name
        
        # Determine target language from dropdown
        dubbing_option = self.dubbing_combo.currentText()
        if dubbing_option == "Türkçe Dublaj":
            target_language = 'tr'
        elif dubbing_option == "İngilizce Dublaj":
            target_language = 'en'
        else:
            target_language = None  # No dubbing
        
        if not url:
            self.add_log("HATA: Lütfen bir URL girin!")
            return

        self.add_log("İndiriliyor...")
        self.download_button.setEnabled(False) # Used new name
        self.cancel_button.setEnabled(True)
        
        self.downloader = Downloader() # Initialized here as per instruction
        self.downloader.finished.connect(self.on_download_finished)
        self.downloader.progress.connect(self.update_status) # Kept original name update_status
        self.downloader.error.connect(self.on_error)
        self.downloader.download(url, resolution, target_language, self.config)
    
    def add_log(self, message):
        """Add message to log area with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
    
    def cancel_download(self):
        """Cancel ongoing download/dubbing process"""
        if self.downloader and self.downloader.worker:
            self.add_log("⚠️ İşlem iptal ediliyor...")
            self.downloader.worker.terminate()
            self.downloader.worker.wait()
            self.add_log("❌ İşlem iptal edildi")
            self.download_button.setEnabled(True)
            self.cancel_button.setEnabled(False)

    def update_status(self, message): # Kept original name update_status
        self.add_log(message)

    def on_download_finished(self, video_path, subtitle_path):
        self.add_log("✅ İndirme Tamamlandı! Harici oynatıcıda açılıyor...")
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.current_video_path = video_path
        
        # Auto-open in external player
        self.open_external_player()

    def on_error(self, message): # Kept original name message
        self.add_log(f"❌ HATA: {message}")
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def open_external_player(self):
        if self.current_video_path and os.path.exists(self.current_video_path):
            # Windows default player
            os.startfile(self.current_video_path)
        else:
            self.add_log("❌ Video dosyası bulunamadı!")
    
    def load_settings_to_ui(self):
        """Load settings from config to UI"""
        # Set TTS engine
        if self.config.get('tts_engine') == 'elevenlabs':
            self.tts_engine_combo.setCurrentIndex(1)
        else:
            self.tts_engine_combo.setCurrentIndex(0)
        
        # Set API key
        api_key = self.config.get('elevenlabs_api_key', '')
        self.api_key_input.setText(api_key)
        
        # Set custom voices checkbox
        use_custom = self.config.get('use_custom_voices', False)
        self.custom_voices_checkbox.setChecked(use_custom)
        
        # Set custom voice IDs
        custom_voices = self.config.get('custom_voice_ids', {})
        for voice_key, input_field in self.custom_voice_inputs.items():
            input_field.setText(custom_voices.get(voice_key, ''))
        
        # Update visibility
        self.on_tts_engine_changed()
        self.on_custom_voices_changed()
    
    def on_tts_engine_changed(self):
        """Show/hide API key field and custom voices based on selected engine"""
        is_elevenlabs = self.tts_engine_combo.currentIndex() == 1
        self.api_key_label.setVisible(is_elevenlabs)
        self.api_key_input.setVisible(is_elevenlabs)
        self.custom_voices_checkbox.setVisible(is_elevenlabs)
        
        # Update custom voice fields visibility
        if is_elevenlabs:
            self.on_custom_voices_changed()
        else:
            # Hide all custom voice fields if not using ElevenLabs
            for label in self.custom_voice_labels:
                label.setVisible(False)
            for input_field in self.custom_voice_inputs.values():
                input_field.setVisible(False)
    
    def on_custom_voices_changed(self):
        """Show/hide custom voice ID inputs based on checkbox"""
        is_custom = self.custom_voices_checkbox.isChecked()
        is_elevenlabs = self.tts_engine_combo.currentIndex() == 1
        
        # Only show if both ElevenLabs is selected AND custom voices is checked
        show_fields = is_elevenlabs and is_custom
        
        for label in self.custom_voice_labels:
            label.setVisible(show_fields)
        for input_field in self.custom_voice_inputs.values():
            input_field.setVisible(show_fields)
    
    def save_settings(self):
        """Save settings from UI to config file"""
        # Update config
        if self.tts_engine_combo.currentIndex() == 1:
            self.config['tts_engine'] = 'elevenlabs'
        else:
            self.config['tts_engine'] = 'edge-tts'
        
        self.config['elevenlabs_api_key'] = self.api_key_input.text()
        
        # Save custom voices settings
        self.config['use_custom_voices'] = self.custom_voices_checkbox.isChecked()
        
        # Save custom voice IDs
        if 'custom_voice_ids' not in self.config:
            self.config['custom_voice_ids'] = {}
        
        for voice_key, input_field in self.custom_voice_inputs.items():
            self.config['custom_voice_ids'][voice_key] = input_field.text()
        
        # Save to file
        if config_manager.save_config(self.config):
            self.add_log("✅ Ayarlar kaydedildi!")
        else:
            self.add_log("❌ Ayarlar kaydedilemedi!")
