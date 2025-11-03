import cv2
import numpy as np
import time
from decimal import Decimal, getcontext


class LineMethod:
    @classmethod
    async def line_deep_measure(cls, param):


        start_time = time.time()
        # 读取图像

        image = cv2.imread('F:/project/weldline/filletWeld23_12_15/23.jpg')
        image_mask = cv2.imread('F:/project/weldline/filletWeld23_12_15/23.png')

        # 将图像转换为灰度图像（如果原始图像是彩色的）
        gray_image = cv2.cvtColor(image_mask, cv2.COLOR_BGR2GRAY)

        # 创建一个二值图像，黑色像素值为0，非黑色像素为1
        # 阈值可以根据需要调整，0代表完全黑色，255代表完全白色
        _, binary_image = cv2.threshold(gray_image, 1, 255, cv2.THRESH_BINARY)

        # 计算非黑色像素的面积
        non_black_area = np.sum(binary_image == 255)
        print(f"非黑色像素的面积是：{non_black_area} 像素")

        # cv2.imshow('blur', binary_image)
        # cv2.waitKey(0)
        # cv2.imshow('image', image)
        # 设置缩小比例（例如0.5表示缩小到原来的一半）
        scale_percent = 100  # 百分比
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)

        # 缩小图像
        image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
        image_mask = cv2.resize(image_mask, dim, interpolation=cv2.INTER_AREA)

        src = image.copy()
        gamma = 2  # 设置伽马值

        # 进行伽马变换
        gamma_corrected = np.power(image / 255.0, gamma)
        gamma_corrected = np.uint8(gamma_corrected * 255)
        blur = cv2.bilateralFilter(gamma_corrected, 27, 75, 75)  # 27
        gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY)

        # 设定容差范围 (这里允许 RGB 的每个通道在 245 到 255 之间)
        lower_white = np.array([245, 245, 245])
        upper_white = np.array([255, 255, 255])

        # 创建一个白色像素的掩码，在指定的范围内找到白色像素
        white_pixels_mask = np.all((image_mask >= lower_white) & (image_mask <= upper_white), axis=-1)

        # 将目标图像中对应位置的像素填充为白色
        binary[white_pixels_mask] = [255]  # 填充为白色像素

        # 定义核的大小和形状
        kernel_size = (10, 10)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)

        # cv2.imshow('gamma_corrected', gamma_corrected)
        # cv2.imshow('blur', binary)
        # cv2.imshow('kernel', kernel)
        # cv2.imshow('binary', binary)
        # cv2.waitKey(0)
        # 进行腐蚀操作
        eroded = cv2.erode(binary, kernel, iterations=1)

        # 进行膨胀操作
        binary = cv2.dilate(eroded, kernel, iterations=1)

        # 先用膨胀操作扩大白色区域
        dilated = cv2.dilate(binary, kernel)

        # 然后用腐蚀操作缩小白色区域回到原来大小，但是孔洞已经被填充
        filled = cv2.erode(dilated, kernel)

        # 反转图像：将黑色变成白色，白色变成黑色（方便处理黑色区域）
        inverted_image = cv2.bitwise_not(filled)

        #####对于白色区域的黑色杂块处理
        # 查找所有连通区域
        num_labels, labels = cv2.connectedComponents(inverted_image)

        # 创建一个新图像，用于存储填充后的结果
        output_image = filled.copy()

        # 遍历所有连通区域，填充较大黑色区域
        max_area = 40000  # 设定一个面积阈值，填充大于此面积的区域
        for label in range(1, num_labels):
            # 计算每个区域的面积
            area = np.sum(labels == label)
            if area < max_area:
                # 找到该区域并填充为白色
                output_image[labels == label] = 255

        #####对于白色区域的黑色杂块处理
        # 查找所有连通区域
        num_labels, labels = cv2.connectedComponents(output_image)

        # 创建一个新图像，用于存储填充后的结果
        output_image1 = filled.copy()

        # 遍历所有连通区域，填充较大黑色区域
        max_area = 20000
        for label in range(1, num_labels):
            # 计算每个区域的面积
            area = np.sum(labels == label)
            if area < max_area:
                # 找到该区域并填充为白色
                output_image1[labels == label] = 0

        # 转成8位整型
        sure_fg = np.uint8(output_image1)
        # 应用高斯滤波器平滑边缘
        smoothed = cv2.GaussianBlur(output_image1, (3, 3), 0)
        edges = cv2.Canny(smoothed, 200, 255)

        # cv2.imshow('binary3', output_image1)
        cv2.imwrite('C:/Users/whale/OneDrive/output_image.png', output_image)

        # cv2.waitKey(0)
        ################################
        # #直线处理函数

        def extend_line(x1, y1, x2, y2, image_width, image_height):
            """扩展线段到图像边界，假设原点在左上角"""

            if x1 == x2:  # 处理垂直线
                # 垂直线的x坐标固定为x1，y坐标范围在[0, image_height-1]之间
                return x1, 0, x1, image_height - 1

            # 计算直线的斜率（m）和截距（b），直线方程为 y = mx + b
            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1

            # 计算与左边界（x=0）的交点
            x1_new = 0
            y1_new = slope * x1_new + intercept

            # 计算与右边界（x=image_width-1）的交点
            x2_new = image_width - 1
            y2_new = slope * x2_new + intercept

            # 检查交点是否在图像范围内，并进行适当调整
            if y1_new < 0:
                y1_new = 0
                x1_new = (0 - intercept) / slope  # 计算y=0时对应的x坐标
            # if y2_new > image_height - 1:
            #     y2_new = image_height - 1
            #     x2_new = (image_height - 1 - intercept) / slope  # 计算y=image_height-1时对应的x坐标
            if y2_new < 0:
                y2_new = 0
                x2_new = (0 - intercept) / slope  # 计算y=0时对应的x坐标

            # 确保x1_new和x2_new保持在有效的图像宽度范围内
            if x1_new < 0:
                x1_new = 0
                y1_new = intercept  # 重新计算x=0时的y1_new
            if x2_new > image_width - 1:
                x2_new = image_width - 1
                y2_new = slope * x2_new + intercept  # 重新计算x=image_width-1时的y2_new

            # 确保计算出来的交点在图像边界内
            return int(x1_new), int(y1_new), int(x2_new), int(y2_new)

        def calculate_angle(x1, y1, x2, y2):
            """Calculate the angle of the line with respect to the x-axis."""
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            return angle

        def calculate_angle_between_lines(angle1, angle2):
            """Calculate the absolute angle between two lines."""
            angle_diff = abs(angle1 - angle2)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            return angle_diff

        ###############################
        # 进行霍夫变换检测直线

        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40,
                                minLineLength=100, maxLineGap=200)

        # 将单通道的edges转换为三通道图像
        edges_color = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # cv2.imshow('binary1', edges_color)

        # 延长直线至边界
        extended_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # cv2.line(edges_color, (x1, y1), (x2, y2), (0, 0, 255), 2)  # 绿色直线，线宽为2
            x1_new, y1_new, x2_new, y2_new = extend_line(x1, y1, x2, y2, image.shape[1], image.shape[0])
            extended_lines.append((x1_new, y1_new, x2_new, y2_new))
            # print('extended_lines', extended_lines)

            cv2.line(edges_color, (x1_new, y1_new), (x2_new, y2_new), (0, 0, 255), 2)  # 绿色直线，线宽为2

        # 保存图像到文件
        # cv2.imwrite('F:/project/weldline/filletWeld23_12_15/result/show3.png', edges_color)

        # cv2.imshow('edges', edges_color)
        # cv2.waitKey(0)
        # # cv2.destroyAllWindows()

        # 存储符合条件的直线
        filtered_lines = []
        line_angles = []
        filtered_group = []

        # #计算夹角
        angles = []
        for (x1, y1, x2, y2) in extended_lines:
            angle = calculate_angle(x1, y1, x2, y2)
            angles.append(angle)
            filtered_lines.append([(x1, y1), (x2, y2)])
        # print(len(filtered_lines))

        for i in range(len(angles)):
            for j in range(i + 1, len(angles)):
                angle_between = calculate_angle_between_lines(angles[i], angles[j])
                line_group = [filtered_lines[i], filtered_lines[j]]
                filtered_group.append(line_group)
                line_angles.append(angle_between)

        # print(len(line_angles))
        # print(len(filtered_group))

        # 在该坐标上绘制一个红色的圆形（半径为5像素）
        # # BGR格式，红色在OpenCV中是 (0, 0, 255)
        # cv2.circle(image_mask, (491, 653), 5, (0, 255, 0), -1)  # -1表示填
        # cv2.line(image_mask, (0, 1060), (1367, 1101), 2)
        # cv2.line(image_mask, (0, 8435), (458, 0), (0, 0, 255), 2)

        # cv2.imshow('mask',image_mask)
        # cv2.waitKey(0)

        ######获取敏感区域坐标
        def inside(x, y):
            if image_mask is None:
                print(f"image_mask文件不存在")

            # 将图像转换为灰度图像
            gray1 = cv2.cvtColor(image_mask, cv2.COLOR_BGR2GRAY)

            # 二值化
            _, binary_image = cv2.threshold(gray1, 6, 255, cv2.THRESH_BINARY)
            # 使用Canny边缘检测
            edges = cv2.Canny(binary_image, 100, 200)

            # 查找图像中的轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 判断点是否在任何一个轮廓内
            is_inside = False
            for contour in contours:
                # 使用 cv2.pointPolygonTest() 来判断点是否在轮廓内
                distance = cv2.pointPolygonTest(contour, (x, y), False)
                # 如果返回值大于0，表示点在轮廓内
                if distance >= 0:
                    is_inside = True
            return is_inside

        def get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4):
            """计算两条直线的交点"""

            # 计算直线1的斜率和截距
            if x2 - x1 != 0:
                m1 = (y2 - y1) / (x2 - x1)
                b1 = y1 - m1 * x1
            else:
                # 处理垂直线
                m1 = None
                b1 = None

            # 计算直线2的斜率和截距
            if x4 - x3 != 0:
                m2 = (y4 - y3) / (x4 - x3)
                b2 = y3 - m2 * x3
            else:
                # 处理垂直线
                m2 = None
                b2 = None

            # 如果两条直线平行且不重合
            if m1 == m2:
                return None

            # 计算交点
            if m1 is not None and m2 is not None:
                # 如果两条线都不是垂直的，使用斜率和截距求交点
                x_inter = (b2 - b1) / (m1 - m2)
                y_inter = m1 * x_inter + b1
            elif m1 is None:
                # 处理直线1垂直的情况
                x_inter = x1
                y_inter = m2 * x_inter + b2
            elif m2 is None:
                # 处理直线2垂直的情况
                x_inter = x3
                y_inter = m1 * x_inter + b1

            return (int(x_inter), int(y_inter))

        outnum = 0
        key = 0
        angle = 0
        angles = 90
        while key == 0:

            angles = angles - angle
            # 选择夹角最接近90度的两根直线
            line_angles = np.abs(np.array(line_angles) - angles)
            sorted_indices = np.argsort(line_angles)
            # print('sorted_indices:', sorted_indices)

            selected_lines = [filtered_group[i] for i in sorted_indices[:40]]
            # selected_lines = selected_lines[2]
            # print('selected_lines:', selected_lines)
            # break
            for lines in selected_lines:
                lines1 = lines[0]
                lines2 = lines[1]
                # print('lines2:', lines2)
                get_point = False
                k = 0
                x0 = None
                y0 = None

                # 示例：给定两条直线的端点，计算交点
                x1, y1, x2, y2 = lines1[0][0], lines1[0][1], lines1[1][0], lines1[1][1]  # 第一条直线的端点
                x3, y3, x4, y4 = lines2[0][0], lines2[0][1], lines2[1][0], lines2[1][1]  # 第二条直线的端点

                if lines1[0][0] == 0 and lines2[0][1] == 0:
                    for pair1 in lines1:
                        if pair1[0] == 0:
                            y0 = int(pair1[1])
                    for pair2 in lines2:
                        if pair2[1] == 0:
                            x0 = int(pair2[0])
                    is_inside1 = inside(x0, y0)
                    point = get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                    # print('point', point)

                    x1 = point[0]
                    y1 = point[1]
                    is_inside2 = inside(x1, y1)
                    # print(x0,y0)
                    if is_inside1 and is_inside2:
                        key = 1
                        get_point = True
                        # print(f"点 ({x0}, {y0}) 在焊缝区域内")
                        lines_grup = lines
                        break
                    else:
                        key = 0
                        # print(f"点 ({x0}, {y0}) 不在焊缝区域内")

                if lines1[0][1] == 0 and lines2[0][0] == 0:
                    x0 = int(lines1[0][0])

                    y0 = int(lines2[0][1])

                    is_inside1 = inside(x0, y0)
                    point = get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                    # print('point', point)

                    x1 = point[0]
                    y1 = point[1]
                    is_inside2 = inside(x1, y1)
                    # print(x0,y0)
                    if is_inside1 and is_inside2:
                        key = 1
                        get_point = True
                        # print(f"点 ({x0}, {y0}) 在焊缝区域内")
                        lines_grup = lines
                        break
                    else:
                        key = 0
                        # print(f"点 ({x0}, {y0}) 不在焊缝区域内")

                if lines1[0][0] == 0 and lines2[1][1] == 0:
                    y0 = int(lines1[0][1])

                    x0 = int(lines2[1][0])

                    is_inside1 = inside(x0, y0)
                    point = get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                    # print('point', point)

                    x1 = point[0]
                    y1 = point[1]
                    is_inside2 = inside(x1, y1)
                    # print(x0,y0)
                    if is_inside1 and is_inside2:
                        key = 1
                        get_point = True
                        # print(f"点 ({x0}, {y0}) 在焊缝区域内")
                        lines_grup = lines
                        break
                    else:
                        key = 0
                        # print(f"点 ({x0}, {y0}) 不在焊缝区域内")

                if lines1[0][1] == 0 and lines2[1][0] == 0:
                    x0 = int(lines1[0][0])

                    y0 = int(lines2[1][1])

                    is_inside1 = inside(x0, y0)
                    point = get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                    # print('point', point)

                    x1 = point[0]
                    y1 = point[1]
                    is_inside2 = inside(x1, y1)
                    # print(x0,y0)
                    if is_inside1 and is_inside2:
                        key = 1
                        get_point = True
                        # print(f"点 ({x0}, {y0}) 在焊缝区域内")
                        lines_grup = lines
                        break
                    else:
                        key = 0
                        # print(f"点 ({x0}, {y0}) 不在焊缝区域内")

                if lines1[1][0] == 0 and lines2[0][1] == 0:
                    y0 = int(lines1[1][1])

                    x0 = int(lines2[0][0])

                    is_inside1 = inside(x0, y0)
                    point = get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                    # print('point', point)

                    x1 = point[0]
                    y1 = point[1]
                    is_inside2 = inside(x1, y1)
                    # print(x0,y0)
                    if is_inside1 and is_inside2:
                        key = 1
                        get_point = True
                        # print(f"点 ({x0}, {y0}) 在焊缝区域内")
                        lines_grup = lines
                        break
                    else:
                        key = 0
                        # print(f"点 ({x0}, {y0}) 不在焊缝区域内")

                if lines1[1][0] == 0 and lines2[1][1] == 0:
                    y0 = int(lines1[1][1])

                    x0 = int(lines2[1][0])

                    is_inside1 = inside(x0, y0)
                    point = get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                    # print('point', point)

                    x1 = point[0]
                    y1 = point[1]
                    is_inside2 = inside(x1, y1)
                    # print(x0,y0)
                    if is_inside1 and is_inside2:
                        key = 1
                        get_point = True
                        # print(f"点 ({x0}, {y0}) 在焊缝区域内")
                        lines_grup = lines
                        break
                    else:
                        key = 0
                        # print(f"点 ({x0}, {y0}) 不在焊缝区域内")

                if lines1[1][1] == 0 and lines2[0][0] == 0:
                    x0 = int(lines1[1][0])

                    y0 = int(lines2[0][1])

                    is_inside1 = inside(x0, y0)
                    point = get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                    # print('point', point)

                    x1 = point[0]
                    y1 = point[1]
                    is_inside2 = inside(x1, y1)
                    # print(x0,y0)
                    if is_inside1 and is_inside2:
                        key = 1
                        get_point = True
                        # print(f"点 ({x0}, {y0}) 在焊缝区域内")
                        lines_grup = lines
                        break
                    else:
                        key = 0
                        # print(f"点 ({x0}, {y0}) 不在焊缝区域内")

                if lines1[1][1] == 0 and lines2[1][0] == 0:
                    x0 = int(lines1[1][0])

                    y0 = int(lines2[1][1])

                    is_inside1 = inside(x0, y0)
                    point = get_line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
                    # print('point', point)

                    x1 = point[0]
                    y1 = point[1]
                    is_inside2 = inside(x1, y1)
                    # print(x0,y0)
                    if is_inside1 and is_inside2:
                        key = 1
                        get_point = True
                        # print(f"点 ({x0}, {y0}) 在焊缝区域内")
                        lines_grup = lines
                        break
                    else:
                        key = 0
                        # print(f"点 ({x0}, {y0}) 不在焊缝区域内")

                if get_point:
                    break

                k = k + 1
                if k == 40:
                    break
            angle = angle + 5
            outnum = outnum + 1
            if outnum == 20:
                print(f"找不到目标直线")
                break

        # # print("新的坐标点:",intersection)
        # print("新的坐标点:", x0, y0)
        # point0 = [x0, y0]
        # print("新的坐标点:", point0)

        # 设置全局的精度，确保足够高的精度来避免溢出
        getcontext().prec = 50  # 可以根据需要调整精度

        def line_intersection(p1, p2, p3, p4):
            # 使用 Decimal 来处理输入的坐标
            x1, y1 = Decimal(int(p1[0])), Decimal(int(p1[1]))
            x2, y2 = Decimal(int(p2[0])), Decimal(int(p2[1]))
            x3, y3 = Decimal(int(p3[0])), Decimal(int(p3[1]))
            x4, y4 = Decimal(int(p4[0])), Decimal(int(p4[1]))

            # 计算分母
            denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
            if denominator == 0:
                return None  # 平行或重合

            # 计算交点坐标
            x = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denominator
            y = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denominator

            # 取整
            x = int(x.to_integral_value())  # 使用高精度整数值
            y = int(y.to_integral_value())  # 使用高精度整数值

            return (x, y)

        # lines1 = np.array(lines1)
        # lines2 = np.array(lines2)

        intersection = line_intersection(np.array(lines1[0]), np.array(lines1[1]), np.array(lines2[0]),
                                         np.array(lines2[1]))
        x0 = intersection[0]
        y0 = intersection[1]
        # print("新的坐标点:", intersection)
        # print("line:", line)

        # 绘制选择的直线
        for line in lines_grup:
            cv2.line(binary, line[0], line[1], (0, 0, 0), 2)

        # 将单通道的binary转换为三通道图像
        binary_color = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

        # 绘制选择的直线
        for line in lines_grup:
            cv2.line(binary_color, line[0], line[1], (0, 0, 255), 2)

        # # 缩小图像，指定新的尺寸 (例如: 宽度 50%，高度 50%)
        # new_width = int(binary_color.shape[1] * 0.2)
        # new_height = int(binary_color.shape[0] * 0.2)
        # resized_img1 = cv2.resize(binary_color, (new_width, new_height))

        # # # 保存图像到文件
        cv2.imwrite('F:/project/weldline/filletWeld23_12_15/result/line1515.png', binary_color)

        # cv2.imshow('binary', binary_color)
        # cv2.waitKey(0)

        # 转成8位整型
        sure_fg = np.uint8(binary)

        # 使用连通组件分析算法，得到初始标记图像，其中前景区域的标记值为2，背景区域的标记值为1
        ret, markers = cv2.connectedComponents(sure_fg)  # 连通区域
        markers = markers + 1  # 整个图+1，使背景不是0而是1值

        # 对二值图像进行膨胀处理，得到未知区域的标记。将未知区域的标记值设为0
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_DILATE, kernel, iterations=1)
        unknown = binary - sure_fg
        # cv2.imshow('binary', binary)
        # 未知区域标记为0
        markers[unknown == 255] = 0

        # 区域标记结果
        markers_show = np.uint8(markers)

        # 分水岭算法分割
        markers = cv2.watershed(image, markers=markers)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(markers)
        markers_8u = np.uint8(markers)

        # 定义不同区域的颜色，用于后续可视化显示
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
                  (255, 0, 255), (0, 255, 255), (255, 128, 0), (255, 0, 128),
                  (128, 255, 0), (128, 0, 255), (255, 128, 128), (128, 255, 255)]

        #############################
        # 显示分割结果
        # 使用自定义颜色来替换彩色映射
        # def custom_color_map(markers):
        #     # 定义你希望使用的颜色。确保颜色足够鲜明且有足够的差距
        #     colors = [
        #         (255, 0, 0),   # 红色
        #         (0, 255, 0),   # 绿色
        #         (0, 0, 255),   # 蓝色
        #         (255, 255, 0), # 黄色
        #         (255, 0, 255), # 紫色
        #         (0, 255, 255), # 青色
        #         (255, 128, 0), # 橙色
        #         (255, 0, 128), # 粉红色
        #         (128, 255, 0), # 浅绿色
        #         (128, 0, 255), # 浅紫色
        #         (255, 128, 128), # 淡红色
        #         (128, 255, 255)  # 淡青色
        #     ]

        #     max_label = np.max(markers)
        #     result = np.zeros((markers.shape[0], markers.shape[1], 3), dtype=np.uint8)

        #     # 为每个标记区域分配颜色
        #     for i in range(1, max_label + 1):  # 从1开始，因为0表示背景
        #         mask = markers == i
        #         result[mask] = colors[i % len(colors)]  # 循环使用颜色

        #     return result

        # # # 创建一个彩色图像用于显示
        # # colored_markers = cv2.applyColorMap(markers_8u, cv2.COLORMAP_HSV)

        # # 自定义颜色映射
        # colored_markers_custom = custom_color_map(markers_8u)

        # # 将彩色标记图像与原图像合并
        # # 如果原图像是彩色图像，可以直接使用，如果是灰度图像，需要转换为彩色图像
        # if len(image.shape) == 2:
        #     image_color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        # else:
        #     image_color = image

        # # 用绿色边框标记分水岭算法分隔出的区域
        # result = image_color.copy()
        # result[markers == -1] = [0, 0, 225]  # 将分水岭线条（标记为 -1）设置为绿色
        # 显示结果
        # cv2.imshow('Original Image', image_color)
        # cv2.imshow('Segmented Image', result)
        # cv2.imshow('Colored Markers', colored_markers_custom)

        # cv2.imwrite("F:/project/weldline/filletWeld23_12_15/result/result17.png",result)
        # cv2.imwrite("F:/project/weldline/filletWeld23_12_15/result/colored_markers2.png",colored_markers_custom)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        #############################

        # 遍历每个标记值，将每个区域的轮廓进行提取，并使用不同颜色对每个区域进行填充。
        # 同时，计算每个区域的中心，并在图像中进行标注。
        # area_threshold = 100  # 设置面积阈值，小于该值的区域将被排除
        # 方法1
        def point_in_triangle(pt, point0, point1, point2):
            A = [pt[0] - point0[0], pt[1] - point0[1]]
            B = [pt[0] - point1[0], pt[1] - point1[1]]
            C = [pt[0] - point2[0], pt[1] - point2[1]]

            a = (A[0] * B[1]) - (B[0] * A[1])
            b = (B[0] * C[1]) - (C[0] * B[1])
            c = (C[0] * A[1]) - (A[0] * C[1])
            # print('A:', A, 'B:', B, 'C:', C)
            # print('a:', a, 'b:', b, 'c:', c)

            if (a > 0 and b > 0 and c > 0) or (a < 0 and b < 0 and c < 0):
                return True
            else:
                return False

        # ###########################################
        # # 使用连接组件分析来提取每个区域的属性
        # num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(markers_8u)

        # # 设定面积范围
        # min_area = 100  # 最小面积
        # max_area = 150000  # 最大面积

        # # 创建一个空白图像用于显示提取的区域
        # filtered_image = np.zeros_like(markers_8u)

        # # 遍历每个区域，检查其面积
        # for i in range(1, num_labels):  # 从1开始，因为0是背景
        #     area = stats[i, cv2.CC_STAT_AREA]
        #     if min_area <= area <= max_area:
        #         filtered_image[labels == i] = 255

        # # 显示结果
        # cv2.imshow('Filtered Image', filtered_image)
        # cv2.imwrite("F:/project/weldline/filletWeld23_12_15/result/ filtered_image.png", filtered_image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # ###########################################

        for i in range(2, int(max_val + 1)):
            ret, thres1 = cv2.threshold(markers_8u, i - 1, 255, cv2.THRESH_BINARY)
            ret2, thres2 = cv2.threshold(markers_8u, i, 255, cv2.THRESH_BINARY)
            mask = thres1 - thres2
            # cv2.imwrite("F:/project/weldline/filletWeld23_12_15/result/mask.png", mask)
            contours, hierarchy = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            # # 计算当前轮廓的面积
            # contour_area = cv2.contourArea(contours[0])

            # 检查是否有轮廓
            if contours:
                # 如果有轮廓，计算第一个轮廓的面积
                contour_area = cv2.contourArea(contours[0])
                # print(f"轮廓 {i} 的面积: {contour_area}")
            else:
                print(f"轮廓 {i} 没有找到任何轮廓")

            # 排除面积最小的区域
            if 590000 > contour_area > 560000:
                # if non_black_area > contour_area > non_black_area*2/5:
                cv2.drawContours(image, contours, -1, colors[(i - 2) % 12], -1)
                # 创建一个与输入图片分辨率相同的纯黑背景图像
                whit_colors = (255, 255, 255)
                black_background = 0 * np.ones_like(image)
                cv2.drawContours(black_background, contours, -1, whit_colors, -1)
                # 找到所有白色部分的坐标
                white_coords = np.column_stack(np.where(image == 255))
                # print('white_coords:', white_coords)

                # 获取图像的高度和宽度
                height, width, _ = image.shape
                # 生成所有像素的坐标
                coordinates = [(x, y) for y in range(height) for x in range(width)]

                # cv2.imshow('black_background', black_background)
                # cv2.imwrite("F:/project/weldline/filletWeld23_12_15/result/black_background41.png", black_background)
                # cv2.waitKey(0)

                # 计算三角形内黑色像素的数量

                def bresenham_line(x0, y0, x1, y1):
                    """
                    Bresenham算法生成两点之间的所有像素点

                    参数：
                    x0, y0 -- 起点坐标
                    x1, y1 -- 终点坐标

                    返回：
                    生成的像素点列表 [(x, y), ...]
                    """
                    points = []
                    dx = abs(x1 - x0)
                    dy = abs(y1 - y0)
                    sx = 1 if x0 < x1 else -1
                    sy = 1 if y0 < y1 else -1
                    err = dx - dy

                    while True:
                        points.append((x0, y0))

                        if x0 == x1 and y0 == y1:
                            break

                        e2 = 2 * err
                        if e2 > -dy:
                            err -= dy
                            x0 += sx
                        if e2 < dx:
                            err += dx
                            y0 += sy

                    return points

                # 获取黑色像素个数
                def num_black_point(i, list_x, list_y, black_pixel_count, count_greater, Len):
                    # while black_pixel_count < 1:
                    j = i
                    k = 0
                    l = 1
                    list_x_sorted = sorted(list_x)
                    # list_y_sorted = sorted(list_y)
                    while black_pixel_count < 1:
                        # if i == len_x//2:
                        #     border_list = list_x[::i]
                        # else:
                        #     border_list = list_x[i::l]
                        for x in list_x_sorted:
                            if x in list_y:
                                if count_greater > Len * 3 / 10:
                                    x1 = x0 + 20 + x
                                    y1 = y0 - 20 - x
                                    # print('存在x==y')
                                    point1 = (x0 + 20, y1)
                                    point2 = (x1, y0 - 20)
                                else:
                                    x1 = x0 - 20 - x
                                    y1 = y0 - 20 - x
                                    # print('存在x==y')
                                    point1 = (x0 - 20, y1)
                                    point2 = (x1, y0 - 20)
                                # print('存在x==y')
                                # point1 = ((x0 + 6), y1)
                                # point2 = (x1, y0 - 4)
                                # point1 = (127, 296)
                                # point2 = (265, 430)

                                # cv2.line(black_background, tuple(point1), tuple(point2), (0, 0, 255), 2)
                                # cv2.imshow('black_background', black_background)
                                # cv2.waitKey(0)
                                # cv2.line(black_background, (127, 296), (265, 430), (0, 0, 255), 2)
                                # print('point1:', point1)
                                # print('point2:', point2)

                                point_line = bresenham_line(point1[0], point1[1], point2[0], point2[1])
                                # print('point_line:', point_line)
                                for point in point_line:
                                    # pt = np.array(point)

                                    x = point[0]
                                    y = point[1]
                                    # print(black_background[y, x])
                                    if black_background[y, x][2] == 0:
                                        # 如果是黑色像素
                                        black_pixel_count += 1
                                        # print(x, y)
                                # print(black_pixel_count)
                            k += 1
                            j = i + l * k
                            i = i + 10

                            # 如果达到条件，退出循环

                            if black_pixel_count >= 30000:
                                cv2.line(black_background, tuple(point1), tuple(point2), (0, 0, 255), 2)
                                # cv2.imshow('black_background', black_background)
                                cv2.imwrite("F:/project/weldline/filletWeld23_12_15/result/tangent21.png",
                                            black_background)
                                # cv2.waitKey(0)
                                return [black_pixel_count, point1, point2]
                    # elif black_pixel_count > 10:
                    #     black_pixel_count = 0
                    #     continue

                    # return [black_pixel_count, point1, point2]
                    # result = [black_pixel_count, point1, point2]
                    # # 输出黑色像素的个数
                    # print(f"三角形内部存在 {black_pixel_count} 个黑色像素.")
                    #
                    # return result

                # 三角形内部的黑色像素初始个数
                black_pixel_count = 0

                # 寻找切线

                list_x = []
                list_y = []

                ###########开口朝右上
                # 计算大于x0的元素数量
                count_greater = sum(1 for num in coordinates if num[1] > x0)

                # 判断是否大于列表一半的数量
                if count_greater > len(coordinates) * 3 / 10:
                    print('right')
                    for point_all in coordinates:

                        if point_all[0] == y0 - 20:
                            x = point_all[1] - x0 - 20
                            if x > 0:
                                list_x.append(x)

                    for point_all in coordinates:
                        if point_all[1] == x0 + 20:
                            y = y0 - 20 - point_all[0]
                            list_y.append(y)

                ###########开口朝左上
                else:
                    print('leght')
                    for point_all in coordinates:

                        if point_all[0] == y0 - 20:
                            x = x0 - 20 - point_all[1]
                            if x > 0:
                                list_x.append(x)

                    for point_all in coordinates:
                        if point_all[1] == x0 - 20:
                            y = y0 - 20 - point_all[0]
                            list_y.append(y)

                Len = len(coordinates)
                len_x = len(list_x)
                # print(x0,y0)
                # i = len_x//2
                # i = 1
                # cv2.circle(image, (x0,y0), 5, (0, 0, 255), -1)
                cv2.circle(image, (x0 + 20, y0 - 20), 5, (0, 0, 255), -1)  # (0, 0, 255) 是红色，-1 表示填充圆
                # cv2.imwrite("F:/project/weldline/filletWeld23_12_15/result/piont19.png", black_background)

                # # 显示图像
                # cv2.imshow('Image with Red Point', image)

                # # 等待按键并关闭窗口
                # cv2.waitKey(0)

                data = num_black_point(i, list_x, list_y, black_pixel_count, count_greater, Len)

                # print(data)

                # for x in list_x:
                #     if x in list_y:
                #         x1 = x0+20 + x
                #         y1 = y0-20 - x
                #         print('存在x==y')
                #         point1 = (x0+20, y1)
                #         point2 = (x1, y0-20)
                #         cv2.line(black_background, tuple(point1), tuple(point2), (0, 0, 255), 2)
                # # 在图像上绘制红色圆点
                # cv2.circle(black_background, (intersection[0], intersection[1]), 5, (0, 0, 255), -1)
                # cv2.imshow('black_background', black_background)
                # cv2.waitKey(0)
                # 计算a值
                def distance_point_to_line(x, y, x1, y1, x2, y2):
                    # Vector AB
                    ABx = x2 - x1
                    ABy = y2 - y1

                    # Vector AP
                    APx = x - x1
                    APy = y - y1

                    # Length of AB
                    AB_length = np.sqrt(ABx ** 2 + ABy ** 2)

                    # Projection of AP onto AB
                    proj_AP_AB = (APx * ABx + APy * ABy) / AB_length

                    # Calculate distance
                    distance = np.sqrt(APx ** 2 + APy ** 2 - proj_AP_AB ** 2)
                    print('distance:', distance)
                    return distance

                d1 = data[1]
                d2 = data[2]

                a = distance_point_to_line(intersection[0], intersection[1], d1[0], d1[1], d2[0], d2[1])
                print('a = ', a)
                # 记录结束时间
                end_time = time.time()
                print(f"代码运行时间: {end_time - start_time:.4f}秒")

                # # 计算轮廓重心
                # M = cv2.moments(contours[0])
                # cx = int(M['m10']/M['m00'])
                # cy = int(M['m01']/M['m00'])  # 轮廓重心
                # cv2.drawMarker(image, (cx, cy), (0, 0, 255), 1, 10, 2)
                # cv2.drawMarker(src, (cx, cy), (0, 0, 255), 1, 10, 2)

                # cv2.imshow('black_background', black_background)
                # cv2.imshow('Selected Line', image1)
                # cv2.imshow('mask_gray', mask_gray)
                # cv2.imshow('whit_img', image1)
                # cv2.imshow('regions', image)
                # result = cv2.addWeighted(src, 0.6, image, 0.5, 0)  # 图像权重叠加
                # cv2.imshow('result', result)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()


