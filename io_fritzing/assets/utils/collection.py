import bpy

def create_collection_and_organize(name="Package", objects=[]):
    """将所有对象组织到一个组合中"""
    if objects is None or objects == []:
        return
    # 创建新的组合
    collection = bpy.data.collections.new(name)
    if bpy.context:
        bpy.context.scene.collection.children.link(collection)
    
        # 将对象从主场景中移除
        for obj in objects:
            bpy.context.scene.collection.objects.unlink(obj)
        
        # 将对象添加到新组合中
        for obj in objects:
            collection.objects.link(obj)
        
        # 选择所有对象
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
    
    return collection
