import os

adb_ip = '127.0.0.1:16384' # mumu 模拟器的端口

# better choose: use subprocess.run() instead of os.system()

def adb_connect():
    """
    连接 ADB 调试
    """
    connect_cmd = 'adb connect ' + adb_ip
    # subprocess.run(connect_cmd, shell=True)
    os.system(connect_cmd)

def adb_disconnect():
    """
    断开 ADB 调试
    """
    disconnect_cmd = 'adb disconnect ' + adb_ip
    os.system(disconnect_cmd)

def adb_click(x, y, device=None):
    """
    使用 ADB 命令模拟在屏幕上点击 (x, y) 位置。

    Args:
        param x: 屏幕上的 x 坐标
        param y: 屏幕上的 y 坐标
        param device: 设备名，如果连接了多个设备或模拟器，需要指定
    """
    cmd = 'adb'
    if device: 
        cmd += f' -s {device}'
    cmd += f' shell input tap {x} {y}'
    os.system(cmd)

def adb_screenshot(filename='screenshot.png'):
    """
    使用 ADB 命令在设备上截图，并将截图文件保存到本地。

    Args:
        filename: 截图文件的名称

    Returns:
        (str): 截图文件的保存路径
    """
    # 获取当前脚本所在的目录
    base_dir = os.path.dirname(os.path.realpath(__file__))
    screenshot_dir = os.path.join(base_dir, 'screenshot')

    # 确保screenshot目录存在
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)

    # 构建截图文件的完整路径
    screenshot_path = os.path.join(screenshot_dir, filename)

    # 在设备上执行截图命令
    os.system(f'adb shell screencap -p /sdcard/{filename}')

    # 将截图文件从设备拉取到指定目录
    os.system(f'adb pull /sdcard/{filename} {screenshot_path}')

    # 返回截图文件的保存路径
    return screenshot_path

# DEBUG
if __name__ == '__main__':
    adb_connect()

    adb_screenshot()

    adb_disconnect()
