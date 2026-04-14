

from ai import SIZE, AI, HUMAN, check_winner, is_full


class Game:
    """
    Oyun durumunu tutan sınıf.

    Özellikler:
        board       : 5x5 tahta (None | 'X' | 'O')
        current     : sıradaki oyuncunun işareti ('X' veya 'O')
        player_mark : insan oyuncunun işareti
        ai_mark     : yapay zekanın işareti
        winner      : kazanan işaret (None, 'X', 'O', veya 'draw')
        win_line    : kazanan hücrelerin listesi
        move_count  : toplam hamle sayısı
        history     : hamle geçmişi listesi
    """

    def __init__(self, player_mark='X'):
        self.player_mark = player_mark
        self.ai_mark     = AI if player_mark == HUMAN else HUMAN
        self.reset()

    def reset(self):
        """Oyunu sıfırlar."""
        self.board      = [[None] * SIZE for _ in range(SIZE)]
        self.current    = 'X'          # X her zaman ilk oynar
        self.winner     = None         # None | 'X' | 'O' | 'draw'
        self.win_line   = None
        self.move_count = 0
        self.history    = []           # [(r, c, mark), ...]

    def is_over(self):
        """Oyun bittiyse True döner."""
        return self.winner is not None

    def is_player_turn(self):
        """İnsan oyuncunun sırası ise True döner."""
        return self.current == self.player_mark and not self.is_over()

    def is_ai_turn(self):
        """AI'nın sırası ise True döner."""
        return self.current == self.ai_mark and not self.is_over()

    def make_move(self, r, c):
        """
        (r, c) konumuna mevcut oyuncunun işaretini koyar.

        Dönüş değeri:
            True  → hamle başarıyla yapıldı
            False → geçersiz hamle (hücre doluydu)
        """
        if self.board[r][c] is not None or self.is_over():
            return False

        mark = self.current
        self.board[r][c] = mark
        self.move_count  += 1
        self.history.append((r, c, mark))

        # Kazanan kontrolü
        win_line = check_winner(self.board, mark)
        if win_line:
            self.winner   = mark
            self.win_line = win_line
        elif is_full(self.board):
            self.winner = 'draw'
        else:
            # Sırayı değiştir
            self.current = AI if self.current == HUMAN else HUMAN

        return True

    def empty_cells_count(self):
        """Boş hücre sayısını döndürür."""
        return sum(1 for r in range(SIZE) for c in range(SIZE) if self.board[r][c] is None)

    def get_result_text(self):
        """Oyun sonucunu Türkçe metin olarak döndürür."""
        if self.winner == self.player_mark:
            return '🎉 Kazandınız!'
        elif self.winner == self.ai_mark:
            return '🤖 AI Kazandı!'
        elif self.winner == 'draw':
            return '🤝 Beraberlik!'
        return ''
