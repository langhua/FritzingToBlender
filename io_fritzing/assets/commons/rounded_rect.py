import bpy
import bmesh
import math

def create_rounded_rectangle(pin_number, width=4.0, height=2.0, depth=0.5, radius=0.3, segments=8, rounded_corners="top"):
    pinname = f"Pin_{pin_number}"
    mesh = bpy.data.meshes.new(pinname)
    obj = bpy.data.objects.new(pinname, mesh)

    context = bpy.context
    if context is None:
        return None
    
    scene = getattr(context, 'scene', None)
    if scene is None:
        return None
    
    scene.collection.objects.link(obj)
    
    # 设置活动对象和选择状态
    view_layer = getattr(context, 'view_layer', None)
    if view_layer is not None:
        view_layer.objects.active = obj
        obj.select_set(True)

    bm = bmesh.new()
    half_w = width / 2
    half_h = height / 2

    # 角顺序: [左下, 右下, 右上, 左上]
    mask = {
        "top":    [False, False, True, True],
        "bottom": [True, True, False, False],
        "left":   [True, False, True, False],
        "right":  [False, True, False, True],
        "all":    [True, True, True, True],
    }
    corners_to_round = mask.get(rounded_corners, mask["all"])

    corners = [
        ((-half_w + radius, -half_h + radius), math.pi, 3 * math.pi / 2),  # 左下
        ((half_w - radius, -half_h + radius), -math.pi / 2, 0),           # 右下
        ((half_w - radius, half_h - radius), 0, math.pi / 2),             # 右上
        ((-half_w + radius, half_h - radius), math.pi / 2, math.pi),      # 左上
    ]

    verts_2d = []
    # 底边
    verts_2d.append((-half_w + radius, -half_h))
    verts_2d.append((half_w - radius, -half_h))
    # 右下角
    if corners_to_round[1]:
        for i in range(segments + 1):
            t = i / segments
            ang = corners[1][1] + (corners[1][2] - corners[1][1]) * t
            cx, cy = corners[1][0]
            verts_2d.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang)))
    else:
        verts_2d.append((half_w, -half_h))
    # 右边
    verts_2d.append((half_w, half_h - radius))
    # 右上角
    if corners_to_round[2]:
        for i in range(segments + 1):
            t = i / segments
            ang = corners[2][1] + (corners[2][2] - corners[2][1]) * t
            cx, cy = corners[2][0]
            verts_2d.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang)))
    else:
        verts_2d.append((half_w, half_h))
    # 顶边
    verts_2d.append((-half_w + radius, half_h))
    # 左上角
    if corners_to_round[3]:
        for i in range(segments + 1):
            t = i / segments
            ang = corners[3][1] + (corners[3][2] - corners[3][1]) * t
            cx, cy = corners[3][0]
            verts_2d.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang)))
    else:
        verts_2d.append((-half_w, half_h))
    # 左边
    verts_2d.append((-half_w, -half_h + radius))
    # 左下角
    if corners_to_round[0]:
        for i in range(segments + 1):
            t = i / segments
            ang = corners[0][1] + (corners[0][2] - corners[0][1]) * t
            cx, cy = corners[0][0]
            verts_2d.append((cx + radius * math.cos(ang), cy + radius * math.sin(ang)))
    else:
        verts_2d.append((-half_w, -half_h))

    bottom_verts = [bm.verts.new((x, y, 0)) for (x, y) in verts_2d]
    top_verts = [bm.verts.new((x, y, depth)) for (x, y) in verts_2d]

    bm.faces.new(bottom_verts)
    bm.faces.new(list(reversed(top_verts)))  # 将迭代器转换为列表
    n = len(bottom_verts)
    for i in range(n):
        bm.faces.new([bottom_verts[i], bottom_verts[(i+1)%n], top_verts[(i+1)%n], top_verts[i]])

    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    bpy.ops.object.shade_smooth()
    
    return obj

if __name__ == "__main__":
    # 示例：只让右上和左上是圆角
    create_rounded_rectangle(1, width=2, height=4, depth=1, radius=1, segments=16, rounded_corners="top")