import math
from PIL import Image
import matplotlib.pyplot as plt

# Преобразование дата картинки из типа tuple в тип list
def data_to_list(data,lenght):
    list_data = []
    for i in range(0,lenght):
        list_data += list(data[i])
    return list_data

# Учёт PSNR - Отношение сигнал-шум Пик по формуле : PSNR = 10*log(255*255/MSE)
def PSNR(image1,image2):
    new_image = Image.open(image2,'r')
    image = Image.open(image1,'r')
    width, height = new_image.size
    data_new = data_to_list(list(new_image.getdata()),width*height)
    data = data_to_list(list(image.getdata()),width*height)
    sum = 0
    for i in range(0,len(data_new)):
        sum += math.pow((data_new[i] - data[i]),2)

    MSE = sum/(width*height)
    RMSE = math.sqrt(MSE)
    PSNR = 10 * math.log((255*255/MSE),10)
    res = [RMSE,PSNR]
    return res

# Построение графики
words = [8,16,40,80,160,400,800]
PSNR_list = [79.52,71.57,67.41,60.86,59.38,56.63,54.21]
RMSE_list = [0.05,0.07,0.11,0.23,0.27,0.38,0.5]
fig, axes = plt.subplots(1,2)
axes[0].plot(words,PSNR_list)
axes[0].set_title('PSNR')
axes[0].set_xlabel('Количество битов')
axes[0].set_ylabel('PSNR')

axes[1].plot(words,RMSE_list)
axes[1].set_title('RMSE')
axes[1].set_xlabel('Количество битов')
axes[1].set_ylabel('RMSE')
fig.show()
fig.savefig('graphic.jpg')
