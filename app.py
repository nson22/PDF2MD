from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import queue
import sys
import threading
from tkinter import Canvas, StringVar, filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD
from converter import convert_pdf


BG = '#151515'
CONTROL = '#272829'
TEXT = '#eeeeef'
MUTED = '#a0a9b3'
BLUE = '#79cff5'
ROW_HEIGHT = 32
ASSETS = Path(__file__).resolve().parent / 'assets'


@dataclass
class FileEntry:
    size: int
    added: datetime
    state: str = 'Na fila'
    detail: str = ''


class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title('PDF2MD')
        if sys.platform == 'win32':
            self.iconbitmap(str(ASSETS / 'app.ico'))
        else:
            with Image.open(ASSETS / 'app.png') as icon:
                self.app_icon = ImageTk.PhotoImage(icon.resize((64, 64)), master=self)
            self.iconphoto(True, self.app_icon)
        self.geometry('1060x750')
        self.minsize(760, 450)
        self.configure(fg_color=BG)
        self.files = {}
        self.checked = set()
        self.events = queue.Queue()
        self.stop = threading.Event()
        self.busy = False
        self.destination = None
        self.help_window = None
        self.query = StringVar(master=self)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_toolbar()
        self.build_queue()
        self.build_footer()
        self.query.trace_add('write', lambda *_: self.refresh_queue())
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.on_drop)
        self.dnd_bind('<<DropEnter>>', self.on_drop_enter)
        self.dnd_bind('<<DropLeave>>', lambda _: self.draw_drop())
        self.bind('<Control-o>', lambda _: self.select_files())
        self.bind('<F1>', lambda _: self.show_help())
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.refresh_queue()
        self.after(100, self.poll)

    def button(self, parent, text, command, width, primary=False):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=32,
                             corner_radius=8, fg_color=BLUE if primary else CONTROL,
                             hover_color='#9bdefb' if primary else '#35383b',
                             text_color='#101820' if primary else TEXT)

    def build_toolbar(self):
        bar = ctk.CTkFrame(self, fg_color=BG)
        bar.grid(row=0, column=0, padx=12, pady=(9, 12), sticky='ew')
        bar.grid_columnconfigure(2, weight=1)
        self.sort = ctk.CTkOptionMenu(bar, values=['Mais novos', 'Mais antigos', 'Nome', 'Maior tamanho'],
                                      command=self.refresh_queue, width=115, height=32, fg_color=CONTROL,
                                      button_color=CONTROL, button_hover_color='#35383b')
        self.sort.grid(row=0, column=0, padx=(0, 8))
        self.filter = ctk.CTkOptionMenu(bar, values=['Todos os PDFs', 'Na fila', 'Convertendo', 'Concluídos', 'Com erro', 'Cancelados'],
                                        command=self.refresh_queue, width=137, height=32, fg_color=CONTROL,
                                        button_color=CONTROL, button_hover_color='#35383b')
        self.filter.grid(row=0, column=1)
        self.pick = self.button(bar, '+  Adicionar PDFs', self.select_files, 148, primary=True)
        self.pick.grid(row=0, column=3, padx=(8, 12))
        search = ctk.CTkEntry(bar, placeholder_text='Localizar nos PDFs…', width=210,
                              height=32, corner_radius=8, fg_color=CONTROL, border_width=0)
        search.grid(row=0, column=4)
        for event in ('<KeyRelease>', '<<Paste>>', '<<Cut>>'):
            search.bind(event, lambda _: self.after_idle(lambda: self.query.set(search.get())))
        self.help_button = self.button(bar, '?', self.show_help, 32)
        self.help_button.grid(row=0, column=5, padx=(8, 0))

    def show_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.lift()
            self.help_window.focus_set()
            return
        window = ctk.CTkToplevel(self, fg_color=BG)
        self.help_window = window
        window.title('Ajuda do PDF2MD')
        window.geometry('620x455')
        window.minsize(500, 400)
        window.transient(self)
        if sys.platform == 'win32':
            window.iconbitmap(str(ASSETS / 'app.ico'))
        window.bind('<Escape>', lambda _: window.destroy())
        window.grid_columnconfigure(0, weight=1)
        window.grid_rowconfigure(1, weight=1)
        with Image.open(ASSETS / 'logo.png') as logo:
            window.logo = ctk.CTkImage(light_image=logo.copy(), size=(240, 60))
        ctk.CTkLabel(window, text='', image=window.logo).grid(row=0, column=0, padx=20, pady=(16, 8), sticky='w')
        content = ctk.CTkTextbox(window, fg_color=CONTROL, text_color=TEXT, wrap='word',
                                 font=ctk.CTkFont(size=14), padx=12, pady=10)
        content.grid(row=1, column=0, padx=20, sticky='nsew')
        command = '.\\PDF2MD-CLI.exe' if sys.platform == 'win32' else './PDF2MD-CLI'
        content.insert('1.0', (
            'No aplicativo\n'
            'Arraste PDFs para converter imediatamente ou use Adicionar PDFs para montar a fila. '
            'Escolha uma pasta de destino antes de converter. Por padrão, o Markdown é salvo ao lado de cada PDF.\n\n'
            'No terminal\n'
            'Na pasta que contém o CLI, execute:\n\n'
            f'{command} --help\n'
            f'{command} -o "markdown" "arquivo.pdf"\n\n'
            'Você pode informar vários PDFs. A opção -o é opcional. '
            'O CLI é distribuído em um pacote separado.\n\n'
            'A conversão é local e preserva arquivos existentes. PDFs digitalizados sem texto precisam de OCR.'
        ))
        content.configure(state='disabled')
        self.button(window, 'Fechar', window.destroy, 88).grid(row=2, column=0, padx=20, pady=14, sticky='e')
        window.focus_set()

    def build_queue(self):
        self.body = ctk.CTkFrame(self, fg_color=BG)
        self.body.grid(row=1, column=0, padx=12, sticky='nsew')
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_rowconfigure(1, weight=1)
        self.body.bind('<Configure>', lambda _: self.fit_queue())
        self.table = ctk.CTkFrame(self.body, fg_color=BG)
        self.table.grid(row=0, column=0, sticky='ew')
        self.table.grid_columnconfigure(0, weight=1)
        self.table.grid_rowconfigure(0, weight=1)
        style = ttk.Style(self)
        style.theme_use('clam')
        row_height = round(self.body._apply_widget_scaling(ROW_HEIGHT))
        style.configure('PDF.Treeview', background=BG, fieldbackground=BG, foreground=TEXT,
                        rowheight=row_height, borderwidth=0, bordercolor=BG, lightcolor=BG,
                        darkcolor=BG, relief='flat', font=('Segoe UI', 10))
        style.configure('PDF.Treeview.Heading', background=BG, foreground=MUTED, relief='flat',
                        borderwidth=0, padding=(4, 6), font=('Segoe UI', 10))
        style.map('PDF.Treeview', background=[('selected', '#292c30')], foreground=[('selected', TEXT)])
        style.map('PDF.Treeview.Heading', background=[('active', CONTROL)])
        self.tree = ttk.Treeview(self.table, columns=('name', 'size', 'state', 'added'),
                                 style='PDF.Treeview', height=1, selectmode='browse')
        self.tree.grid(row=0, column=0, sticky='nsew')
        self.checkbox_icons = {checked: self.checkbox_icon(checked) for checked in (False, True)}
        self.tree.heading('#0', text='□', command=self.toggle_all)
        self.tree.column('#0', width=round(self.body._apply_widget_scaling(36)), stretch=False, anchor='center')
        for column, label, width in [('name', 'Nome', 375), ('size', 'Tamanho', 95),
                                     ('state', 'Estado', 135), ('added', 'Adicionado', 145)]:
            self.tree.heading(column, text=label, anchor='w')
            self.tree.column(column, width=round(self.body._apply_widget_scaling(width)), stretch=column == 'name')
        self.tree.tag_configure('Concluído', foreground=BLUE)
        self.tree.tag_configure('Erro', foreground='#ff8f91')
        self.tree.tag_configure('Convertendo', foreground='#f8cd82')
        self.tree.tag_configure('Cancelado', foreground=MUTED)
        scrollbar = ctk.CTkScrollbar(self.table, orientation='vertical', command=self.tree.yview,
                                     width=12, fg_color=BG, button_color='#36393c', button_hover_color='#53575b')
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind('<Button-1>', self.on_table_click)
        self.tree.bind('<space>', self.on_table_space)
        self.tree.bind('<<TreeviewSelect>>', lambda _: self.update_detail())
        self.tree.bind('<Double-1>', self.show_detail)
        self.tree.bind('<Return>', self.show_detail)
        self.drop = Canvas(self.body, bg=BG, highlightthickness=0, height=1)
        self.drop.grid(row=1, column=0, pady=(8, 10), sticky='nsew')
        self.drop.bind('<Configure>', lambda _: self.draw_drop())

    def checkbox_icon(self, checked):
        size = round(self.body._apply_widget_scaling(16))
        icon = Image.new('RGBA', (64, 64))
        draw = ImageDraw.Draw(icon)
        draw.rounded_rectangle((3, 3, 60, 60), radius=13, width=4,
                               outline=BLUE if checked else '#555a60', fill=BLUE if checked else CONTROL)
        if checked:
            draw.line([(15, 31), (26, 42), (48, 20)], width=7, fill=BG, joint='curve')
        return ImageTk.PhotoImage(icon.resize((size, size), Image.Resampling.LANCZOS), master=self)

    def build_footer(self):
        footer = ctk.CTkFrame(self, fg_color=BG)
        footer.grid(row=2, column=0, sticky='ew')
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkFrame(footer, height=1, fg_color=CONTROL).grid(row=0, column=0, sticky='ew')
        options = ctk.CTkFrame(footer, fg_color=BG)
        options.grid(row=1, column=0, padx=12, pady=(8, 5), sticky='ew')
        options.grid_columnconfigure(0, weight=1)
        self.folder_label = ctk.CTkLabel(options, text='Destino: mesma pasta de cada PDF', text_color=MUTED, anchor='w', width=1)
        self.folder_label.grid(row=0, column=0, padx=(0, 8), sticky='ew')
        self.folder = self.button(options, 'Escolher pasta', self.choose_folder, 112)
        self.reset = self.button(options, 'Restaurar', self.reset_folder, 78)
        self.clear = self.button(options, 'Limpar fila', self.clear_files, 83)
        self.cancel = self.button(options, 'Cancelar', self.stop.set, 78)
        self.convert = self.button(options, 'Converter para Markdown', self.start, 184, primary=True)
        for column, button in enumerate((self.folder, self.reset, self.clear, self.cancel, self.convert), 1):
            button.grid(row=0, column=column, padx=(0, 6))
        self.cancel.configure(state='disabled')
        self.progress = ctk.CTkProgressBar(footer, height=3, fg_color=CONTROL, progress_color=BLUE)
        self.progress.grid(row=2, column=0, padx=12, sticky='ew')
        self.progress.set(0)
        statusbar = ctk.CTkFrame(footer, fg_color=BG)
        statusbar.grid(row=3, column=0, padx=12, pady=(1, 3), sticky='ew')
        statusbar.grid_columnconfigure(1, weight=1)
        self.status = ctk.CTkLabel(statusbar, text='Pronto', text_color=MUTED, anchor='w', height=24)
        self.status.grid(row=0, column=0, sticky='w')
        self.detail = ctk.CTkLabel(statusbar, text='', text_color=MUTED, anchor='e', width=1, height=24)
        self.detail.grid(row=0, column=1, padx=(12, 0), sticky='ew')

    def fit_queue(self):
        if not hasattr(self, 'drop'):
            return
        row_height = self.body._apply_widget_scaling(ROW_HEIGHT)
        available = max(1, int((self.body.winfo_height() - row_height * 4.6) / row_height))
        height = min(len(self.tree.get_children()), available)
        self.tree.configure(height=max(1, height))

    def draw_drop(self, active=False):
        canvas = self.drop
        canvas.delete('all')
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 36 or h < 36:
            return
        color = BLUE if active else '#42464b'
        canvas.create_polygon(3, 17, 3, 3, 17, 3, w-17, 3, w-3, 3, w-3, 17,
                              w-3, h-17, w-3, h-3, w-17, h-3, 17, h-3, 3, h-3, 3, h-17,
                              smooth=True, fill='', outline=color, width=2, dash=(17, 5))
        label = 'Solte para converter' if active else 'Arraste e solte um ou mais PDFs para converter'
        canvas.create_text(w/2, h/2, text=f'⇩  {label}', fill=BLUE if active else MUTED, font=('Segoe UI', 12))

    def refresh_queue(self, *_):
        selected = self.tree.selection()
        offset = self.tree.yview()[0]
        query = self.query.get().strip().casefold()
        state = {'Na fila': 'Na fila', 'Convertendo': 'Convertendo', 'Concluídos': 'Concluído',
                 'Com erro': 'Erro', 'Cancelados': 'Cancelado'}.get(self.filter.get())
        paths = [path for path, entry in self.files.items()
                 if query in path.name.casefold() and (state is None or entry.state == state)]
        order = self.sort.get()
        if order == 'Nome':
            paths.sort(key=lambda path: path.name.casefold())
        elif order == 'Maior tamanho':
            paths.sort(key=lambda path: self.files[path].size, reverse=True)
        elif order == 'Mais novos':
            paths.reverse()
        self.tree.delete(*self.tree.get_children())
        for path in paths:
            entry = self.files[path]
            size = f'{entry.size / 1048576:.1f} MB' if entry.size >= 1048576 else f'{entry.size / 1024:.1f} KB'
            self.tree.insert('', 'end', iid=str(path), image=self.checkbox_icons[path in self.checked],
                             values=(path.name, size.replace('.', ','), entry.state, entry.added.strftime('%d/%m %H:%M')),
                             tags=(entry.state,))
        if paths:
            self.table.grid()
        else:
            self.table.grid_remove()
        if selected and self.tree.exists(selected[0]):
            self.tree.selection_set(selected)
        self.tree.yview_moveto(offset)
        self.fit_queue()
        self.update_selection()

    def toggle_all(self):
        if self.busy:
            return
        visible = {Path(item) for item in self.tree.get_children()}
        if visible <= self.checked:
            self.checked.difference_update(visible)
        else:
            self.checked.update(visible)
        self.update_selection()

    def toggle(self, item):
        if self.busy or not item:
            return
        path = Path(item)
        if path in self.checked:
            self.checked.remove(path)
        else:
            self.checked.add(path)
        self.update_selection()

    def on_table_click(self, event):
        if self.tree.identify_region(event.x, event.y) == 'tree':
            self.toggle(self.tree.identify_row(event.y))
            return 'break'
        return None

    def on_table_space(self, _):
        self.toggle(self.tree.focus())
        return 'break'

    def update_selection(self):
        rows = self.tree.get_children()
        all_checked = bool(rows) and all(Path(item) in self.checked for item in rows)
        self.tree.heading('#0', text='', image=self.checkbox_icons[all_checked])
        for item in rows:
            self.tree.item(item, image=self.checkbox_icons[Path(item) in self.checked])
        self.convert.configure(text=f'Converter {len(self.checked)} selecionado(s)' if self.checked else 'Converter para Markdown',
                               state='normal' if self.files and not self.busy else 'disabled')
        self.clear.configure(state='normal' if self.files and not self.busy else 'disabled')
        self.update_detail()

    def update_detail(self):
        selected = self.tree.selection()
        entry = self.files.get(Path(selected[0])) if selected else None
        if entry and entry.detail:
            text = entry.detail
        elif self.checked:
            text = f'{len(self.checked)} PDF(s) selecionado(s)'
        elif self.files:
            text = f'{len(self.tree.get_children())} de {len(self.files)} PDF(s)'
        else:
            text = 'PDF → Markdown'
        self.detail.configure(text=text)

    def show_detail(self, event):
        if event.type.name == 'ButtonPress' and self.tree.identify_region(event.x, event.y) != 'cell':
            return
        selected = self.tree.selection()
        if selected:
            path = Path(selected[0])
            entry = self.files[path]
            messagebox.showinfo(entry.state, entry.detail or str(path), parent=self)

    def select_files(self):
        if not self.busy:
            paths = filedialog.askopenfilenames(parent=self, filetypes=[('Documentos PDF', '*.pdf')])
            if paths:
                self.add_files(paths)

    def on_drop_enter(self, _):
        if self.busy:
            return 'refuse_drop'
        self.draw_drop(active=True)
        return 'copy'

    def on_drop(self, event):
        self.draw_drop()
        if self.busy:
            return 'refuse_drop'
        paths = self.add_files(self.tk.splitlist(event.data))
        self.start_conversion(paths)
        return 'copy'

    def add_files(self, paths):
        accepted = {}
        rejected = 0
        for value in paths:
            try:
                path = Path(value).resolve()
                if path.suffix.lower() != '.pdf' or not path.is_file():
                    rejected += 1
                    continue
                if path not in self.files:
                    self.files[path] = FileEntry(path.stat().st_size, datetime.now())
                accepted[path] = None
            except (OSError, ValueError):
                rejected += 1
        self.refresh_queue()
        message = f'{len(self.files)} PDF(s) na fila'
        if rejected:
            message += f' · {rejected} item(ns) ignorado(s)'
        self.status.configure(text=message)
        return list(accepted)

    def choose_folder(self):
        folder = filedialog.askdirectory(parent=self)
        if folder:
            self.destination = Path(folder)
            self.folder_label.configure(text=f'Destino: {folder}')

    def reset_folder(self):
        self.destination = None
        self.folder_label.configure(text='Destino: mesma pasta de cada PDF')

    def clear_files(self):
        self.files.clear()
        self.checked.clear()
        self.refresh_queue()
        self.progress.set(0)
        self.status.configure(text='Fila limpa')

    def start(self):
        self.start_conversion([path for path in self.files if not self.checked or path in self.checked])

    def start_conversion(self, paths):
        if self.busy or not paths:
            return
        self.busy = True
        self.stop.clear()
        for widget in (self.pick, self.folder, self.reset, self.clear, self.convert):
            widget.configure(state='disabled')
        self.cancel.configure(state='normal')
        self.progress.set(0)
        for path in paths:
            self.files[path].state = 'Na fila'
            self.files[path].detail = ''
        self.refresh_queue()
        threading.Thread(target=self.worker, args=(paths, self.destination), daemon=True).start()

    def worker(self, paths, destination):
        success = failed = 0
        for index, path in enumerate(paths):
            if self.stop.is_set():
                break
            self.events.put(('working', path))
            try:
                output = convert_pdf(path, destination or path.parent)
                success += 1
                self.events.put(('result', path, f'Salvo: {output}', True, index + 1, len(paths)))
            except Exception as exc:
                failed += 1
                self.events.put(('result', path, str(exc), False, index + 1, len(paths)))
        pending = paths[success + failed:]
        self.events.put(('done', success, failed, self.stop.is_set(), pending))

    def poll(self):
        changed = False
        try:
            while True:
                event = self.events.get_nowait()
                changed = True
                if event[0] == 'working':
                    self.files[event[1]].state = 'Convertendo'
                    self.status.configure(text=f'Convertendo: {event[1].name}')
                elif event[0] == 'result':
                    entry = self.files[event[1]]
                    entry.state = 'Concluído' if event[3] else 'Erro'
                    entry.detail = event[2]
                    self.progress.set(event[4] / event[5])
                elif event[0] == 'done':
                    self.busy = False
                    for widget in (self.pick, self.folder, self.reset):
                        widget.configure(state='normal')
                    self.cancel.configure(state='disabled')
                    label = 'Cancelado' if event[3] else 'Concluído'
                    self.status.configure(text=f'{label} · {event[1]} convertido(s), {event[2]} erro(s)')
                    for path in event[4]:
                        self.files[path].state = 'Cancelado'
        except queue.Empty:
            pass
        if changed:
            self.refresh_queue()
        self.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo('Conversão em andamento', 'Cancele e aguarde o arquivo atual terminar antes de fechar.', parent=self)
            return
        self.destroy()


if __name__ == '__main__':
    ctk.set_appearance_mode('dark')
    ctk.set_default_color_theme('blue')
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-test':
        from smoke_test import run
        try:
            run(sys.argv[2])
        except Exception:
            import traceback
            Path(sys.argv[2]).write_text(traceback.format_exc(), encoding='utf-8')
            raise
    else:
        App().mainloop()

