import bpy
from mathutils import Matrix

## Anatomical (body-segment) coordinate systems for the ISB Shoulder JCS recommendations
## Wu et al. 2002 -  https://doi.org/10.1016/j.jbiomech.2004.05.042

## This script still needs to be modified so that it:
## 1) Creates all the frames using MuSkeMo's panels
## 2) Checks whether the requisite landmarks exist for each frame

## thorax: 
IJ = bpy.data.objects['IJ'].matrix_world.translation
C7 = bpy.data.objects['C7'].matrix_world.translation

midIJC7 = bpy.data.objects['midIJC7'].matrix_world.translation
midPXT8 = bpy.data.objects['midPXT8'].matrix_world.translation

or_thor = IJ

ydir_thor = midIJC7-midPXT8
ydir_thor.normalize() #normalize the vector to unit length

xtemp_thor = IJ - C7

zdir_thor = xtemp_thor.cross(ydir_thor)
zdir_thor.normalize() #normalize the vector to unit length

xdir_thor = ydir_thor.cross(zdir_thor)
xdir_thor.normalize()

gRl_thor = Matrix((xdir_thor, ydir_thor, zdir_thor)).transposed()  #Rotation matrix, local to global

bpy.data.objects['thorax_frame'].matrix_world=gRl_thor.to_4x4() #assuming the frame already exists
bpy.data.objects['thorax_frame'].matrix_world.translation = or_thor

bpy.data.objects['thorax_viz'].matrix_world = bpy.data.objects['thorax_frame'].matrix_world

## clavicle
SC = bpy.data.objects['SC'].matrix_world.translation
AC = bpy.data.objects['AC'].matrix_world.translation

or_clav = SC

zdir_clav = AC-SC
zdir_clav.normalize()

xdir_clav = ydir_thor.cross(zdir_clav)  #clavicle uses thorax y direction as y_temp 
xdir_clav.normalize()

ydir_clav = zdir_clav.cross(xdir_clav) 
ydir_clav.normalize()


gRl_clav = Matrix((xdir_clav, ydir_clav, zdir_clav)).transposed()
bpy.data.objects['clavicle_frame'].matrix_world=gRl_clav.to_4x4() #assuming the frame already exists
bpy.data.objects['clavicle_frame'].matrix_world.translation = or_clav

bpy.data.objects['clav_viz'].matrix_world = bpy.data.objects['clavicle_frame'].matrix_world

## scapula

AA = bpy.data.objects['AA'].matrix_world.translation
TS = bpy.data.objects['TS'].matrix_world.translation
AI = bpy.data.objects['AI'].matrix_world.translation
PC = bpy.data.objects['PC'].matrix_world.translation

or_scap = AA

zdir_scap = AA-TS
zdir_scap.normalize()

ytemp_scap =  TS-AI

xdir_scap = ytemp_scap.cross(zdir_scap) 
xdir_scap.normalize()

ydir_scap = zdir_scap.cross(xdir_scap) 
ydir_scap.normalize()


gRl_scap = Matrix((xdir_scap, ydir_scap, zdir_scap)).transposed()
bpy.data.objects['scapula_frame'].matrix_world=gRl_scap.to_4x4() #assuming the frame already exists
bpy.data.objects['scapula_frame'].matrix_world.translation = or_scap

bpy.data.objects['scap_viz'].matrix_world = bpy.data.objects['scapula_frame'].matrix_world

## humerus


GH = bpy.data.objects['GH'].matrix_world.translation
EL = bpy.data.objects['EL'].matrix_world.translation
EM = bpy.data.objects['EM'].matrix_world.translation

or_hum = GH

ydir_hum = GH - (EL+EM)/2
ydir_hum.normalize()

ztemp_hum = EL-EM

xdir_hum = ydir_hum.cross(ztemp_hum)
xdir_hum.normalize()

zdir_hum = xdir_hum.cross(ydir_hum)
zdir_hum.normalize()

gRl_hum = Matrix((xdir_hum, ydir_hum, zdir_hum)).transposed()

bpy.data.objects['humerus_frame'].matrix_world=gRl_hum.to_4x4() #assuming the frame already exists
bpy.data.objects['humerus_frame'].matrix_world.translation = or_hum


bpy.data.objects['hum_viz'].matrix_world = bpy.data.objects['humerus_frame'].matrix_world

## humerus alt - this should be constructed with the elbow in 90 degrees flexion

US = bpy.data.objects['US'].matrix_world.translation


xtemp_humalt = (EL+EM)/2 - US
zdir_humalt = xtemp_humalt.cross(ydir_hum)
zdir_humalt.normalize()

xdir_humalt = ydir_hum.cross(zdir_humalt)
xdir_humalt.normalize()

gRl_humalt = Matrix((xdir_humalt, ydir_hum, zdir_humalt)).transposed()
bpy.data.objects['humerus_frame_alt'].matrix_world=gRl_humalt.to_4x4() #assuming the frame already exists
bpy.data.objects['humerus_frame_alt'].matrix_world.translation = or_hum


## forearm frame
US = bpy.data.objects['US'].matrix_world.translation
RS = bpy.data.objects['RS'].matrix_world.translation


or_fore = US
ydir_fore = (EL+EM)/2 - US
ydir_fore.normalize()

ztemp_fore = RS-US

xdir_fore = ydir_fore.cross(ztemp_fore)
xdir_fore.normalize()

zdir_fore = xdir_fore.cross(ydir_fore)
zdir_fore.normalize()

gRl_fore = Matrix((xdir_fore, ydir_fore, zdir_fore)).transposed()
bpy.data.objects['forearm_frame'].matrix_world=gRl_fore.to_4x4() #assuming the frame already exists
bpy.data.objects['forearm_frame'].matrix_world.translation = or_fore
