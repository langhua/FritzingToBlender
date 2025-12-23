import bpy
from io_fritzing.pnp.import_pnp_report import importdata
from bpy.types import Operator, Collection
import re
import math
from io_fritzing.assets.resistors.YC164 import generate_yc164_resistor
from io_fritzing.pnp.utils.parse_resistor import parse_resistance_string
from io_fritzing.assets.switch.TS_D014 import create_ts_d014_switch
from io_fritzing.assets.switch.PB86_A0 import create_pb86_button, pb86_a0_dimensions
from io_fritzing.assets.resistors.smd_resistors import generate_smd_resistor, SMD_SIZES
from io_fritzing.assets.sod.sod323 import create_sod323_model
from io_fritzing.assets.sot.sot23_3 import create_sot23_3_model
from io_fritzing.assets.sot.sot23_6 import create_sot23_6_model
from io_fritzing.assets.mx.mx125 import create_mx125_2p
from io_fritzing.assets.vqfn_hr.vqfn_hr_12 import create_vqfn_hr_12
from io_fritzing.assets.sop.sop20 import create_sop20_model

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
                            # mil to mm
                            center_x = round(float(center_x) * 25.4 / 1000, 4)
                            center_y = round(float(center_y) * 25.4 / 1000, 4)

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
    component = None
    # 处理每一行数据的逻辑
    # 这里可以添加将数据添加到Blender场景中的代码
    print(f" ** Processing line: {designator},{description},{package},{center_x},{center_y},{rotation},{layer},{mount}")
    # 分号分割description
    description_parts = description.split(';')
    if description_parts[0].strip() != '':
        # 如果description第一个分号前有内容，作为电阻导入
        print(f" ** Resistor: {description_parts[0].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
        resistance, unit, resistance_str = parse_resistance_string(description_parts[0].strip())
        print(f"   -> 电阻阻值：{resistance}")
        if resistance is None:
            resistance = 0
        if SMD_SIZES[package.strip()] is not None:
            collection = generate_smd_resistor(resistance=resistance, tolerance=description_parts[6].strip(), package_size=package.strip())
            component = collection.objects[0]
            bpy.ops.object.select_all(action='DESELECT')
            for obj in collection.objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = component
            bpy.ops.object.join()
    elif description_parts[1].strip() != '':
        # 如果description第二个分号前有内容，作为电容导入
        print(f" ** Capacitor: {description_parts[1].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
    elif description_parts[2].strip() != '':
        # 如果description第三个分号前有内容，作为电感导入
        print(f" ** Inductor: {description_parts[2].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
    else:
        # 依据package类型进行导入
        component = None
        if package.capitalize().startswith('Pb86-a0'):
            component = create_pb86_button(dims=pb86_a0_dimensions, color=description)
        elif package.capitalize().startswith('Usb-typec'):
            print(f" **** USB-TYPE-C ****")
        elif package.capitalize().startswith('Yc164'):
            resistance, unit, resistance_str = parse_resistance_string(description)
            if resistance is None:
                resistance = 0
            component = generate_yc164_resistor(resistance)
        elif package.capitalize().startswith('Sot23-5'):
            print(f" **** SOT-23-5 ****")
        elif package.capitalize().startswith('Sot23-3'):
            print(f" **** SOT23-3 ****")
            component = create_sot23_3_model()
        elif package.capitalize().startswith('Sot23-6'):
            print(f" **** SOT23-6 ****")
            component = create_sot23_6_model()
        elif package.capitalize().startswith('Sop20'):
            print(f" **** SOP20 ****")
            component = create_sop20_model(description_parts[6])
        elif package.capitalize().startswith('Sod323'):
            print(f" **** SOD323 ****")
            component, pins, collection = create_sod323_model()
            bpy.ops.object.select_all(action='DESELECT')
            if component and bpy.context:
                for obj in collection.all_objects:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = component
                bpy.ops.object.join()
        elif package.capitalize().startswith('Sod123fl'):
            print(f" **** SOD123FL ****")
        elif package.capitalize().startswith('Esop8'):
            print(f" **** ESOP8 ****")
        elif package.capitalize().startswith('Msop-10'):
            print(f" **** msop-10 ****")
        elif package.capitalize().startswith('Wdfn3x3-10'):
            print(f" **** WDFN3X3-10 ****")
        elif package.capitalize().startswith('Ts-d014'):
            component = create_ts_d014_switch()
        elif package.capitalize().startswith('Vqfn-hr-12'):
            print(f" **** VQFN-HR-12 ****")
            component = create_vqfn_hr_12(description_parts[6])
        elif package.lower().find('mx1.25') > 0:
            print(f" **** MX1.25 ****")
            component = create_mx125_2p()
        else:
            print(f" !!!! Unknown !!!!")
            return False

    # 调整元件位置
    if component is not None:
        if isinstance(component, object):
            post_parse(component=component, center_x=center_x, center_y=center_y, rotation=rotation, layer=layer)
        elif isinstance(component, Collection):
            for obj in component.objects:
                post_parse(component=obj, center_x=center_x, center_y=center_y, rotation=rotation, layer=layer)

    return True

def post_parse(component, center_x, center_y, rotation, layer):
    # 先旋转
    if float(rotation) != 0.0:
        print(f"   -> 旋转：{rotation}")
        component.rotation_euler.z += -float(rotation) * math.pi / 180
    if layer == 'Bottom':
        component.rotation_euler.y -= math.pi
    else:
        component.location.z += importdata.pcb_thickness
    # 再移动
    if center_x != 0.0:
        component.location.x += center_x
    if center_y != 0.0:
        component.location.y += center_y
