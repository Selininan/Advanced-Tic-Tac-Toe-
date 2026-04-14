

import math

# ── Sabitler ──────────────────────────────────────────────────────────────────
SIZE   = 5   # Tahta boyutu
WIN    = 4   # Kazanmak için gereken ardışık işaret sayısı
AI     = 'O' # Yapay zekanın işareti
HUMAN  = 'X' # İnsanın işareti

# Zorluk seviyelerine göre arama derinliği
DEPTH_MAP = {
    'Kolay':  2,
    'Orta':   4,
    'Zor':    6,
}


# ── Tüm kazanma çizgilerini üret ──────────────────────────────────────────────
def get_all_lines():
    """
    5x5 tahta üzerindeki tüm olası 4'lü dizileri döndürür.
    Satır, sütun, ana köşegen ve ters köşegen yönlerinde.
    """
    lines = []

    # Yatay satırlar
    for r in range(SIZE):
        for c in range(SIZE - WIN + 1):
            lines.append([(r, c + k) for k in range(WIN)])

    # Dikey sütunlar
    for c in range(SIZE):
        for r in range(SIZE - WIN + 1):
            lines.append([(r + k, c) for k in range(WIN)])

    # Ana köşegen (sol üst → sağ alt) ↘
    for r in range(SIZE - WIN + 1):
        for c in range(SIZE - WIN + 1):
            lines.append([(r + k, c + k) for k in range(WIN)])

    # Ters köşegen (sağ üst → sol alt) ↙
    for r in range(SIZE - WIN + 1):
        for c in range(WIN - 1, SIZE):
            lines.append([(r + k, c - k) for k in range(WIN)])

    return lines


ALL_LINES = get_all_lines()  # Bir kere hesaplanır, tekrar kullanılır


# ── Kazanan kontrolü ──────────────────────────────────────────────────────────
def check_winner(board, mark):
    """
    board: 5x5 liste (board[r][c] = 'X' | 'O' | None)
    mark:  kontrol edilecek işaret ('X' veya 'O')
    Kazanan çizgiyi (hücre listesi) döndürür, yoksa None.
    """
    for line in ALL_LINES:
        if all(board[r][c] == mark for r, c in line):
            return line
    return None


def is_full(board):
    """Tahtada boş hücre kalmadıysa True döner."""
    return all(board[r][c] is not None for r in range(SIZE) for c in range(SIZE))


def get_empty_cells(board):
    """Boş hücrelerin (r, c) listesini döndürür."""
    return [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] is None]


# ── Sezgisel değerlendirme fonksiyonu ────────────────────────────────────────
def evaluate(board):
    """
    Terminal olmayan tahta konumları için puan hesaplar.

    Her 4'lü pencere incelenir:
    - Sadece AI işareti varsa:    +10^(işaret sayısı)
    - Sadece insan işareti varsa: -10^(işaret sayısı) * 1.2  (savunma ağırlığı)
    - Karışık pencereler: 0 puan (kazanılamaz)
    """
    score = 0
    for line in ALL_LINES:
        marks = [board[r][c] for r, c in line]
        ai_count    = marks.count(AI)
        human_count = marks.count(HUMAN)

        if human_count == 0 and ai_count > 0:
            score += 10 ** ai_count          # AI için olumlu
        elif ai_count == 0 and human_count > 0:
            score -= (10 ** human_count) * 1.2  # İnsan tehdidi (savunmacı ağırlık)
    return score


# ── Minimax + Alpha-Beta Pruning ──────────────────────────────────────────────
def minimax(board, depth, alpha, beta, is_maximizing, stats):
    """
    Minimax algoritması — Alpha-Beta Pruning ile optimize edilmiş.

    Parametreler:
        board          : mevcut tahta durumu
        depth          : kalan arama derinliği
        alpha          : maximizer'ın şu ana kadar bulduğu en iyi değer
        beta           : minimizer'ın şu ana kadar bulduğu en iyi değer
        is_maximizing  : True → AI oynuyor, False → insan oynuyor
        stats          : {'nodes': int, 'pruned': int}  — istatistik sözlüğü

    Dönüş değeri: (skor, istatistikler)
    """
    stats['nodes'] += 1

    # ── Terminal durumlar ──────────────────────────────────────────────────────
    if check_winner(board, AI):
        return 100_000 + depth, stats    # AI kazandı (erken kazanç daha değerli)

    if check_winner(board, HUMAN):
        return -100_000 - depth, stats   # İnsan kazandı

    if is_full(board) or depth == 0:
        return evaluate(board), stats    # Beraberlik ya da derinlik limiti

    empty_cells = get_empty_cells(board)

    # ── Maximizer (AI turu) ────────────────────────────────────────────────────
    if is_maximizing:
        best = -math.inf
        for r, c in empty_cells:
            board[r][c] = AI
            score, stats = minimax(board, depth - 1, alpha, beta, False, stats)
            board[r][c] = None
            best = max(best, score)
            alpha = max(alpha, best)
            if beta <= alpha:
                stats['pruned'] += 1   # Beta kesimi — bu dalı atla
                break
        return best, stats

    # ── Minimizer (insan turu) ─────────────────────────────────────────────────
    else:
        best = math.inf
        for r, c in empty_cells:
            board[r][c] = HUMAN
            score, stats = minimax(board, depth - 1, alpha, beta, True, stats)
            board[r][c] = None
            best = min(best, score)
            beta = min(beta, best)
            if beta <= alpha:
                stats['pruned'] += 1   # Alpha kesimi — bu dalı atla
                break
        return best, stats


# ── AI'nın en iyi hamlesini bul ───────────────────────────────────────────────
def get_best_move(board, difficulty='Orta'):
    """
    Verilen tahta durumu ve zorluk seviyesi için AI'nın oynaması
    gereken en iyi (satır, sütun) konumunu döndürür.

    Ayrıca istatistikleri de döndürür:
        {
          'nodes'  : kaç düğüm değerlendirildi,
          'pruned' : kaç dal budandı,
          'score'  : seçilen hamlenin minimax skoru
        }
    """
    depth = DEPTH_MAP.get(difficulty, 4)
    stats = {'nodes': 0, 'pruned': 0}

    # Açılış kitabı: tahta boşsa merkeze git
    empty = get_empty_cells(board)
    center = (SIZE // 2, SIZE // 2)
    if len(empty) == SIZE * SIZE and center in empty:
        return center, {'nodes': 1, 'pruned': 0, 'score': 0}

    best_score = -math.inf
    best_move  = empty[0]

    for r, c in empty:
        board[r][c] = AI
        score, stats = minimax(board, depth - 1, -math.inf, math.inf, False, stats)
        board[r][c] = None
        stats['nodes'] += 1
        if score > best_score:
            best_score = score
            best_move  = (r, c)

    stats['score'] = best_score
    return best_move, stats
