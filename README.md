# GerberToBlender
A plugin for Blender 3D modeling software which (when completed) will import SVG exports of a Gerber file into an accurate virtual model of the PCB. 

Just in case you didn't notice while developing this project the .py files have been given names that prevent importing. A couple refactorings from now and they'll be consolidated into a single module, plus whatever other files are necessary to put it in a panel or menu or someplace on the Blender GUI (probably the file -> import -> ... menu).

I had two reasons for making this.

First off, I want to start 3d-printing out cases for some of my Arduino or Rasberry Pi hobby projects, and wanted an accurate virtual model of the boards I order for designing those casings. Virtual models of most components can be downloaded right from the manufacturers for this, but not custom PCB's or SMT's.

Secondly, sometimes I feel that the 2D layout is not suffecient for examining a PCB before placing the order -I recently got one in with a tiny mistake (I left the pads for resistors and transitors from the SMT in the PCB I planned to solder by hand for a prototype). I would have caught that easily in a 3D virtual model, and now have to wait a couple weeks for the corrected design -I'm not paying rapid shipping rates for two dollars worth of PCB's to come from China.

I figure I'm not the only one who does this stuff with Arduino or Rasberry Pi project so I'd share it on here.

Still a lot to do on this project, but so far it reads in a list of SVG files (must be set up in a folder with a text file called "names" --folder not generated yet--, and a filebrowser will select the directory) and sets up the x and y positions and sizes for each layer of the PCB. Then it applies modifiers to change the remaining 2d curves into 3d meshes and drill the holes through all the components. It finally applies the materials to all the objects once they're finished. So basically only the first and last steps are complete so far, still have to set up extrusions, and eventually it will produce two versions of a completed model, one as a single piece and one separated into components.


Current Instructions:
<blockquote>
  1.) using GerbV 2.7 export the gerer files as SVG files, each layer needs to include the board outline to import correctly for the automated parts --done manually working on automating this part
  
  
  2.) include a filenames.txt file in the folder with the svg (I always use 2-layer boards with top silk screen, the filenames.txt file is included in this repository)
  
  3.) run the import_pcb.py script
  
  4.) extrusions: --still done manually, script coming soon
  
  *board_outline: remove duplicate vertices, add in face, extrude 2.4 up z axis
  
  *bottom_solder: remove duplicate vertices, remove board outline, put faces on remaining vertices, move 0.01 down z axis
  
  *bottom_layer: remove duplicate vertices,  remove board outline, extrude 0.8 up z axis, move 0.2 up z axis, add faces
  
  *top_layer: remove duplicate verties,  remove board outline, extrude 0.8 up z axis, move 1.4 up z axis, add faces
  
  *top_solder: remove duplicates vertices,  remove board outline, add faces, move 2.41 up z axis, flip normals
  
  *silk_screen: remove duplicates vertices,  remove board outline, extrude 0.1 on x axis, extrude 0.1 on y axis move 2.41 up z axis
  
  5.) run the "apply materials.py" script
  
  6.) run the "solidify modifier.py" script
  
  7.) run the "boolean modifier.py" script
  
  8.) run the "harden board.py" script
</blockquote>


The testing so far was PCB created with EasyEDA online PCB editing software, SVG files exported from gerbv Gerber Viewer Software, and scripted with Blender 2.8.3 API.


Early drafts of the Doxygen generated documentation is available at https://francis-chris5.github.io/GerberToBlender/ 


Here's the result of running this plugin, one solid single piece model representing the board with 1 meter in Blender equal to 1 millimeter in the real world. I've been downloading models of common components for Arduino projects from GrabCAD.com, those slide right into the boards generated by this plugin, allowing a more detailed inspection of an idea before an order for the PCB's are placed.

![screenshot1](https://user-images.githubusercontent.com/50467171/86076729-97822a80-ba58-11ea-9a54-c673e119cd6b.png)
![screenshot2](https://user-images.githubusercontent.com/50467171/86076734-99e48480-ba58-11ea-942d-368719ac0989.png)

And here's a picture with components situated in a board generated by this plugin (I haven't bothered to change the leads on the transistor model I have yet, but everything else is fits nicely in the model). Note that with the viewport set to "SOLID" the traces inside the PCB are clearly visible making it easy to inspect the circuit virtually, the whole point of this project.

![screenshot3](https://user-images.githubusercontent.com/50467171/86077776-9fdb6500-ba5a-11ea-89cf-cc00480f7cfc.png)
![screenshot4](https://user-images.githubusercontent.com/50467171/86077780-a23dbf00-ba5a-11ea-9f75-23b41fc178f6.png)

