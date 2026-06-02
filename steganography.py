from PIL import Image
import random
import numpy as np
from scipy.special import gammainc
from scipy.stats import chi2

def int_to_32bit_binary(n):
    return format(n, '032b')

def binary_to_int(b):
    return int(b, 2)

def text_to_binary(text):
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_string):
    chars = []
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i+8]
        chars.append(chr(int(byte, 2)))
    return ''.join(chars)

#LSB_code
def embed_message_lsb(image_path, message, output_path):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        width, height = img.size

        binary_message = text_to_binary(message)
        message_length = len(message)  

        # 
        header = int_to_32bit_binary(message_length)
        full_message = header + binary_message

        total_bits = len(full_message)
        print(len(full_message))
        print(width * height * 3)
        if total_bits > width * height * 3:
            raise ValueError("Сообщение слишком длинное для изображения")

        pixel_index = 0
        for x in range(width):
            for y in range(height):
                if pixel_index >= total_bits:
                    break

                r, g, b = img.getpixel((x, y))

                if pixel_index < total_bits:
                    r = (r & ~1) | int(full_message[pixel_index])
                    pixel_index += 1
                if pixel_index < total_bits:
                    g = (g & ~1) | int(full_message[pixel_index])
                    pixel_index += 1
                if pixel_index < total_bits:
                    b = (b & ~1) | int(full_message[pixel_index])
                    pixel_index += 1

                img.putpixel((x, y), (r, g, b))

            if pixel_index >= total_bits:
                break

        img.save(output_path)
        print(f"Готово: {output_path}")

    except FileNotFoundError:
        print(f"Error. Файл не найден: {image_path}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

#RandomLSB_code
def embed_message_random_lsb(image_path, message, output_path, seed):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        width, height = img.size

        binary_message = text_to_binary(message)
        message_length = len(message)  # длина в символах

        # Добавляем 32-битный заголовок с длиной сообщения
        header = int_to_32bit_binary(message_length)
        full_message = header + binary_message

        total_bits = len(full_message)
        if total_bits > width * height * 3:
            raise ValueError("The message is too long for this image.")

        # Инициализируем генератор случайных чисел с seed
        random.seed(seed)
        
        # Создаем список всех возможных позиций пикселей и каналов
        pixel_indices = [(x, y, c) 
                        for x in range(width) 
                        for y in range(height) 
                        for c in [0, 1, 2]]  # 0-R, 1-G, 2-B
        
        # Перемешиваем позиции согласно seed
        random.shuffle(pixel_indices)

        # Встраиваем сообщение в случайные пиксели
        for i, bit in enumerate(full_message):
            if i >= len(pixel_indices):
                raise ValueError("Недостаточно позиций в пикселях для сообщения.")
            
            x, y, c = pixel_indices[i]
            r, g, b = img.getpixel((x, y))
            
            # Модифицируем соответствующий канал
            if c == 0:  # Red
                r = (r & ~1) | int(bit)
            elif c == 1:  # Green
                g = (g & ~1) | int(bit)
            else:  # Blue
                b = (b & ~1) | int(bit)
                
            img.putpixel((x, y), (r, g, b))

        img.save(output_path)
        print(f"Готово: {output_path}")

    except FileNotFoundError:
        print(f"Error. Файл не найден: {image_path}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")

#BlockLSB_code
def embed_message_block_lsb(image_path, message, output_path, seed, block_size=4):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        width, height = img.size
        pixels = img.load()

        binary_message = text_to_binary(message)
        message_length = len(message)
        header = int_to_32bit_binary(message_length)
        full_message = header + binary_message

        random.seed(seed)

        # Создаем блоки
        blocks = []
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                block = []
                for j in range(y, min(y + block_size, height)):
                    for i in range(x, min(x + block_size, width)):
                        for channel in [0, 1, 2]:  # R, G, B channels
                            block.append((i, j, channel))
                if block:  # только непустые блоки
                    blocks.append(block)

        # Перемешиваем блоки
        random.shuffle(blocks)
        # print(len(blocks))
        if len(full_message) > len(blocks):
            raise ValueError("Сообщение слишком длинное для изображения")
        # Встраиваем сообщение
        for bit_index, secret_bit in enumerate(full_message):
            if bit_index >= len(blocks):
                break

            block = blocks[bit_index]
            secret_bit_int = int(secret_bit)

            # Вычисляем текущую четность блока
            current_parity = 0
            for x, y, channel in block:
                r, g, b = pixels[x, y]
                if channel == 0:
                    current_parity ^= (r & 1)
                elif channel == 1:
                    current_parity ^= (g & 1)
                else:
                    current_parity ^= (b & 1)

            # Если четность не совпадает, инвертируем случайный LSB
            if current_parity != secret_bit_int:
                x, y, channel = random.choice(block)
                r, g, b = pixels[x, y]
                
                if channel == 0:
                    r ^= 1
                elif channel == 1:
                    g ^= 1
                else:
                    b ^= 1
                
                pixels[x, y] = (r, g, b)

        img.save(output_path)
        print(f"Simple block parity method ready: {output_path}")

    except Exception as e:
        print(f"Error: {e}")

#LSB_decode
def extract_message_lsb(image_path):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        width, height = img.size

        bits = []
        pixel_index = 0

        header_bits = []
        for x in range(width):
            for y in range(height):
                r, g, b = img.getpixel((x, y))
                for color in (r, g, b):
                    if len(header_bits) < 32:
                        header_bits.append(str(color & 1))
                    else:
                        break
                if len(header_bits) >= 32:
                    break
            if len(header_bits) >= 32:
                break

        message_length = binary_to_int(''.join(header_bits))
        print(f"Length of message (chars): {message_length}")

        total_message_bits = message_length * 8
        bits_extracted = []

        bits_read = 0
        bit_pos = 32

        for x in range(width):
            for y in range(height):
                r, g, b = img.getpixel((x, y))
                for color in (r, g, b):
                    if bit_pos < 32:
                        bit_pos += 1
                        continue
                    if bits_read < total_message_bits:
                        bits_extracted.append(str(color & 1))
                        bits_read += 1
                        bit_pos += 1
                    else:
                        break
                if bits_read >= total_message_bits:
                    break
            if bits_read >= total_message_bits:
                break

        binary_message = ''.join(bits_extracted)
        message = binary_to_text(binary_message)
        return message

    except FileNotFoundError:
        print(f"Error. File not found: {image_path}")
    except Exception as e:
        print(f"Error: {e}")

#RandomLSB_decode
def extract_message_random_lsb(image_path, seed):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        width, height = img.size

        # Инициализируем генератор случайных чисел с тем же seed
        random.seed(seed)
        
        # Создаем и перемешиваем позиции так же, как при встраивании
        pixel_indices = [(x, y, c) 
                        for x in range(width) 
                        for y in range(height) 
                        for c in [0, 1, 2]]
        random.shuffle(pixel_indices)

        # Сначала извлекаем 32 бита заголовка (длина сообщения)
        header_bits = []
        for i in range(32):
            if i >= len(pixel_indices):
                raise ValueError("Not enough pixel positions to extract header.")
            
            x, y, c = pixel_indices[i]
            r, g, b = img.getpixel((x, y))
            
            if c == 0:
                header_bits.append(str(r & 1))
            elif c == 1:
                header_bits.append(str(g & 1))
            else:
                header_bits.append(str(b & 1))

        message_length = binary_to_int(''.join(header_bits))
        total_message_bits = message_length * 8
        bits_extracted = []

        # Извлекаем оставшиеся биты сообщения
        for i in range(32, 32 + total_message_bits):
            if i >= len(pixel_indices):
                raise ValueError("Not enough pixel positions to extract message.")
            
            x, y, c = pixel_indices[i]
            r, g, b = img.getpixel((x, y))
            
            if c == 0:
                bits_extracted.append(str(r & 1))
            elif c == 1:
                bits_extracted.append(str(g & 1))
            else:
                bits_extracted.append(str(b & 1))

        binary_message = ''.join(bits_extracted)
        message = binary_to_text(binary_message)
        return message

    except FileNotFoundError:
        print(f"Error. File not found: {image_path}")
    except Exception as e:
        print(f"Error: {e}")

#BlockLSB_decode
def extract_message_block_lsb(image_path, seed, block_size=4):
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        width, height = img.size
        pixels = img.load()

        random.seed(seed)

        # Создаем блоки в том же порядке
        blocks = []
        for y in range(0, height, block_size):
            for x in range(0, width, block_size):
                block = []
                for j in range(y, min(y + block_size, height)):
                    for i in range(x, min(x + block_size, width)):
                        for channel in [0, 1, 2]:
                            block.append((i, j, channel))
                if block:
                    blocks.append(block)

        # Перемешиваем так же
        random.shuffle(blocks)

        extracted_bits = []

        # Извлекаем биты из блоков
        for block in blocks:
            parity = 0
            for x, y, channel in block:
                r, g, b = pixels[x, y]
                if channel == 0:
                    parity ^= (r & 1)
                elif channel == 1:
                    parity ^= (g & 1)
                else:
                    parity ^= (b & 1)
            extracted_bits.append(str(parity))

        # Извлекаем заголовок и сообщение
        if len(extracted_bits) >= 32:
            header_bits = ''.join(extracted_bits[:32])
            message_length = binary_to_int(header_bits)
            total_bits_needed = 32 + message_length * 8

            if len(extracted_bits) >= total_bits_needed:
                message_binary = ''.join(extracted_bits[32:total_bits_needed])
                return binary_to_text(message_binary)

        return "Message extraction failed"

    except Exception as e:
        print(f"Error: {e}")

#визуальная атака
def extract_lsb_plane(image_path, output_path):

    try:
        img = Image.open(image_path)
        img = img.convert("RGB")  

        width, height = img.size
        lsb_img = Image.new("RGB", (width, height)) 

        for x in range(width):
            for y in range(height):
                r, g, b = img.getpixel((x, y))

                r_lsb = (r & 1) * 255
                g_lsb = (g & 1) * 255
                b_lsb = (b & 1) * 255

                lsb_img.putpixel((x, y), (r_lsb, g_lsb, b_lsb))

        lsb_img.save(output_path)
        print(f"Готово: {output_path}")

    except FileNotFoundError:
        print(f"Error FileNotFound: {image_path}")
    except Exception as e:
        print(f"Error: {e}")
def chi2_attack_on_zone_full(hist_zone):
    """Хи-квадрат для одной зоны. Возвращает (chi2_stat, p_value)"""
    observed = []
    expected = []
    
    for k in range(128):
        obs = hist_zone[2 * k]
        exp = (hist_zone[2 * k] + hist_zone[2 * k + 1]) / 2.0
        observed.append(obs)
        expected.append(exp)
    
    observed = np.array(observed)
    expected = np.array(expected)
    
    mask = expected > 0
    if not np.any(mask):
        return 0.0, 1.0
    
    observed = observed[mask]
    expected = expected[mask]
    
    chi2_stat = np.sum((observed - expected) ** 2 / expected)
    df = len(observed) - 1
    
    if df <= 0:
        return chi2_stat, 1.0
    
    p_value = 1 - chi2.cdf(chi2_stat, df)
    return chi2_stat, p_value
def zonal_chi2_attack(image_path, zone_size=(32, 32), threshold=0.95):
    """Анализ по всем каналам сразу (объединённая гистограмма)"""
    img = Image.open(image_path).convert("RGB")
    pixels = np.array(img)  # (h, w, 3)
    h, w, _ = pixels.shape
    
    zh, zw = zone_size
    zones_h = h // zh
    zones_w = w // zw
    
    print(f"\n{'='*80}")
    print(f"Файл: {image_path} | Анализ по ВСЕМ КАНАЛАМ | Зона: {zh}x{zw}")
    print(f"{'='*80}")
    print(f"{'Зона':^8} {'χ² значение':^14} {'p-value':^12} {'Статус':^15} {'⚠️'}")
    print(f"{'-'*80}")
    
    suspicious_zones = []
    chi2_values = []
    p_values = []
    
    for i in range(zones_h):
        for j in range(zones_w):
            # Вырезаем зону для ВСЕХ каналов
            zone = pixels[i*zh:(i+1)*zh, j*zw:(j+1)*zw]  # (zh, zw, 3)
            
            # Объединяем гистограммы всех каналов
            hist_zone = np.zeros(256)
            for c in range(3):
                hist_zone += np.bincount(zone[:, :, c].flatten(), minlength=256)
            
            chi2_val, p_val = chi2_attack_on_zone_full(hist_zone)
            
            chi2_values.append(chi2_val)
            p_values.append(p_val)
            
            status = "ПОДОЗРИТЕЛЬНО" if p_val > threshold else "нормально"
            warning = "⚠️" if p_val > threshold else " "
            
            print(f"  ({i},{j})    {chi2_val:10.2f}    {p_val:10.6f}    {status:<15} {warning}")
            
            if p_val > threshold:
                suspicious_zones.append((i, j, chi2_val, p_val))
    
    print(f"{'-'*80}")
    
    chi2_values = np.array(chi2_values)
    p_values = np.array(p_values)
    suspicious_ratio = len(suspicious_zones) / len(p_values) if len(p_values) > 0 else 0
    
    print(f"   Среднее χ²: {np.mean(chi2_values):.2f}")
    print(f"   Средний p-value: {np.mean(p_values):.6f}")
    print(f"   Подозрительных зон: {len(suspicious_zones)} из {len(p_values)} ({suspicious_ratio*100:.1f}%)")
    
    print(f"\n{'='*80}")
    if suspicious_ratio > 0.5:
        print("СКОРЕЕ ВСЕГО ЕСТЬ СКРЫТОЕ СООБЩЕНИЕ")
    else:
        print("СКРЫТОЕ СООБЩЕНИЕ НЕ ОБНАРУЖЕНО")
    print(f"{'='*80}\n")
    
    return {
        'chi2_values': chi2_values,
        'p_values': p_values,
        'suspicious_zones': suspicious_zones,
        'avg_chi2': np.mean(chi2_values),
        'avg_p': np.mean(p_values),
        'suspicious_ratio': suspicious_ratio
    }

#RS-атака

def flip_f1(value):
    return value ^ 1

def flip_f_minus_1(value):
    if value == 255:
        return 0
    if value == 0:
        return 255
    if value % 2 == 1:
        return value + 1
    else:
        return value - 1

def apply_mask(block, mask, use_inverse=False):
    flipped = block.copy()
    for i in range(len(block)):
        if mask[i] == 1:
            if use_inverse:
                flipped[i] = flip_f_minus_1(block[i])
            else:
                flipped[i] = flip_f1(block[i])
        elif mask[i] == -1:
            if use_inverse:
                flipped[i] = flip_f1(block[i])
            else:
                flipped[i] = flip_f_minus_1(block[i])
    return flipped

def smoothness(block):
    return np.sum(np.abs(np.diff(block)))

def classify_block(block, mask, use_inverse=False):
    original_smooth = smoothness(block)
    flipped_block = apply_mask(block, mask, use_inverse)
    flipped_smooth = smoothness(flipped_block)
    
    if flipped_smooth > original_smooth:
        return 'R'
    elif flipped_smooth < original_smooth:
        return 'S'
    else:
        return 'U'

def rs_analysis_channel(channel_array, masks):
    height, width = channel_array.shape
    block_size = 4
    
    valid_rows = height
    valid_cols = (width - block_size + 1)
    total_blocks = valid_rows * valid_cols
    
    results = {}
    for M in masks:
        M_key = tuple(M)
        minus_M_key = tuple([-x for x in M])
        results[M_key] = {'R': 0, 'S': 0, 'U': 0, 'count': 0}
        results[minus_M_key] = {'R': 0, 'S': 0, 'U': 0, 'count': 0}
    
    for row in range(valid_rows):
        for col in range(valid_cols):
            block = channel_array[row, col:col+block_size]
            
            for M in masks:
                M_key = tuple(M)
                minus_M = [-x for x in M]
                minus_M_key = tuple(minus_M)
                
                cls_M = classify_block(block, M, use_inverse=False)
                results[M_key][cls_M] += 1
                results[M_key]['count'] += 1
                
                cls_minus_M = classify_block(block, minus_M, use_inverse=False)
                results[minus_M_key][cls_minus_M] += 1
                results[minus_M_key]['count'] += 1
    
    return results, total_blocks

def check_rs_hypothesis(results, masks, channel_name):
    print(f"\n{'='*70}")
    print(f"Проверка гипотезы для канала {channel_name}")
    print(f"{'='*70}")
    
    hypothesis_holds = True
    
    for M in masks:
        M_key = tuple(M)
        minus_M = [-x for x in M]
        minus_M_key = tuple(minus_M)
        
        total_M = results[M_key]['count']
        total_minus_M = results[minus_M_key]['count']
        
        if total_M == 0 or total_minus_M == 0:
            continue
        
        R_M = results[M_key]['R'] / total_M * 100
        S_M = results[M_key]['S'] / total_M * 100
        
        R_minus_M = results[minus_M_key]['R'] / total_minus_M * 100
        S_minus_M = results[minus_M_key]['S'] / total_minus_M * 100
        
        diff_R = abs(R_M - R_minus_M)
        diff_S = abs(S_M - S_minus_M)
        
        print(f"\nМаска M: {M}")
        print(f"Маска -M: {minus_M}")
        print(f"  R_M={R_M:5.2f}%, R_-M={R_minus_M:5.2f}% | ΔR={diff_R:5.2f}%")
        print(f"  S_M={S_M:5.2f}%, S_-M={S_minus_M:5.2f}% | ΔS={diff_S:5.2f}%")
        
        if diff_R > 5.0 or diff_S > 5.0:
            hypothesis_holds = False
            print(f"⚠️ ЗНАЧИТЕЛЬНОЕ ОТКЛОНЕНИЕ")
        else:
            print(f"Гипотеза выполняется")
    
    print(f"\n{'-'*70}")
    if hypothesis_holds:
        print("ВЫВОД: Изображение ЧИСТОЕ")
    else:
        print("ВЫВОД: Вероятно наличие СТЕГО")
    
    return hypothesis_holds

def get_standard_masks():
    masks = [
        [1, 1, 1, 1],
        [1, 0, 1, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 1],
        [0,0,0,1],
        [0,1,0,1],
        [0,1,1,1],
    ]
    return masks

def rs_analysis_color(image_path):
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    r, g, b = img.split()
    channels = {
        'R': np.array(r),
        'G': np.array(g),
        'B': np.array(b)
    }
    
    masks = get_standard_masks()

    all_hypotheses = {}
    
    for name, channel_array in channels.items():
        print(f"АНАЛИЗ КАНАЛА: {name}")
        
        results, total_blocks = rs_analysis_channel(channel_array, masks)
        print(f"\nПроанализировано блоков: {total_blocks}")
        
        hypothesis_holds = check_rs_hypothesis(results, masks, name)
        all_hypotheses[name] = hypothesis_holds
    
    print("\n" + "="*70)
    print("ИТОГОВЫЙ ВЕРДИКТ")
    print("="*70)
    
    if all(all_hypotheses.values()):
        print("\nИЗОБРАЖЕНИЕ ЧИСТОЕ")
    else:
        print("\nОБНАРУЖЕНО СКРЫТОЕ СООБЩЕНИЕ")
    
    return all_hypotheses


if __name__ == "__main__":
    mode = input("Выберите режим:\n1 - Закодировать сообщение в изображение\n2 - Декодировать сообщение из изображения\n3 - Выбрать стеганографическую атаку> ").strip()
    if mode == "1":
        # Кодирование
        print("\n--- Кодирование ---")
        method = input("Выберите метод (1 - LSB, 2 - RandomLSB, 3 - BlockLSB): ").strip()
        #image_path = "input.png"
        image_path = input("Введите путь к исходному изображению (например, input.png): ").strip()
        output_path = input("Введите путь для сохранения результата (например, output.png): ").strip()
        #output_path = "output_with_message.png"
        message_file = "hello.txt"  # путь к файлу с сообщением
        # Чтение сообщения из текстового файла
        with open(message_file, "r", encoding="utf-8") as f:
            message = f.read()
        if method == "1":
            embed_message_lsb(image_path, message, output_path)
        elif method == "2":
            seed = input("Введите пароль: ").strip()
            embed_message_random_lsb(image_path, message, output_path, seed)
        elif method == "3":
            seed = input("Введите пароль: ").strip()
            embed_message_block_lsb(image_path, message, output_path, seed)
        else:
            print("Неверный выбор метода.")
        
        print("Готово! Файл:", output_path)
    
    elif mode == "2":
        # Декодирование
        print("\n--- Декодирование ---")
        method = input("Выберите метод (1 - LSB, 2 - RandomLSB, 3 - BlockLSB): ").strip()
        image_path = input("Введите путь к изображению с сообщением: ").strip()
        
        # Извлечение сообщения
        if method == "1":
            extracted = extract_message_lsb(image_path)
        elif method == "2":
            seed = input("Введите пароль: ").strip()
            extracted = extract_message_random_lsb(image_path, seed)
        elif method == "3":
            seed = input("Введите пароль: ").strip()
            extracted = extract_message_block_lsb(image_path, seed)
        else:
            print("Неверный выбор метода.")
        print("\nИзвлечённое сообщение:")
        print(extracted)
        
        # Сохранение в файл
        save = input("Сохранить сообщение в файл? (y/n): ").lower().strip()
        if save == "y":
            out_file = input("Имя файла для сохранения: ").strip()
            try:
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(extracted)
                print("Сохранено.")
            except Exception as e:
                print(f"Ошибка при сохранении: {e}")
    elif mode=="3":
        # Атака
        print("\n--- Атака на стеганографическую систему ---")
        method = input("Выберите атаку (1 - Визуальная, 2 - Хи-квадрат, 3 - Regular-Singular): ").strip()
        image_path = input("Введите путь к изображению: ").strip()
        
        # Алгоритмы атак
        if method == "1":
            output_path = "lsb_extract.png"  
            extract_lsb_plane(image_path, output_path)
        elif method == "2":
            result = zonal_chi2_attack(image_path, zone_size=(1,531))

        elif method == "3":
            rs_analysis_color(image_path)
        else:
            print("Неверный выбор атаки.")
    else:
        print("Неверный режим.")

