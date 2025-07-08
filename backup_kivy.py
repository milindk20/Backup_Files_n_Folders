import os
import shutil
import threading
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.clock import Clock

class BackupLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=20, spacing=10, **kwargs)
        self.source_dirs = []
        self.destination = ''
        self.copied_files = 0
        self.total_files = 0
        self.start_time = None
        self.is_running = False
        self.thread = None
        self.progress_percent = 0
        self.eta = 0

        self.title = Label(text='[b]Directory Backup Tool[/b]', markup=True, font_size=28, color=(0.29,0.56,0.89,1), size_hint=(1, 0.15))
        self.add_widget(self.title)

        from kivy.uix.spinner import Spinner
        self.src_label = Label(text='Source Directories:', size_hint=(1, 0.08), bold=True)
        self.add_widget(self.src_label)
        src_box = BoxLayout(size_hint=(1, 0.12), spacing=10)
        self.src_spinner = Spinner(text='No folder selected', values=[], size_hint=(0.7, 1))
        src_box.add_widget(self.src_spinner)
        self.add_src_btn = Button(text='Add Folder', size_hint=(0.15, 1), on_press=self.add_folder)
        src_box.add_widget(self.add_src_btn)
        self.remove_src_btn = Button(text='Remove Selected', size_hint=(0.15, 1), on_press=self.remove_selected_folder)
        src_box.add_widget(self.remove_src_btn)
        self.add_widget(src_box)

        self.dest_label = Label(text='Destination Directory:', size_hint=(1, 0.08), bold=True)
        self.add_widget(self.dest_label)
        self.dest_input = TextInput(hint_text='Click "Select Folder" to choose', readonly=True, size_hint=(1, 0.08))
        self.add_widget(self.dest_input)
        self.dest_btn = Button(text='Select Folder', size_hint=(1, 0.08), on_press=self.select_dest)
        self.add_widget(self.dest_btn)

        self.progress = ProgressBar(max=100, value=0, size_hint=(1, 0.08))
        self.add_widget(self.progress)
        self.progress_label = Label(text='', size_hint=(1, 0.08))
        self.add_widget(self.progress_label)

        btn_layout = BoxLayout(size_hint=(1, 0.12), spacing=10)
        self.start_btn = Button(text='Start Backup', on_press=self.start_backup)
        self.reset_btn = Button(text='Reset', on_press=self.reset)
        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.reset_btn)
        self.add_widget(btn_layout)

    def add_folder(self, instance):
        chooser = FileChooserListView(path='/', dirselect=True, filters=['!*.pyc'])
        box = BoxLayout(orientation='vertical')
        box.add_widget(chooser)
        btn = Button(text='Add', size_hint=(1, 0.12))
        box.add_widget(btn)
        popup = Popup(title='Select Source Folder', content=box, size_hint=(0.9, 0.9))
        def select_folder(instance):
            if chooser.selection:
                folder = chooser.selection[0]
                if folder not in self.source_dirs:
                    self.source_dirs.append(folder)
                    self.update_src_spinner()
            popup.dismiss()
        btn.bind(on_press=select_folder)
        popup.open()

    def update_src_spinner(self):
        if self.source_dirs:
            self.src_spinner.values = self.source_dirs
            self.src_spinner.text = self.source_dirs[0]
        else:
            self.src_spinner.values = []
            self.src_spinner.text = 'No folder selected'

    def remove_selected_folder(self, instance):
        selected = self.src_spinner.text
        if selected in self.source_dirs:
            self.source_dirs.remove(selected)
            self.update_src_spinner()

    def select_dest(self, instance):
        chooser = FileChooserListView(path='/', dirselect=True, filters=['!*.pyc'])
        box = BoxLayout(orientation='vertical')
        box.add_widget(chooser)
        btn = Button(text='Select', size_hint=(1, 0.12))
        box.add_widget(btn)
        popup = Popup(title='Select Destination Folder', content=box, size_hint=(0.9, 0.9))
        def select_folder(instance):
            if chooser.selection:
                self.destination = chooser.selection[0]
                self.dest_input.text = self.destination
                popup.dismiss()
        btn.bind(on_press=select_folder)
        popup.open()

    def count_files(self, dirs):
        count = 0
        for d in dirs:
            for root, _, files in os.walk(d):
                count += len(files)
        return count

    def backup_worker(self):
        self.is_running = True
        self.copied_files = 0
        self.total_files = self.count_files(self.source_dirs)
        self.start_time = time.time()
        try:
            for src in self.source_dirs:
                dest_path = os.path.join(self.destination, os.path.basename(src))
                for root, dirs, files in os.walk(src):
                    rel_path = os.path.relpath(root, src)
                    dest_dir = os.path.join(dest_path, rel_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    for file in files:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_dir, file)
                        if not os.path.exists(dest_file) or os.path.getmtime(src_file) > os.path.getmtime(dest_file):
                            shutil.copy2(src_file, dest_file)
                        self.copied_files += 1
                        Clock.schedule_once(lambda dt: self.update_progress(), 0)
            self.is_running = False
            Clock.schedule_once(lambda dt: self.progress_label.setter('text')(self.progress_label, 'Backup completed!'), 0)
        except Exception as e:
            self.is_running = False
            Clock.schedule_once(lambda dt: self.progress_label.setter('text')(self.progress_label, f'Error: {e}'), 0)

    def update_progress(self):
        percent = int((self.copied_files / self.total_files) * 100) if self.total_files else 0
        elapsed = time.time() - self.start_time
        eta = int(elapsed * (self.total_files - self.copied_files) / self.copied_files) if self.copied_files else 0
        self.progress.value = percent
        self.progress_label.text = f'Copied {self.copied_files} of {self.total_files} files ({percent}%) | ETA: {eta}s'

    def start_backup(self, instance):
        if self.is_running:
            self.progress_label.text = 'Backup is already running.'
            return
        if not self.source_dirs or not self.destination:
            self.progress_label.text = 'Please select source and destination folders.'
            return
        self.progress.value = 0
        self.progress_label.text = 'Starting backup...'
        self.thread = threading.Thread(target=self.backup_worker, daemon=True)
        self.thread.start()

    def reset(self, instance):
        self.source_dirs = []
        self.destination = ''
        self.update_src_spinner()
        self.dest_input.text = ''
        self.progress.value = 0
        self.progress_label.text = ''

class BackupAppKivy(App):
    def build(self):
        return BackupLayout()

if __name__ == '__main__':
    BackupAppKivy().run()
