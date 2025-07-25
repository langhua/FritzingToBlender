# FritzingToBlender
这是一个Blender插件，修改自[GerberToBlender](https://github.com/francis-chris5/GerberToBlender)。本项目目的是把Fritzing导出的Gerber目录，转成3D PCB板模型，以便精确设计安装螺孔位置和外壳等。

限于零件3D模型的欠缺，目前没能进一步生成完整的安装好零件的PCB 3D模型，以后条件成熟了再逐步扩展这一功能。

## 适用
Blender 4.2.1及以上版本

## 为Blender安装python模块

1. 在Windows中，以系统管理员身份打开终端，进入Blender自己的python目录，比如：cd '..\..\Program Files\Blender Foundation\Blender 4.2\4.2\python\bin\'

2. 安装所需python包：
```
.\python.exe -m pip install -r requirements.txt
```

## 使用

1. 在Fritzing中，选择【PCB】界面，选择【导出为PCB】->【Extended Gerber(RS-274X)...】，导出
2. 在Gerbv中，打开部分导出文件，包括.gm1(轮廓)、.gbl(底层布线层)、.gtl(顶层布线层)、_drill.txt(钻孔)、.gbo(底层丝印层)、.gto(顶层丝印层)
3. 在Gerbv中，逐个导出上述文件对应的层为svg：选轮廓层以及一个其它层->点击【File】菜单->【Export】->【SVG...】->选择一个文件夹保存
4. 把本项目下载为一个zip文件，在Blender中，选择菜单【编辑】->【偏好设置】->【获取扩展】->从右上角的下拉菜单栏选择【从磁盘安装】->选择之前下载的zip文件进行安装
5. 安装本模块后，在Blender中，选择菜单【文件】->【导入】->【导入SVG文件夹】，即可导入在第三步生成的那些SVG文件

【技巧】
1. 为了Blender中，各层能对齐，可以把.gm1层和其它层两层一起导出。
2. 如果不满意导入结果，可以尝试使用Inkscape先把导出的svg进行调整和保存，然后再在Blender中导入调整后的svg。


## 开发调试

1. 下载和安装VS Code
2. 在VS Code中，搜索并安装Blender Development插件
3. 在VS Code中，下载本项目源码
4. 在VS Code中，在"Command Pallete"中，运行"Blender: Build and Start"，下一步选择安装好的blender.exe，会启动这个Blender
5. 在VS Code中修改本项目源码，在Blender中查看修改后的执行结果

## 后续开发计划

1. 完美的方式，当然是直接导入Gerber文件。目前已经尝试了pcb_tools等几个项目，都不可用，但pygerber状态喜人，颇为期待，欠缺对drill的解析是pygerber的最大问题。


## 参考资料
1. [How to add a progress indicator to the Info header in Blender](https://blog.michelanders.nl/2017/04/how-to-add-progress-indicator-to-the-info-header-in-blender.html)

