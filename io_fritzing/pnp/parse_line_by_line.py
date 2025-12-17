import bpy
from io_fritzing.pnp.import_pnp_report import importdata
from bpy.types import Operator
import re

class PnpParseLineByLine(Operator):
    bl_idname = "fritzing.pnp_parse_line_by_line"
    bl_label = "Fritzing pnp import: parse line by line"
    
    def execute(self, context):
        try:
            # 转换为绝对路径（处理Blender相对路径）
            abs_path = bpy.path.abspath(importdata.filename)
            i = 0
            with open(abs_path, 'r', encoding='utf-8') as file:
                for line in file:
                    i += 1
                    # Skip lines that start with Via or Pad or comments
                    if not line.strip().startswith('Via') and not line.strip().startswith('Pad') \
                            and not re.match(r'^P[0-9]', line.strip()) \
                            and not line.strip().startswith('#') and not line.strip().startswith('Description:') \
                            and not line.strip().startswith('RefDes,Description,Package,X,Y,Rotation,Side,Mount'):
                        clean_line = line.replace('"', '')
                        for s in ['[SMD, multilayer]', '[SMD]', 'SandFlower', 'sandflower', '[SMD, electrolytic]']:
                            clean_line = clean_line.replace(s, '')
                        parts = clean_line.strip().split(',')
                        if len(parts) >= 6:
                            designator = parts[0]
                            description = parts[1]
                            package = parts[2]
                            center_x = parts[3]
                            center_y = parts[4]
                            center_x = str(round(float(center_x) * 25.4 / 1000, 4))
                            center_y = str(round(float(center_y) * 25.4 / 1000, 4))
                            rotation = parts[5]
                            layer = parts[6]
                            mount = parts[7]
                            print(f"++ Success line {i}: {designator},{description},{package},{center_x},{center_y},{rotation},{layer},{mount}")
                            result = process_line(designator, description, package, center_x, center_y, rotation, layer, mount)
                            if result:
                                importdata.successed += 1
                            else:
                                importdata.failed += 1
                                importdata.failed_lines.append(i)
                        else:
                            print(f"-- Invalid line {i}: {line.strip()}")
                            importdata.invalid += 1
                            importdata.invalid_lines.append(i)
                    else:
                        print(f"== Skipped line {i}: {line.strip()}")
                        importdata.skipped += 1
        except Exception as e:
            print(f"读取文件失败: {e}")
            importdata.error_msg = str(e)
            getattr(getattr(bpy.ops, 'fritzing'), 'pnp_import_error')("INVOKE_DEFAULT")

        importdata.step_name = 'FINISHED'
        return {"FINISHED"}


def process_line(designator, description, package, center_x, center_y, rotation, layer, mount):
    # 处理每一行数据的逻辑
    # 这里可以添加将数据添加到Blender场景中的代码
    print(f" ** Processing line: {designator},{description},{package},{center_x},{center_y},{rotation},{layer},{mount}")
    # 分号分割description
    description_parts = description.split(';')
    if description_parts[0].strip() != '':
        # 如果description第一个分号前有内容，作为电阻导入
        print(f" ** Resistor: {description_parts[0].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
    elif description_parts[1].strip() != '':
        # 如果description第二个分号前有内容，作为电容导入
        print(f" ** Capacitor: {description_parts[1].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
    elif description_parts[2].strip() != '':
        # 如果description第三个分号前有内容，作为电感导入
        print(f" ** Inductor: {description_parts[2].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
    else:
        # 依据package类型进行导入
        if package.capitalize().startswith('Pb86-a0'):
            print(f" **** PB86-A0 ****")
        elif package.capitalize().startswith('Usb-typec'):
            print(f" **** USB-TYPE-C ****")
        elif package.capitalize().startswith('Yc164'):
            print(f" **** YC-164 ****")
        elif package.capitalize().startswith('Sot23-3'):
            print(f" **** SOT23-3 ****")
        elif package.capitalize().startswith('Sot23-6'):
            print(f" **** SOT23-6 ****")
        elif package.capitalize().startswith('Sop20'):
            print(f" **** SOP20 ****")
        elif package.capitalize().startswith('Sod323'):
            print(f" **** SOD323 ****")
        elif package.capitalize().startswith('Sod123fl'):
            print(f" **** SOD123FL ****")
        elif package.capitalize().startswith('Esop8'):
            print(f" **** ESOP8 ****")
        elif package.capitalize().startswith('Msop-10'):
            print(f" **** msop-10 ****")
        elif package.capitalize().startswith('Wdfn3x3-10'):
            print(f" **** WDFN3X3-10 ****")
        elif package.capitalize().startswith('Ts-d014'):
            print(f" **** TS-D014 ****")
        elif package.capitalize().startswith('Pb86-a0'):
            print(f" **** PB86-A0 ****")
        elif package.capitalize().startswith('Vqfn-hr-12'):
            print(f" **** VQFN-HR-12 ****")
        elif package.lower().find('mx1.25') > 0:
            print(f" **** MX1.25 ****")
        else:
            print(f" !!!! Unknown !!!!")
            return False
        
    return True
