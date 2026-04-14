

import tkinter as tk
from tkinter import ttk, font
import threading
import time

from game import Game
from ai   import get_best_move, SIZE, AI, HUMAN

# ── Renk paleti ───────────────────────────────────────────────────────────────
BG       = '#0d0f14'   # Ana arka plan (koyu lacivert)
SURFACE  = '#161a22'   # Panel arka planı
SURFACE2 = '#1e2430'   # Hücre arka planı
BORDER   = '#2a3040'   # Kenarlık rengi
GOLD     = '#e8c547'   # AI / sarı vurgu
BLUE     = '#4fc3f7'   # Oyuncu / mavi vurgu
GREEN    = '#4caf50'   # Kazanma rengi
MUTED    = '#6b7280'   # Soluk metin
TEXT     = '#e8eaf0'   # Ana metin
WIN_CELL = '#1a3a1a'   # Kazanan hücre arka planı


class TicTacToeApp(tk.Tk):
    """Ana uygulama penceresi."""

    def __init__(self):
        super().__init__()
        self.title('5×5 Strategic AI — Minimax + Alpha-Beta Pruning')
        self.configure(bg=BG)
        self.resizable(False, False)

        # Oyun nesnesi
        self.game       = Game(player_mark='X')
        self.difficulty = tk.StringVar(value='Orta')
        self.player_var = tk.StringVar(value='X')

        # Hücre butonlarını tutacak 2D liste
        self.cells = [[None] * SIZE for _ in range(SIZE)]

        self._build_ui()
        self._update_status()

    # ── Arayüz oluşturma ──────────────────────────────────────────────────────
    def _build_ui(self):
        """Tüm widget'ları oluşturur ve yerleştirir."""

        # Ana çerçeve: sol (tahta) + sağ (paneller)
        main = tk.Frame(self, bg=BG, padx=16, pady=16)
        main.pack()

        # ── Başlık ──
        title_frame = tk.Frame(main, bg=BG)
        title_frame.grid(row=0, column=0, columnspan=2, pady=(0, 12), sticky='w')

        tk.Label(title_frame, text='5×5 Strategic AI',
                 bg=BG, fg=TEXT, font=('Arial', 20, 'bold')).pack(side='left')

        tk.Label(title_frame,
                 text='  //  Minimax + Alpha-Beta Pruning · 4\'lü dizi için kazan',
                 bg=BG, fg=MUTED, font=('Courier', 10)).pack(side='left', padx=8)

        # ── Sol sütun: kontroller + tahta ──
        left = tk.Frame(main, bg=BG)
        left.grid(row=1, column=0, padx=(0, 16), sticky='n')

        self._build_controls(left)
        self._build_status_bar(left)
        self._build_board(left)
        self._build_legend(left)

        # ── Sağ sütun: paneller ──
        right = tk.Frame(main, bg=BG)
        right.grid(row=1, column=1, sticky='n')

        self._build_score_panel(right)
        self._build_stats_panel(right)
        self._build_log_panel(right)

    def _build_controls(self, parent):
        """Zorluk, oyuncu seçimi ve yeni oyun butonları."""
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill='x', pady=(0, 8))

        # Zorluk
        tk.Label(frame, text='Zorluk:', bg=BG, fg=MUTED,
                 font=('Courier', 9)).pack(side='left')

        diff_cb = ttk.Combobox(frame, textvariable=self.difficulty,
                               values=['Kolay', 'Orta', 'Zor'],
                               state='readonly', width=8,
                               font=('Courier', 9))
        diff_cb.pack(side='left', padx=(4, 16))

        # Oyuncu seçimi
        tk.Label(frame, text='Sen:', bg=BG, fg=MUTED,
                 font=('Courier', 9)).pack(side='left')

        self.btn_x = tk.Button(frame, text='X (önce)', font=('Arial', 9, 'bold'),
                               command=lambda: self._set_player('X'),
                               bg=GOLD, fg='#000', relief='flat',
                               padx=8, pady=3, cursor='hand2')
        self.btn_x.pack(side='left', padx=4)

        self.btn_o = tk.Button(frame, text='O (sonra)', font=('Arial', 9, 'bold'),
                               command=lambda: self._set_player('O'),
                               bg=SURFACE2, fg=TEXT, relief='flat',
                               padx=8, pady=3, cursor='hand2')
        self.btn_o.pack(side='left', padx=4)

        # Yeni oyun
        tk.Button(frame, text='↺  Yeni Oyun', font=('Arial', 9, 'bold'),
                  command=self._reset_game,
                  bg=SURFACE2, fg=TEXT, relief='flat',
                  padx=10, pady=3, cursor='hand2',
                  activebackground='#2a1a1a', activeforeground='#ef5350').pack(
                      side='right')

    def _build_status_bar(self, parent):
        """Durum çubuğu: sıra ve hamle bilgisi."""
        self.status_frame = tk.Frame(parent, bg=SURFACE, pady=8, padx=12)
        self.status_frame.pack(fill='x', pady=(0, 8))

        # Sol: renkli nokta + metin
        left = tk.Frame(self.status_frame, bg=SURFACE)
        left.pack(side='left')

        self.status_dot = tk.Canvas(left, width=10, height=10, bg=SURFACE,
                                    highlightthickness=0)
        self.status_dot.pack(side='left', padx=(0, 8))

        self.status_label = tk.Label(left, text='Senin sıran — X koy',
                                     bg=SURFACE, fg=TEXT,
                                     font=('Arial', 11, 'bold'))
        self.status_label.pack(side='left')

        # Sağ: hamle numarası
        self.status_sub = tk.Label(self.status_frame, text='hamle 0 · 5×5 tahta',
                                   bg=SURFACE, fg=MUTED, font=('Courier', 9))
        self.status_sub.pack(side='right')

    def _build_board(self, parent):
        """5×5 tahta butonlarını oluşturur."""
        board_frame = tk.Frame(parent, bg=BORDER, padx=4, pady=4)
        board_frame.pack()

        for r in range(SIZE):
            for c in range(SIZE):
                btn = tk.Button(
                    board_frame,
                    text='',
                    width=4, height=2,
                    font=('Courier', 20, 'bold'),
                    bg=SURFACE2, fg=TEXT,
                    relief='flat',
                    cursor='hand2',
                    command=lambda row=r, col=c: self._on_cell_click(row, col)
                )
                btn.grid(row=r, column=c, padx=3, pady=3)
                self.cells[r][c] = btn

                # Hover efektleri
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#252d3d')
                         if b['text'] == '' else None)
                btn.bind('<Leave>', lambda e, b=btn: b.config(bg=SURFACE2)
                         if b['bg'] == '#252d3d' else None)

    def _build_legend(self, parent):
        """Renk açıklamaları."""
        frame = tk.Frame(parent, bg=BG)
        frame.pack(pady=(8, 0), anchor='w')

        for color, label in [(BLUE, 'Sen (X)'), (GOLD, 'AI (O)'), (GREEN, 'Kazanma çizgisi')]:
            dot = tk.Canvas(frame, width=8, height=8, bg=BG, highlightthickness=0)
            dot.create_oval(1, 1, 7, 7, fill=color, outline='')
            dot.pack(side='left', padx=(0, 4))
            tk.Label(frame, text=label, bg=BG, fg=MUTED,
                     font=('Courier', 9)).pack(side='left', padx=(0, 12))

    def _build_score_panel(self, parent):
        """Skor paneli."""
        panel = self._panel(parent, 'SKOR TABLOSU')

        score_row = tk.Frame(panel, bg=SURFACE)
        score_row.pack(fill='x')

        self.lbl_you  = self._score_box(score_row, 'SEN',    '0', BLUE)
        self.lbl_draw = self._score_box(score_row, 'BERABERLIK', '0', MUTED)
        self.lbl_ai   = self._score_box(score_row, 'AI',     '0', GOLD)

    def _build_stats_panel(self, parent):
        """Algoritma istatistikleri paneli."""
        panel = self._panel(parent, 'ALGORİTMA İSTATİSTİKLERİ')

        self.stat_nodes  = self._stat_row(panel, 'Değerlendirilen düğüm', BLUE)
        self.stat_pruned = self._stat_row(panel, 'Budanan dal',           GOLD)
        self.stat_eff    = self._stat_row(panel, 'Budama verimliliği',    GREEN)
        self.stat_time   = self._stat_row(panel, 'Düşünme süresi',        TEXT)
        self.stat_score  = self._stat_row(panel, 'En iyi skor',           TEXT)
        self.stat_depth  = self._stat_row(panel, 'Arama derinliği',       TEXT)

        # İlerleme çubuğu
        tk.Label(panel, text='budama tasarrufu:', bg=SURFACE, fg=MUTED,
                 font=('Courier', 8)).pack(anchor='w', pady=(4, 0))
        self.progress_bar = ttk.Progressbar(panel, maximum=100, length=200)
        self.progress_bar.pack(fill='x', pady=(2, 4))

    def _build_log_panel(self, parent):
        """Hamle geçmişi paneli."""
        panel = self._panel(parent, 'HAMLE GEÇMİŞİ')

        self.log_text = tk.Text(panel, width=26, height=8,
                                bg=SURFACE2, fg=MUTED,
                                font=('Courier', 9), relief='flat',
                                state='disabled', wrap='none')
        self.log_text.pack(fill='both')
        self._log('// oyun başlamadı')

    # ── Yardımcı widget oluşturucular ─────────────────────────────────────────
    def _panel(self, parent, title):
        """Başlıklı panel çerçevesi döndürür."""
        outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        outer.pack(fill='x', pady=(0, 8))
        inner = tk.Frame(outer, bg=SURFACE, padx=12, pady=10)
        inner.pack(fill='both')
        tk.Label(inner, text=title, bg=SURFACE, fg=MUTED,
                 font=('Courier', 8, 'bold')).pack(anchor='w', pady=(0, 6))
        return inner

    def _score_box(self, parent, label, value, color):
        """Skor kutusu (etiket + büyük sayı)."""
        frame = tk.Frame(parent, bg=SURFACE2, padx=12, pady=8)
        frame.pack(side='left', expand=True, fill='both', padx=3)
        tk.Label(frame, text=label, bg=SURFACE2, fg=MUTED,
                 font=('Courier', 8)).pack()
        lbl = tk.Label(frame, text=value, bg=SURFACE2, fg=color,
                       font=('Arial', 22, 'bold'))
        lbl.pack()
        return lbl

    def _stat_row(self, parent, label, color):
        """İstatistik satırı (solda etiket, sağda değer)."""
        frame = tk.Frame(parent, bg=SURFACE)
        frame.pack(fill='x', pady=1)
        tk.Label(frame, text=label, bg=SURFACE, fg=MUTED,
                 font=('Courier', 9)).pack(side='left')
        val = tk.Label(frame, text='—', bg=SURFACE, fg=color,
                       font=('Courier', 11, 'bold'))
        val.pack(side='right')
        return val

    # ── Olaylar ───────────────────────────────────────────────────────────────
    def _set_player(self, mark):
        """Oyuncu işareti değiştiğinde çağrılır."""
        self.player_var.set(mark)
        if mark == 'X':
            self.btn_x.config(bg=GOLD, fg='#000')
            self.btn_o.config(bg=SURFACE2, fg=TEXT)
        else:
            self.btn_o.config(bg=GOLD, fg='#000')
            self.btn_x.config(bg=SURFACE2, fg=TEXT)
        self._reset_game()

    def _reset_game(self):
        """Oyunu ve arayüzü sıfırlar."""
        self.game = Game(player_mark=self.player_var.get())
        # Tahtayı temizle
        for r in range(SIZE):
            for c in range(SIZE):
                self.cells[r][c].config(text='', bg=SURFACE2, fg=TEXT,
                                        state='normal', cursor='hand2')
        # İstatistikleri temizle
        for lbl in (self.stat_nodes, self.stat_pruned, self.stat_eff,
                    self.stat_time, self.stat_score, self.stat_depth):
            lbl.config(text='—')
        self.progress_bar['value'] = 0
        # Logu temizle
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')
        self._log('// yeni oyun')

        self._update_status()

        # AI önce oynayacaksa başlat
        if self.game.is_ai_turn():
            self.after(400, self._trigger_ai)

    def _on_cell_click(self, r, c):
        """Kullanıcı bir hücreye tıkladığında çağrılır."""
        if not self.game.is_player_turn():
            return
        if self.game.board[r][c] is not None:
            return

        self._place_move(r, c)

    def _place_move(self, r, c):
        """Hamleyi uygular ve arayüzü günceller."""
        mark = self.game.current
        ok   = self.game.make_move(r, c)
        if not ok:
            return

        # Hücreyi güncelle
        color = BLUE if mark == self.game.player_mark else GOLD
        self.cells[r][c].config(text=mark, fg=color, cursor='arrow',
                                state='disabled')

        # Hamle logunu güncelle
        col_label = chr(65 + r) + str(c + 1)   # örn: A1, C3
        kim = 'Sen' if mark == self.game.player_mark else 'AI '
        self._log(f'#{self.game.move_count:02d}  {kim}  {mark}  →  {col_label}')

        # Oyun bitti mi?
        if self.game.is_over():
            self._on_game_over()
            return

        self._update_status()

        # AI sırası ise tetikle
        if self.game.is_ai_turn():
            self.after(150, self._trigger_ai)

    def _trigger_ai(self):
        """AI hamlesi için arka plan thread'i başlatır."""
        if not self.game.is_ai_turn():
            return

        self.status_label.config(text='🤖 AI düşünüyor…', fg=GOLD)
        # Tahtayı devre dışı bırak
        self._set_board_state('disabled')

        def ai_thread():
            t_start = time.time()
            move, stats = get_best_move(
                self.game.board,
                difficulty=self.difficulty.get()
            )
            elapsed = (time.time() - t_start) * 1000   # ms cinsinden
            # GUI güncellemesi ana thread'de yapılmalı
            self.after(0, lambda: self._on_ai_done(move, stats, elapsed))

        threading.Thread(target=ai_thread, daemon=True).start()

    def _on_ai_done(self, move, stats, elapsed_ms):
        """AI hamlesi tamamlandığında ana thread'de çağrılır."""
        # İstatistikleri güncelle
        nodes  = stats['nodes']
        pruned = stats['pruned']
        total  = nodes + pruned
        eff    = round(pruned / total * 100) if total > 0 else 0

        self.stat_nodes.config(text=f'{nodes:,}')
        self.stat_pruned.config(text=f'{pruned:,}')
        self.stat_eff.config(text=f'{eff}%')
        self.stat_time.config(text=f'{elapsed_ms:.1f} ms')

        score = stats.get('score', 0)
        if score >  50_000:
            score_txt = '+KAZANÇ'
        elif score < -50_000:
            score_txt = '−KAYIP'
        else:
            score_txt = str(score)
        self.stat_score.config(text=score_txt)
        self.stat_depth.config(text=str(DEPTH_MAP_UI.get(self.difficulty.get(), 4)))
        self.progress_bar['value'] = eff

        # Tahtayı yeniden etkinleştir
        self._set_board_state('normal')
        # Hamleyi uygula
        self._place_move(*move)

    def _on_game_over(self):
        """Oyun bitişini işler."""
        result = self.game.get_result_text()
        self.status_label.config(text=result, fg=GREEN)
        self.status_sub.config(text=f'{self.game.move_count} hamle oynandı')

        # Skorları güncelle
        winner = self.game.winner
        player = self.game.player_mark

        if winner == player:
            old = int(self.lbl_you.cget('text'))
            self.lbl_you.config(text=str(old + 1))
        elif winner == 'draw':
            old = int(self.lbl_draw.cget('text'))
            self.lbl_draw.config(text=str(old + 1))
        else:
            old = int(self.lbl_ai.cget('text'))
            self.lbl_ai.config(text=str(old + 1))

        # Kazanan çizgiyi vurgula
        if self.game.win_line:
            for r, c in self.game.win_line:
                self.cells[r][c].config(bg=WIN_CELL, fg=GREEN)

        # Tüm hücreleri devre dışı bırak
        self._set_board_state('disabled')

    def _set_board_state(self, state):
        """Tahta üzerindeki boş hücrelerin durumunu değiştirir."""
        for r in range(SIZE):
            for c in range(SIZE):
                if self.game.board[r][c] is None:
                    self.cells[r][c].config(
                        state=state,
                        cursor='hand2' if state == 'normal' else 'arrow'
                    )

    def _update_status(self):
        """Durum çubuğunu günceller."""
        if self.game.is_over():
            return

        dot  = self.status_dot
        dot.delete('all')

        if self.game.is_player_turn():
            dot.create_oval(1, 1, 9, 9, fill=BLUE, outline='')
            self.status_label.config(
                text=f'Senin sıran — {self.game.player_mark} koy', fg=TEXT)
        else:
            dot.create_oval(1, 1, 9, 9, fill=GOLD, outline='')
            self.status_label.config(text='AI sırasında…', fg=GOLD)

        empty = self.game.empty_cells_count()
        self.status_sub.config(
            text=f'hamle {self.game.move_count + 1} · {empty} boş hücre')

    def _log(self, text):
        """Hamle log penceresine satır ekler."""
        self.log_text.config(state='normal')
        self.log_text.insert('1.0', text + '\n')   # Yeni satırlar üste eklenir
        self.log_text.config(state='disabled')


# Derinlik haritası (istatistik panelinde göstermek için)
DEPTH_MAP_UI = {'Kolay': 2, 'Orta': 4, 'Zor': 6}
