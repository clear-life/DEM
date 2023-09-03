from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
#1.首先得到原图像的宽度、高度
def get_image_information(image_path):
    vector=plt.imread(image_path)
    # print(vector)#得到图像的三维矩阵
    # print(type(vector))
    # print(vector.shape)#得到(高，宽，通道数)
    height=vector.shape[0]
    width=vector.shape[1]
    return height,width,vector

def getdst_image_vector(srcHeight,srcWidth,srcVector,dstHeight,dstWidth):
    #定义一个三维矩阵存储目标图像，每个像素由RGB三种颜色组成，shape接受一个元组，可以创建多维矩阵
    dstVector=np.zeros(shape=(dstHeight,dstWidth,3),dtype=int)#默认是float64
    # print(dstVector)
    #遍历目标图像的每一个像素
    for dstX in range(1,dstWidth+1):#[0,dstWid-1]，#矩阵从0开始，不是从1开始
        for dstY in range(1,dstHeight+1):#[0,dstHeight-1]
            #坐标换算
            dstX_srcX=dstX*(srcWidth/dstWidth)#python中/表示除法,//表示整除
            dstY_srcY=dstY*(srcHeight/dstHeight)
            # print(dstX_srcX,dstY_srcY)
            #最近邻四舍五入，采用round函数实现
            dstX_srcX_round=int(round(dstX_srcX))
            dstY_srcY_round=int(round(dstY_srcY))
            # print(srcVector[dstX_srcX_round][dstY_srcY_round])
            # print(dstX_srcX_round,dstY_srcY_round)
            dstVector[dstY-1][dstX-1]=srcVector[dstY_srcY_round-1][dstX_srcX_round-1]#这个地方要认真琢磨,x,y也不能搞反了
            # dstVector[dstX][dstY]=srcVector[dstX_srcX_round][dstY_srcY_round]
    print(dstVector)
    # pic=Image.fromarray(dstVector, "RGB")
    # pic.show()
    plt.imshow(dstVector)  # 显示数组
    plt.show()
    plt.imsave('邻近法得到的图像.jpg',dstVector.astype(np.uint8))#matplotlib保存图像的时候，只接受浮点数或者unit8的整数类型
    # plt.imsave('邻近法得到的图像.jpg',dstVector/255)
    return dstVector

if __name__=='__main__':
    imagePath=r'songshu.jpg'
    srcHeight,srcWidth,srcVector=get_image_information(imagePath)
    dstHeight=int(2*srcHeight)
    dstWidth =int(2*srcWidth)
    print(srcHeight,srcWidth)
    print(dstHeight,dstWidth)
    dstVector=getdst_image_vector(srcHeight,srcWidth,srcVector,dstHeight,dstWidth)
    # print("srcVector",srcVector)
    # print("dstVector",dstVector)