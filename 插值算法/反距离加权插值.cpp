#include <iostream>
#include <cmath>
#include <vector>

using namespace std;

const int R = 2;    // 反距离的幂值

class Point
{
public:
    double x;       // 横坐标
    double y;       // 纵坐标
    double z;       // 高程值
    double d;       // 到插值点的距离
    double w;       // 权重

    Point(double x, double y, double z, double d, double w)
    {
        this->x = x;
        this->y = y;
        this->z = z;
        this->d = d;
        this->w = w;
    }
};


int n;                  // 采样点个数
vector<Point> arr;      // 采样点数组
double x, y, z;         // 插值点

void distance()         
{
    for(int i = 0; i < arr.size(); i++)
        arr[i].d = sqrt(pow(arr[i].x - x, 2) + pow(arr[i].y - y, 2)); 
}

void weight()   
{
    double sum = 0;                            // 权之和
    for(int i = 0; i < arr.size(); i++)     
        sum += pow(arr[i].d, -R);
    for(int i = 0; i < arr.size(); i++)        // 权归一化后为权重
        arr[i].w = pow(arr[i].d, -R) / sum;
}

void get_z()             
{
    for(int i = 0; i < arr.size(); i++)
        z += arr[i].w * arr[i].z;
}

int main()
{

    cin >> n;
    for(int i = 0; i < n; i++)
    {
        double a, b, c;
        cin >> a >> b >> c;

        arr.push_back({a, b, c, -1, -1});
    }

	while(cin >> x >> y)
	{
		distance();

		weight();

		get_z();

	    cout << x << " " << y << " " << z << endl;
	}
	
    return 0;
}

/*
6
70 140 115.4
115 115 123.1
150 150 113.8
110 170 110.5
90 190 107.2
180 210 131.78
110 150 

res:
110 150 113.595
*/