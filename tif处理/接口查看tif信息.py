from gdalconst import *
from osgeo import gdal  # Open Source Geospatial 开源地理空间
import osr              # 坐标转换

import struct  # 在 C 语言中的 struct 结构体和 python 中的 string 之间转换

# 注册所有驱动程序
gdal.AllRegister()

# 设置文件路径
filename = r'C:\Users\clearlife\Desktop\论文代码\DEM数据\DEM样例数据\12m.tif'


def open_tif():
    dataset = gdal.Open(filename, GA_ReadOnly)  # 打开文件

    # 获取驱动程序名称 GTiff/GeoTIFF 对应 .tif 文件
    # print("Driver: {}/{}".format(dataset.GetDriver().ShortName,
    #                              dataset.GetDriver().LongName))

    # 获取像素信息
    # 栅格宽度 x 和高度 y, 波段数 RasterCount
    # 波段: DEM 是单波段, 即 Z 维大小为 1, 只有一层个像素
    print("Size is {} x {} x {}".format(dataset.RasterXSize,
                                        dataset.RasterYSize,
                                        dataset.RasterCount))


    # 获取坐标系标准信息, 即用的哪个标准
    # 地理信息系统 GIS
    # WKT(Well-known text)是一种文本标记语言(二进制表示WKB well-known binary)，用于表示矢量几何对象、空间参照系统及空间参照系统之间的转换
    # 该格式由开放地理空间联盟(OGC)制定, 开放地理空间信息联盟 OGC Open Geospatial Consortium-OGC

    print("Projection is")
    print(dataset.GetProjection())
    # 常见都是 WGS 84 坐标系, 国际地理协会标准, 通用
    # GEOGCS["WGS 84", DATUM[
    #     "WGS_1984", SPHEROID["WGS 84", 6378137, 298.25722356049, AUTHORITY["EPSG", "7030"]], AUTHORITY["EPSG", "6326"]],
    #        PRIMEM["Greenwich", 0], UNIT["degree", 0.0174532925199433, AUTHORITY["EPSG", "9122"]], AXIS["Latitude", NORTH],
    #        AXIS["Longitude", EAST], AUTHORITY["EPSG", "4326"]]


    # 获取仿射变换系数
    # GeoTransform 意为地理空间变换
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

    # 获取数据集第一个波段对象
    band = dataset.GetRasterBand(1)
    print("Band Type={}".format(gdal.GetDataTypeName(band.DataType)))

    # 获取波段的最小值最大值
    min = band.GetMinimum()  # 波段的最小值, 即最小的栅格值
    max = band.GetMaximum()  # 波段的最大值, 即最大的栅格值
    if not min or not max:
        (min, max) = band.ComputeRasterMinMax(True)  # 计算波段的最小值/最大值。
    print("Min={:.3f}, Max={:.3f}".format(min, max))


    # 读取原始二进制数据
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



    # 转换后的数据, 类型为元组, 长度跟宽度像素大小一样, 即一行的像素个数
    tuple_of_floats = struct.unpack('f' * band.XSize * band.YSize, scanline)

    print(tuple_of_floats[8759000:8759100])     # 打印一小部分值
    print(len(tuple_of_floats))                 # 12958757 = 4759 * 2723
    #
    # print(tuple_of_floats.count(-32767.0))      # 1685241, 结论: 只有部分数据是 -32767.0, -32767.0 刚好是 int16 的最小值
    # (742, 3719)

    # s=set(tuple_of_floats)    # 查看 typle_of_floats 中有几个不同的值
    # print(s)
    # print(len(s))


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
