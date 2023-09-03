from gdalconst import *
from osgeo import gdal
import osr      # 坐标转换库
import numpy as np
import math
from pylab import *

import matplotlib.pyplot as pyplot


# 获取 tif 文件的信息
def get_tif_info(tif_path):
    if tif_path.endswith('.tif') or tif_path.endswith('.TIF'):
        dataset = gdal.Open(tif_path)

        pcs = osr.SpatialReference()                                # 该类表示 OpenGIS 空间参考系统, 用于在 opengis 和 wkt 格式间进行转换
        pcs.ImportFromWkt(dataset.GetProjection())                  # 从 wkt 文本导入空间坐标系信息
        gcs = pcs.CloneGeogCS()                                     # 复制该对象的 geogcs 地理空间坐标系

        extend = dataset.GetGeoTransform()                          # 获取仿射变换系数
        # im_width = dataset.RasterXSize    #栅格矩阵的列数
        # im_height = dataset.RasterYSize   #栅格矩阵的行数
        shape = (dataset.RasterYSize, dataset.RasterXSize)          # 栅格图像大小, 获取图片的宽和高
    else:
        raise "Unsupported file format"

    img = dataset.GetRasterBand(1).ReadAsArray()
    # img(ndarray), gdal数据集、地理空间坐标系、投影坐标系、栅格影像大小
    return img, dataset, gcs, pcs, extend, shape


# longlat 表示经纬度, xy 表示投影坐标, rowcol 表示行列号
def longlat_to_xy(gcs, pcs, lon, lat):
    ct = osr.CoordinateTransformation(gcs, pcs)                     # 创建坐标系转换对象
    coordinates = ct.TransformPoint(lon, lat)                       # 经纬度转换为图像坐标
    return coordinates[0], coordinates[1], coordinates[2]


def xy_to_lonlat(gcs, pcs, x, y):
    ct = osr.CoordinateTransformation(gcs, pcs)
    lon, lat, _ = ct.TransformPoint(x, y)                           # 图像坐标转换为经纬度
    return lon, lat


def xy_to_rowcol(extend, x, y):
    a = np.array([[extend[1], extend[2]], [extend[4], extend[5]]])
    b = np.array([x - extend[0], y - extend[3]])

    row_col = np.linalg.solve(a, b)
    row = int(np.floor(row_col[1]))
    col = int(np.floor(row_col[0]))

    return row, col


def rowcol_to_xy(extend, row, col):
    x = extend[0] + col * extend[1] + row * extend[2]
    y = extend[3] + col * extend[4] + row * extend[5]
    return x, y


# 根据所给信息查询值
def get_value_by_coordinates(tif_pah, coordinates, coordinate_type='rowcol'):
    img, dataset, gcs, pcs, extend, shape = get_tif_info(tif_pah)

    if coordinate_type == 'rowcol':         # 行列号
        value = img[coordinates[0], coordinates[1]]
    elif coordinate_type == 'lonlat':       # 经纬度
        x, y, _ = longlat_to_xy(gcs, pcs, coordinates[0], coordinates[1])
        row, col = xy_to_rowcol(extend, x, y)
        value = img[row, col]
    elif coordinate_type == 'xy':           # 投影坐标
        row, col = xy_to_rowcol(extend, coordinates[0], coordinates[1])
        value = img[row, col]
    else:
        raise 'coordinated_type error'
    return value


# 保存 tif 文件
def save_tif(array, path, shape, geo_trans, projection, type_name):
    if 'int8' in type_name:
        datatype = gdal.GDT_Byte
    elif 'int16' in type_name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32

    driver = gdal.GetDriverByName('GTiff')          # 根据名称获取管理驱动程序的类
    dataset = driver.Create(path, shape[1], shape[0], 1, datatype)  # 使用驱动程序创建一个数据集
    # path: 数据集名称
    # nXSize: 数据集栅格宽度(以像素为单位, 下同)
    # nYSize: 数据集栅格高度
    # nBands: 波段数, 1 说明只有一个波段
    # eType: 栅格数据类型

    if dataset is not None:
        dataset.SetGeoTransform(geo_trans)          # 设置仿射变换系数
        dataset.SetProjection(projection)           # 设置投影参考字符串
        dataset.GetRasterBand(1).WriteArray(array)  # 向数据集写入数组 array


tif_path = r'D:\workspace\DEM数字高程模型\DEM数据\DEM样例数据\12m.tif'

img, dataset, gcs, pcs, extend, shape = get_tif_info(tif_path)
print(img)


np_img = np.array(img)
# print(img)
# print(shape)
# for i in range(1000, 2000):
#     for j in range(2000, 3000):
#         a[i][j] = 32766
# print(np_img)
#
#
# value = get_value_by_coordinates(tif_path, [1, 1])
# print(value)


# 计算平均坡度
def average_slope(img, shape):
    slope = 0
    cnt = 0
    for i in range(shape[0]):
        for j in range(shape[1] - 1):
            if(img[i][j] > -32766):
                k = j + 1
                while k < shape[1] - 1 and img[i][k] < -32766:
                    k = k + 1

                if(img[i][k] > -32766):
                    cnt = cnt + 1
                    b = abs(img[i][k] - img[i][j])
                    b = b ** 2
                    a = (12.5 * (k - j)) ** 2
                    tmp_slope = math.acos(12.5 / math.sqrt(a + b + 1))
                    slope = slope + tmp_slope
    return math.degrees(slope) / cnt, cnt


# a, b = average_slope(img, shape)
#
# print(a, b)


# 计算最小值最大值
def min_max_value(img, shape):
    mini = 32766
    maxi = -32767

    for i in range(shape[0]):
        for j in range(shape[1]):
            if(img[i][j] > -32766 and img[i][j] < mini):
                mini = img[i][j]
            if(img[i][j] > maxi):
                maxi = img[i][j]

    return mini, maxi


def min_max_value_fun(tif_path):
    dataset = gdal.Open(tif_path, GA_ReadOnly)
    band = dataset.GetRasterBand(1)
    min_value = band.GetMinimum()  # 波段的最小值, 即最小的栅格值
    max_value = band.GetMaximum()  # 波段的最大值, 即最大的栅格值
    return min_value, max_value


# mpl.rcParams['font.sans-serif'] = ['SimHei']  # 添加这条可以让图形显示中文
#
# x_axis_data = range(4759)
# y_axis_data = img[1500]
#
# # plot中参数的含义分别是横轴值，纵轴值，线的形状，颜色，透明度,线的宽度和标签
# plt.plot(x_axis_data, y_axis_data, 'ro-', color='#4169E1', alpha=0.8, linewidth=1, label='一些数字')
#
# # 显示标签，如果不加这句，即使在plot中加了label='一些数字'的参数，最终还是不会显示标签
# plt.legend(loc="upper right")
# plt.xlabel('x轴数字')
# plt.ylabel('y轴数字')
#
# plt.show()

values=img[1500]
#有12个数据，bins=3将其分为3段，即(0,2),(2,4),(4,6),从直方图中可以看出(2,4)中的数据最多
plt.hist(values,bins=1000)
plt.show()
