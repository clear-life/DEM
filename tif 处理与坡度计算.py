from gdalconst import *
from osgeo import gdal  # Open Source Geospatial 开源地理空间
import osr      # 坐标转换库
import numpy as np
import math
from pylab import *
import matplotlib.pyplot as pyplot
import struct  # 在 C 语言中的 struct 结构体和 python 中的 string 之间转换


# 获取 tif 文件的信息
def get_tif_info(tif_path):
    if tif_path.endswith('.tif') or tif_path.endswith('.TIF'):
        dataset = gdal.Open(tif_path)

        pcs = osr.SpatialReference()                                # 该类表示 OpenGIS 空间参考系统, 用于在 opengis 和 wkt 格式间进行转换
        pcs.ImportFromWkt(dataset.GetProjection())                  # 从 wkt 文本导入空间坐标系信息
        gcs = pcs.CloneGeogCS()                                     # 复制该对象的 geogcs 地理空间坐标系

        extend = dataset.GetGeoTransform()                          # 获取仿射变换系数
        shape = (dataset.RasterYSize, dataset.RasterXSize)          # 栅格图像大小, 获取图片的宽和高
    else:
        raise "Unsupported file format"

    img = dataset.GetRasterBand(1).ReadAsArray()
    # img(ndarray), gdal数据集、地理空间坐标系、仿射变换系数、栅格 shape
    return img, dataset, gcs, pcs, extend, shape


# longlat 经纬度(地理坐标), xy 笛卡尔坐标(投影坐标), rowcol 行列下标(像素坐标)
def longlat_to_xy(gcs, pcs, lon, lat):
    ct = osr.CoordinateTransformation(gcs, pcs)                     # 创建坐标系转换对象
    coordinates = ct.TransformPoint(lon, lat)
    return coordinates[0], coordinates[1], coordinates[2]


def xy_to_lonlat(gcs, pcs, x, y):
    ct = osr.CoordinateTransformation(gcs, pcs)
    lon, lat, _ = ct.TransformPoint(x, y)
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


# 根据坐标查询值
def get_value_by_coordinates(tif_pah, coordinates, coordinate_type='rowcol'):
    img, dataset, gcs, pcs, extend, shape = get_tif_info(tif_pah)

    if coordinate_type == 'rowcol':         # 像素坐标
        value = img[coordinates[0], coordinates[1]]
    elif coordinate_type == 'lonlat':       # 地理坐标
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

    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(path, shape[1], shape[0], 1, datatype)  # 使用驱动程序创建一个数据集
    # path: 数据集名称
    # nXSize: 数据集栅格宽度
    # nYSize: 数据集栅格高度
    # nBands: 波段数, 1 说明只有一个波段
    # eType: 栅格数据类型

    if dataset is not None:
        dataset.SetGeoTransform(geo_trans)          # 仿射变换系数
        dataset.SetProjection(projection)           # 设置投影参考字符串
        dataset.GetRasterBand(1).WriteArray(array)  # 向数据集写入数组 array


tif_path = r'D:\workspace\DEM数字高程模型\DEM数据\DEM样例数据\12m.tif'

img, dataset, gcs, pcs, extend, shape = get_tif_info(tif_path)
print(img)


np_img = np.array(img)
# print(np_img)
# for i in range(1000, 2000):
#     for j in range(2000, 3000):
#         np_img[i][j] = 32766
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



# 查询 tif 文件信息

# 注册所有驱动程序
gdal.AllRegister()

# 设置文件路径
filename = r'C:\Users\clearlife\Desktop\论文代码\DEM数据\DEM样例数据\12m.tif'


def open_tif():
    dataset = gdal.Open(filename, GA_ReadOnly)  # 打开文件

    # 像素信息
    print("Size is {} x {} x {}".format(dataset.RasterXSize,    # 栅格宽度 x 和高度 y
                                        dataset.RasterYSize,
                                        dataset.RasterCount))   # 波段数, DEM 是单波段, 即 z 维大小为 1


    # 坐标系标准
    # WKT(Well-known text)是一种文本标记语言(二进制表示WKB well-known binary)，用于表示矢量几何对象、空间参照系统及空间参照系统之间的转换
    print("Projection is")
    print(dataset.GetProjection())
    # 常见都是 WGS 84 坐标系, 国际地理协会标准, 通用
    # GEOGCS["WGS 84", DATUM[
    #     "WGS_1984", SPHEROID["WGS 84", 6378137, 298.25722356049, AUTHORITY["EPSG", "7030"]], AUTHORITY["EPSG", "6326"]],
    #        PRIMEM["Greenwich", 0], UNIT["degree", 0.0174532925199433, AUTHORITY["EPSG", "9122"]], AXIS["Latitude", NORTH],
    #        AXIS["Longitude", EAST], AUTHORITY["EPSG", "4326"]]


    # 仿射变换系数
    # GeoTransform 地理空间变换
    # 地理变换是从图像坐标空间（行、列）到地理参考坐标空间（投影或地理坐标）的仿射变换
    geotransform = dataset.GetGeoTransform()

    # geotransform[0] 左上角 x 坐标
    # geotransform[1] 东西方向像素分辨率
    # geotransform[2] 如果北边朝上, 为地图的行旋转角度, 通常为零
    # geotransform[3] 左上角 y 坐标
    # geotransform[4] 如果北边朝上, 为地图的列旋转角度, 通常为零
    # geotransform[5] 南北方向像素分辨率, 北边朝上时为负值
    for i in range(6):
        print(geotransform[i])

    if geotransform:
        print("Origin = ({}, {})".format(geotransform[0], geotransform[3]))
        print("Pixel Size = ({}, {})".format(geotransform[1], geotransform[5]))




def get_data():
    dataset = gdal.Open(filename, GA_ReadOnly)

    # 获取像素信息
    band = dataset.GetRasterBand(1)
    print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))

    # 波段最小值最大值
    min = band.GetMinimum()  # 波段的最小值, 即最小的栅格值
    max = band.GetMaximum()  # 波段的最大值, 即最大的栅格值
    if not min or not max:
        (min, max) = band.ComputeRasterMinMax(True)
    print("Min={:.3f}, Max={:.3f}".format(min, max))


    # 原始二进制数据
    # xoff, yoff 表示该左上角坐标在整个图像中距离原点的偏移
    # xsize, ysize 表示读取图像的矩形大小, x 是宽度, y 是高度
    # 图像读取出来后可以缩放, buf_xsize, buf_ysize 表示缩放后图像的大小
    # buf_type 表示以指定格式读取数据
    scanline = band.ReadRaster(xoff=0, yoff=0,
                               xsize=band.XSize, ysize=band.YSize,
                               buf_xsize=band.XSize, buf_ysize=band.YSize,
                               buf_type=gdal.GDT_Float32)
    # print(scanline)
    print(type(scanline))
    print(len(scanline))


    # 转换后的数据, 类型为元组
    tuple_of_floats = struct.unpack('f' * band.XSize * band.YSize, scanline)

    print(tuple_of_floats[8759000:8759100])     # 打印一小部分值
    print(len(tuple_of_floats))                 # 总长度 12958757 = 4759 * 2723
    # print(tuple_of_floats.count(-32767.0))      # 1685241, 结论: 只有部分数据是 -32767.0, -32767.0 刚好是 int16 的最小值


open_tif()

get_data()


# 高程值
# 高程值的含义, 一般都是相对高程, 绝对高程需要通过处理得到, 单位是 米
# ALOS 数据集, 发布单位:日本宇宙航空研究开发机构（Japan Aerospace Exploration Agency），简称JAXA，
# wgs84参考系，参考椭球是海福德椭球（hayford ellipsoid），所以它的高程起算点是在这个椭球面上的（从椭球面上某点做它的法线，并连接到地表某点 即为地表某点的高程值），称为大地高。
# 2015年发布, WGS84 坐标系, 椭球高, 12.5m 分辨率, DEM的分辨率是指DEM最小的单元格的长度, 用 int16 类型存储
# WGS 84基准面是以地心为中心的全球通用的椭球面, z 轴 IERS 参考子午面原点为整个地球（包括海洋和大气）的质心；，而各国则选取最符合本国实际的基准面，也就是最贴近本国地面的椭球平面
# 高程是指某一点相对于基准面的高度，目前常用的高程系统共有正高、正常高、力高和大地高程4种，而高程基准各国均有不同定义。高程系统则是定义某点沿特定的路径到一个参考面上距离的一维坐标系统。
# 是相对于给定参考基准面的地表高程的数字表示
# 绝对高程(海拔): 地面点到大地水准面的铅锤距离, 唯一
# 相对高程(假定高程): 地面点高假定水准面的铅锤距离, 不唯一
# 合成孔径雷达在获取数据的过程中,信号受到干扰,或是发生了镜面反射等情况,导致了SRTM高程数据出现了空值,尤其是在水域和高山峡谷地区,
# 因此,要增强SRTM高程数据的实用性和可靠性,就必须对其数据的空值区域进行填补。
