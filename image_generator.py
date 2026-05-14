import random, re, os, textwrap, math
from PIL import Image, ImageDraw, ImageFont
import config

# Глобальный кэш
FONT_CACHE = {}
UI_CACHE = {
    "base_img": None,
    "last_bg_color": None
}

def get_font(text, weight, size):
    # Проверяем наличие корейских символов или стрелки
    has_kr = bool(re.search(r'[\uac00-\ud7af\u3130-\u318f]', str(text)))
    is_arrow = "↓" in str(text)
    
    # Стрелка и корейский текст в MaruBuri, остальное в Roboto
    if has_kr or is_arrow:
        path = config.FONT_KR
    else:
        path = config.FONT_RU_BOLD if weight == "bold" else config.FONT_RU_REGULAR
    
    key = (path, size)
    if key not in FONT_CACHE:
        if os.path.exists(path):
            FONT_CACHE[key] = ImageFont.truetype(path, size)
        else:
            FONT_CACHE[key] = ImageFont.load_default()
    return FONT_CACHE[key]

def create_quiz_image(data):
    W, H = config.IMG_SIZE
    UI = config.UI_SETTINGS
    SC = config.UI_SCALES
    
    lvl_col = config.LEVEL_COLORS.get(str(data.get('level')), (46, 204, 113))
    img = Image.new('RGB', (W, H), lvl_col)
    d = ImageDraw.Draw(img)
    
    pad = int(min(W, H) * 0.055)
    card_radius = int(min(W, H) * 0.06)
    d.rounded_rectangle(
        [pad, pad, W - pad, H - pad],
        radius=card_radius,
        fill=(255, 255, 255)
    )

    GROUP_MAP = {
        "category": "topic",
        "level_circle": "level", "level_num": "level", "level_label": "level",
        "main_text_kr": "content", "main_text_ru": "content", "transcription": "content",
        "footer_hint": "hint"
    }

    def draw_t(draw_obj, cfg_key, text, anchor="mm", x=None, y=None):
        if not text: return
        cfg = UI[cfg_key]
        group = GROUP_MAP.get(cfg_key)
        scale = SC.get(group, 1.0) if group else 1.0
        abs_size = int(cfg["size"] * H * scale)
        font = get_font(text, cfg.get("weight"), abs_size)
        
        pos_x = (x if x is not None else cfg["pos"][0]) * W
        pos_y = (y if y is not None else cfg["pos"][1]) * H

        max_w_px = None
        if cfg_key in ("main_text_ru", "main_text_kr"):
            left = UI["category"]["pos"][0]
            right = 1 - left
            max_w_px = (right - left) * W
        else:
            max_w_ratio = cfg.get("max_width")
            if max_w_ratio:
                max_w_px = max_w_ratio * W

        if max_w_px:
            line_spacing = cfg.get("line_spacing", 4)
            # Оптимизированный wrap
            wrapped_text = "\n".join(textwrap.wrap(str(text), width=int(max_w_px / (abs_size * 0.5))))
            # Если wrap по ширине символов неточен, используем более надежный метод
            words = str(text).split()
            lines = []
            if words:
                current = words[0]
                for w in words[1:]:
                    if font.getlength(current + " " + w) <= max_w_px:
                        current += " " + w
                    else:
                        lines.append(current)
                        current = w
                lines.append(current)
                wrapped_text = "\n".join(lines)
            
            draw_obj.multiline_text((pos_x, pos_y), wrapped_text, fill=cfg["color"], font=font, anchor=anchor, align="center", spacing=line_spacing)
        else:
            draw_obj.text((pos_x, pos_y), str(text), fill=cfg["color"], font=font, anchor=anchor)

    # Динамика
    draw_t(d, "category", f"Тема: {data['category']}", anchor="mm", x=0.5, y=UI["category"]["pos"][1] + 0.05)
    
    # Уровень
    circ = UI["level_circle"]
    lvl_dx = 0.03
    lvl_dy = 0.03
    cx, cy = (circ["pos"][0] + lvl_dx) * W, (circ["pos"][1] + lvl_dy) * H
    cr = circ["radius"] * H * SC["level"]
    d.ellipse((cx-cr, cy-cr, cx+cr, cy+cr), fill=lvl_col)
    draw_t(d, "level_num", data['level'], x=(circ["pos"][0] + lvl_dx), y=(circ["pos"][1] + lvl_dy))
    draw_t(d, "level_label", "УРОВЕНЬ", x=(UI["level_label"]["pos"][0] + lvl_dx), y=(UI["level_label"]["pos"][1] + lvl_dy))

    # Текст
    has_kr = bool(re.search(r'[\uac00-\ud7af\u3130-\u318f]', str(data['main_text'])))
    main_cfg_key = "main_text_kr" if has_kr else "main_text_ru"
    draw_t(d, main_cfg_key, data['main_text'], anchor="ms", x=0.5, y=0.62)
    if data.get("transcription"): 
        draw_t(d, "transcription", data['transcription'], anchor="ms", x=0.5, y=0.80)

    # Сохранение в JPG с оптимизацией
    path = "quiz_out.jpg"
    # quality=85 - баланс между весом и качеством, optimize=True - сжатие без потерь в заголовках
    img.save(path, "JPEG", quality=85, optimize=True)
    return path

def create_true_false_image(data): 
    # Берем настройки из конфига 
    QD = config.QUIZ_DESIGN 
    W, H = config.IMG_SIZE # (800, 450) 
     
    bg_color = random.choice(QD["bg_colors"]) 
    # Создаем основной фон в режиме RGBA для корректной работы прозрачности
    img = Image.new('RGBA', (W, H), bg_color) 
 
    # 1. Фоновый знак вопроса (хаотичный паттерн)
    if QD.get("show_bg_question", True):
        try:
            BQC = QD.get("bg_question_config", {
                "count": (20, 35), "size": (50, 200), "angle": (-45, 45), "opacity": (40, 90)
            })
            
            # Слой для всех знаков вопроса
            q_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            
            placed_objects = [] # Список (x, y, radius) для контроля пересечений
            margin = 30 # Промежуток между знаками
            
            target_count = random.randint(BQC["count"][0], BQC["count"][1])
            attempts = 0
            placed_count = 0
            
            # Пытаемся разместить знаки, пока не достигнем нужного количества или лимита попыток
            while placed_count < target_count and attempts < 150:
                attempts += 1
                q_size = random.randint(BQC["size"][0], BQC["size"][1])
                q_radius = q_size * 0.5 # Эффективный радиус для коллизий
                
                q_x = random.randint(0, W)
                q_y = random.randint(0, H)
                
                # Проверка на пересечение с уже размещенными объектами
                overlap = False
                for (ox, oy, orad) in placed_objects:
                    # Расстояние между центрами
                    dist = math.sqrt((q_x - ox)**2 + (q_y - oy)**2)
                    if dist < (q_radius + orad + margin):
                        overlap = True
                        break
                
                if overlap:
                    continue # Пробуем еще раз в другом месте
                
                # Если место свободно — рисуем
                char = BQC.get("char", "!")
                q_font = get_font(char, "bold", q_size)
                q_angle = random.randint(BQC["angle"][0], BQC["angle"][1])
                q_opacity = random.randint(BQC["opacity"][0], BQC["opacity"][1])
                
                temp_size = int(q_size * 2.0)
                temp_q = Image.new('RGBA', (temp_size, temp_size), (0, 0, 0, 0))
                temp_draw = ImageDraw.Draw(temp_q)
                
                temp_draw.text((temp_size//2, temp_size//2), char, fill=(255, 255, 255, q_opacity), font=q_font, anchor="mm")
                rotated_q = temp_q.rotate(q_angle, expand=True, resample=Image.BICUBIC)
                
                rw, rh = rotated_q.size
                q_layer.paste(rotated_q, (q_x - rw//2, q_y - rh//2), rotated_q)
                
                # Сохраняем данные объекта
                placed_objects.append((q_x, q_y, q_radius))
                placed_count += 1
            
            # Используем alpha_composite для правильного наложения прозрачных слоев
            img = Image.alpha_composite(img, q_layer)
        except Exception as e:
            print(f"Ошибка отрисовки фона: {e}")
            pass
    
    # Теперь создаем Draw объект для рисования карточки и текста ПОВЕРХ фона
    draw = ImageDraw.Draw(img) 
 
    # 2. Заголовок 
    f_title = get_font(QD["title_text"], "bold", QD["title_size"]) 
    draw.text((W/2, 55), QD["title_text"], fill=QD["title_color"], font=f_title, anchor="mm") 
 
    # 3. Центральная карточка 
    c_h = QD["card_height"] 
    c_y1 = (H - c_h) / 2 + 20
    c_y2 = c_y1 + c_h + 20
    draw.rounded_rectangle([60, c_y1, 740, c_y2], 
                           radius=QD["card_radius"], fill=QD["card_bg"], 
                           outline=QD["card_outline"], width=QD["card_outline_width"]) 
 
    # 4. Текст вопроса 
    text = data['main_text'].replace('**', '') 
    f_q = get_font(text, "bold", QD["question_size"]) 
    lines = textwrap.wrap(text, width=QD["question_max_width"]) 
     
    # Центрируем текст внутри карточки по вертикали
    # y_text рассчитывается так, чтобы блок текста был ровно посередине плашки
    total_text_h = len(lines) * (QD["question_size"] + 10)
    y_text = c_y1 + (c_h / 2) - (total_text_h / 2) + (QD["question_size"] / 2)
    
    for line in lines: 
        draw.text((W/2, y_text), line, fill=QD["question_color"], font=f_q, anchor="mm") 
        y_text += QD["question_size"] + 12 
 
    # 5. Кнопки (ПРАВДА / ЛОЖЬ) - отрисовка только если включено в конфиге
    if QD.get("show_buttons", True):
        bw, bh = QD["btn_width"], QD["btn_height"] 
        by = H - bh - 40 # Отступ снизу 
         
        # Левая (ПРАВДА) 
        draw.rounded_rectangle([W/2 - bw - 15, by, W/2 - 15, by + bh], radius=QD["btn_radius"], fill=QD["btn_true_bg"]) 
        # Правая (ЛОЖЬ) 
        draw.rounded_rectangle([W/2 + 15, by, W/2 + bw + 15, by + bh], radius=QD["btn_radius"], fill=QD["btn_false_bg"]) 
         
        f_btn = get_font("ПРАВДА", "bold", QD["btn_text_size"]) 
        draw.text((W/2 - bw/2 - 15, by + bh/2), "ПРАВДА", fill="white", font=f_btn, anchor="mm") 
        draw.text((W/2 + bw/2 + 15, by + bh/2), "ЛОЖЬ", fill="white", font=f_btn, anchor="mm") 
 
    path = "quiz_final.png" 
    # Конвертируем в RGB перед сохранением
    img.convert('RGB').save(path) 
    return path
