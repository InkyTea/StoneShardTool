import ctypes
import win32process
import win32con
import win32gui
import win32api
import psutil
import time
import struct
from typing import Optional

class GameSpeedHack:
    def __init__(self):
        self.process_handle = None
        self.process_id = None
        self.original_speed = None
        
    def get_process_by_name(self, process_name: str) -> Optional[int]:
        """
        通过进程名获取进程ID
        """
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process_name.lower():
                return proc.info['pid']
        return None

    def get_process_by_window(self, window_title: str) -> Optional[int]:
        """
        通过窗口标题获取进程ID
        """
        window_handle = win32gui.FindWindow(None, window_title)
        if window_handle == 0:
            return None
        _, process_id = win32process.GetWindowThreadProcessId(window_handle)
        return process_id

    def attach_process(self, identifier: str, by_window: bool = False) -> bool:
        """
        附加到目标进程
        """
        try:
            if by_window:
                self.process_id = self.get_process_by_window(identifier)
            else:
                self.process_id = self.get_process_by_name(identifier)

            if not self.process_id:
                print(f"未找到目标进程: {identifier}")
                return False

            self.process_handle = win32api.OpenProcess(
                win32con.PROCESS_ALL_ACCESS,
                False,
                self.process_id
            )
            return True
        except Exception as e:
            print(f"附加进程失败: {e}")
            return False

    def read_memory(self, address: int, size: int) -> bytes:
        """
        读取内存数据
        """
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        ctypes.windll.kernel32.ReadProcessMemory(
            self.process_handle.handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )
        return buffer.raw

    def write_memory(self, address: int, data: bytes) -> bool:
        """
        写入内存数据
        """
        bytes_written = ctypes.c_size_t()
        result = ctypes.windll.kernel32.WriteProcessMemory(
            self.process_handle.handle,
            ctypes.c_void_p(address),
            data,
            len(data),
            ctypes.byref(bytes_written)
        )
        return result != 0

    def find_speed_address(self, start_address: int, size: int) -> Optional[int]:
        """
        查找可能的速度相关内存地址
        这里使用一个简单的示例方法，实际应用中需要根据具体游戏分析
        """
        try:
            memory = self.read_memory(start_address, size)
            # 这里需要根据具体游戏分析内存特征
            # 这只是一个示例模式
            pattern = b'\x00\x00\x80\x3F'  # 1.0的浮点数模式
            pos = memory.find(pattern)
            if pos != -1:
                return start_address + pos
            return None
        except:
            return None

    def set_game_speed(self, speed_multiplier: float) -> bool:
        """
        设置游戏速度
        """
        if not self.process_handle:
            print("未附加到进程")
            return False

        try:
            # 将速度乘数转换为字节
            speed_bytes = struct.pack('f', speed_multiplier)
            
            # 如果还没有找到速度地址
            if self.original_speed is None:
                # 示例：搜索主模块的内存范围
                module = psutil.Process(self.process_id).memory_maps()[0]
                start_addr = module.rss #int(module.addr.split('-')[0], 16)
                size = 1024 * 1024  # 搜索前1MB内存
                
                speed_address = self.find_speed_address(start_addr, size)
                if not speed_address:
                    print("未找到速度相关内存地址")
                    return False
                    
                # 保存原始速度值
                self.original_speed = {
                    'address': speed_address,
                    'value': self.read_memory(speed_address, 4)
                }
            
            # 写入新的速度值
            return self.write_memory(
                self.original_speed['address'],
                speed_bytes
            )
            
        except Exception as e:
            print(f"设置游戏速度失败: {e}")
            return False

    def restore_speed(self) -> bool:
        """
        恢复原始游戏速度
        """
        if not self.original_speed:
            print("没有保存的原始速度值")
            return False

        try:
            return self.write_memory(
                self.original_speed['address'],
                self.original_speed['value']
            )
        except Exception as e:
            print(f"恢复游戏速度失败: {e}")
            return False

    def cleanup(self):
        """
        清理资源
        """
        if self.process_handle:
            self.restore_speed()
            self.process_handle.Close()
            self.process_handle = None
            self.process_id = None
            self.original_speed = None

# 使用示例
def main():
    speed_hack = GameSpeedHack()
    
    try:
        # 附加到游戏进程（这里需要替换为实际的游戏进程名）
        if not speed_hack.attach_process("StoneShard.exe"):
            print("附加进程失败")
            return

        # 设置游戏速度为2倍
        if speed_hack.set_game_speed(2.0):
            print("游戏速度已设置为2倍")
            time.sleep(5)  # 保持5秒
            
            # 恢复原始速度
            if speed_hack.restore_speed():
                print("已恢复原始速度")
            
    except Exception as e:
        print(f"发生错误: {e}")
    
    finally:
        speed_hack.cleanup()

if __name__ == "__main__":
    main()
