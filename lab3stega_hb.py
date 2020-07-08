from PIL import Image
import numpy as np
import cv2
import math
import psnr as p

# Преобразование десятичной системы в двоичную, используемую 16 битов
def decimal_to_binary(number):
    res = []
    res = "{0:016b}".format(number)
    return res
# Преобразование двоичного кода в десятичную систему
def binary_to_decimal(binary):
    num = int(binary,2)
    return num

# Преобразование строки в строку двоичного кода
def string_to_binary(text):
    res = ''.join(format(ord(i), '08b') for i in text)
    return res
# Преобразование строки двоичного кода в строку
def binary_to_string(binary):
    str = ''
    for i in range(0, len(binary), 8):
        # Преобразование каждый 8-бит число в символ
        str += ''.join(chr(int(binary[i:i+8],2)))
    return str

# Преобразование дата картинки из типа tuple в тип list
def data_to_list(data,lenght):
    list_data = []
    for i in range(0,lenght):
        list_data += list(data[i])
    return list_data

TABLE_QUANTIZATION = np.array([
[16, 12, 14, 14, 18, 24, 49, 72],
[11, 12, 13, 17, 22, 35, 64, 92],
[10, 14, 16, 22, 37, 55, 78, 95],
[16, 19, 24, 29, 56, 64, 87, 98],

[24, 26, 40, 51, 68, 81, 103, 112],
[40, 58, 57, 87, 109, 104, 121, 100],
[51, 60, 69, 80, 103, 113, 120, 103],
[61, 55, 56, 62, 77, 92, 101, 99]
])

# Разделение картинки на блоки и их квантование
def image_to_blocks(data,lenght_mes):
    blocks = []
    # Разделение информация картинки на 8х8 блоки
    blocks = np.reshape(data,(lenght_mes,8,8))
    blocks = np.float32(blocks)
    # Преобразование DCT (ДКТ)
    DCT_blocks = []
    for i in range(0, lenght_mes):
        DCT_blocks.append(cv2.dct(blocks[i]))

    # Квантование блоков
    DCT_blocks = np.asarray(DCT_blocks) # Преобразование list в array numpy
    blocks_after_quantization = []
    for i in range(0,lenght_mes):
        # делится каждое значение блоков на ответственного значения таблицы квантования
        blocks_after_quantization.append(np.divide(DCT_blocks[i],TABLE_QUANTIZATION))
    blocks_after_quantization = np.asarray(blocks_after_quantization)
    return blocks_after_quantization

# Восстановление и получение новой картинки
def reconstruct_image(blocks,lenght_mes):
    blocks_after_multiply = []
    for i in range(0,lenght_mes):
        # умножить каждое значение блоков на ответственного значения таблицы квантования
        blocks_after_multiply.append(np.multiply(blocks[i],TABLE_QUANTIZATION))

    inverse_DCT_blocks = []
    for i in range(0,lenght_mes):
        # Преобразование IDCT(обратное двумерное ДКП)
        inverse_DCT_blocks.append(np.uint8(np.round(cv2.idct(blocks_after_multiply[i]))))

    # Собрать все блоки воедино
    inverse_DCT_blocks = np.around(inverse_DCT_blocks).ravel()
    data_of_image = list(np.uint8(inverse_DCT_blocks))
    return data_of_image

# Встраивание информации в картинку и получение новой картинки
def data_after_change(data,mes,index):
    lenght_mes_bin = decimal_to_binary(len(mes))
    # Cохранение длины текста (сообщения) в НЗБ 16 первых компонетов
    for i in range(0,16):
        if lenght_mes_bin[i] == '0':
            if data[i] %2 == 1:
                data[i] = data[i] - 1
        else:
            if data[i] %2 == 0:
                data[i] = data[i] + 1
    # Редактирование дата картинки и получение новой дата после встраивания
    mes_bin = string_to_binary(mes)
    # берем n 8х8 блок, в которых мы будем встраивать информацию
    # n это количество битов сообщения (на каждом блоке встраивать 1 бит сообщения)
    # 16+64*len(mes_bin) 
    data_of_blocks = data[16:(16+64*len(mes_bin))] 

    # разделить информацию на блоки, 
    # К каждому блоку применить двумерное дискретное косинусное преобразование
    # потом применить квантизацию
    blocks_after_quantization = image_to_blocks(data_of_blocks,len(mes_bin))
    # Встраивать биты сообщения в коэфф блоки, который находится на позиции x,y
    # x = index[0] , y = index[1]
    for i in range(0,len(mes_bin)):
        if(mes_bin[i] == '0'):
            if(np.round(blocks_after_quantization[i][index[0]][index[1]]) %2 == 1):
                blocks_after_quantization[i][index[0]][index[1]] = np.round(blocks_after_quantization[i][index[0]][index[1]])
                blocks_after_quantization[i][index[0]][index[1]] -= 1
        else:
            if(np.round(blocks_after_quantization[i][index[0]][index[1]]) %2 == 0):
                blocks_after_quantization[i][index[0]][index[1]] = np.round(blocks_after_quantization[i][index[0]][index[1]])
                blocks_after_quantization[i][index[0]][index[1]] += 1

    # умножить каждое значение блоков на ответственного значения таблицы квантования
    # К каждому блоку применить обратное двумерное дискретное косинусное преобразование
    # Собрать все блоки воедино
    data_inverse_DCT_blocks = reconstruct_image(blocks_after_quantization,len(mes_bin))
    # сохранение новых значений яркости в изображении
    j = 0
    # 16 - начальная позиция встраивать информации
    # 64 - количество коэффтов 1ого блока
    for i in range(16,16+64*len(mes_bin)):
        data[i] = data_inverse_DCT_blocks[j]
        j += 1
    return data

# Чтение дата из новой картинки после встраивания информации в исходнную картинку
# Используется при извлечении секретного сообщения
def read_data(data,index):
    lenght_mes_bin = ''
    # Чтение LSB 16 первых RGB компанентов, чтобы узнать длину сообщения
    for i in range(0,16):
        if data[i]%2 == 0:
            lenght_mes_bin += '0'
        else:
            lenght_mes_bin += '1'

    lenght_mes = binary_to_decimal(lenght_mes_bin)
    mes = ''
    # преобразование с компонента нормер 16 до 16 + 64* количество битов сообщения
    data_of_blocks = data[16:(16+64*lenght_mes*8)] # 1 символ нужно 8 битов, знаем количество битов мы встраиваем

    blocks_after_quantization = image_to_blocks(data_of_blocks,lenght_mes*8)

    # Чтение дата сообщения и её получение
    for i in range(0, lenght_mes*8):
        if np.round(blocks_after_quantization[i][index[0]][index[1]]) %2 == 0:
            mes += '0'
        else:
            mes += '1'
    return mes

# Чтение файла скрытого сообщения
def secret_mes(file):
    mess = open('message.txt','r').read()
    return mess

# Встраивание скрытой информации в картинки
def encrypt_file(file,mes,index):
    image = Image.open(file, 'r')
    new_image = image.copy()
    width, height = new_image.size

    data = data_to_list(list(new_image.getdata()),width*height)
    data = data_after_change(data,mes,index)
    data_of_image = []
    for i in range(0,width*height*3,3):
        data_of_image.append(tuple(data[i:i+3]))
    new_image.putdata(data_of_image)
    new_image.save('output.bmp')
    image.close()
    new_image.close()

# Извлечения и получение нужного сообщения
def find_text(file,index):
    image = Image.open(file, 'r')
    width, height = image.size
    data = data_to_list(list(image.getdata()),width*height)
    mes = binary_to_string(read_data(data,index))
    file_text = open('text.txt',mode = 'w', encoding ='UTF-8')
    file_text.write(mes)
    file_text.close()
    image.close()

# main программ, состоит из 4 выполненных шагов
print("Вводите файл картинки: ")
image = input()
print("Вводите скрытое сообщение: ")
mes = input()
# mes = secret_mes('message.txt')
# print(mes)

index = []
index.append(int(input('Вводите индекс коэффициента: \n')))
index.append(int(input()))
encrypt_file(image,mes,index)

print("Вводите файл новой картинки:")
new_image = input()
find_text(new_image,index)
print("Скрытое сообщение можно смотреть в файле 'text.txt'.")

print("Результат вычисления PSNR:")
res = p.PSNR('sample.bmp','output.bmp')
print(f"RMSE = {round(res[0],2)}")
print(f"PSNR = {round(res[1],2)}")
print("График зависимости PSNR и RMSE от количество слов можно смотреть в файле 'graphic.jpg'.")
