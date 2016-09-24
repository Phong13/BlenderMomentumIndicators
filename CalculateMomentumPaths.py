import bgl
import blf
import bpy
import math
import mathutils
import copy

#TODO
# make robust
# do 

def dehomonogize(vector):
    return(mathutils.Vector([vector[0] / vector[3], vector[1] / vector[3], vector[2] / vector[3]]))
    
def world_to_screen(context, vector):
    prj = context.region_data.perspective_matrix * \
        mathutils.Vector((vector[0], vector[1], vector[2], 1.0))
    width_half = context.region.width / 2.0
    height_half = context.region.height / 2.0

    x = int(width_half + width_half * (prj.x / prj.w))
    y = int(height_half + height_half * (prj.y / prj.w))

    # correction for corner cases in perspective mode
    if prj.w < 0:
        if x < 0:
            x = context.region.width * 2
        else:
            x = context.region.width * -2
        if y < 0:
            y = context.region.height * 2
        else:
            y = context.region.height * -2
    return(x, y)


def draw_callback_px(self, context):
    font_id = 0  # XXX, need to find out how best to get this.
    screenPointsMomentum = []
    screenPointsImpulses = []
    screenPointsCOM = []
    screenPointsAngularMomentum = []
    screenPointsFreefallPath = []
    for i in range(0,len(context.scene.momentum_trail.centerOfMasses)):
        centerOfMassPath = context.scene.momentum_trail.centerOfMasses[i]
        momentumVectorsForObj = context.scene.momentum_trail.momentumVectors[i]
        momentumImpulsesForObj = context.scene.momentum_trail.momentumImpulses[i]
        angularMomentumsForObj = context.scene.momentum_trail.angularMomentum[i]
        
        #create set of lines for momentum vectors
        for j in range(0,len(centerOfMassPath)):
            com = centerOfMassPath[j]
            moVecEnd = com + (momentumVectorsForObj[j] * context.scene.momentum_trail.momentum_vector_scale)
            comPoint = world_to_screen(context, com)
            screenPointsCOM.append(comPoint)
            screenPointsMomentum.append(comPoint)
            screenPointsMomentum.append(world_to_screen(context, moVecEnd))
        
        #create set of lines for impulses
        for j in range (0,len(momentumImpulsesForObj)):
          com = centerOfMassPath[j]
          impulseVecEnd = com + (momentumImpulsesForObj[j] * context.scene.momentum_trail.momentum_vector_scale)
          screenPointsImpulses.append(world_to_screen(context, com))
          screenPointsImpulses.append(world_to_screen(context, impulseVecEnd))

        #create set of lines for angular momentum
        for j in range(0,len(centerOfMassPath)):
            com = centerOfMassPath[j]
            moVecEnd = com + (angularMomentumsForObj[j] * context.scene.momentum_trail.momentum_vector_scale)
            screenPointsAngularMomentum.append(world_to_screen(context, com))
            screenPointsAngularMomentum.append(world_to_screen(context, moVecEnd))
            
    bgl.glEnable(bgl.GL_BLEND)
    
    #draw center of masses
    if context.scene.momentum_trail.showCOM:
      bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
      bgl.glPointSize(4)
      bgl.glBegin(bgl.GL_POINTS)
      for x, y in screenPointsCOM:
          bgl.glVertex2i(int(x), int(y))
      bgl.glEnd()
    
    #draw momentum vectors
    if context.scene.momentum_trail.showMomentum:
      bgl.glColor4f(1.0, 0.0, 0.0, 0.5)
      bgl.glLineWidth(2)
      bgl.glBegin(bgl.GL_LINES)
      for x, y in screenPointsMomentum:
          bgl.glVertex2i(int(x), int(y))
      bgl.glEnd()
    
    #draw impulse vectors
    if context.scene.momentum_trail.showImpulse:
      bgl.glColor4f(1.0, 1.0, 0.0, 0.5)
      bgl.glBegin(bgl.GL_LINES)
      for x, y in screenPointsImpulses:
          bgl.glVertex2i(int(x), int(y))
      bgl.glEnd()
    
    #mark current frame with a brighter dot
    if hasattr(context.scene.momentum_trail,"frameNums"):
        if len(context.scene.momentum_trail.frameNums) > 0:
            if context.scene.frame_current >= context.scene.momentum_trail.frameNums[0][0] and context.scene.frame_current <= context.scene.momentum_trail.frameNums[0][-1]:
                idx = context.scene.frame_current - context.scene.momentum_trail.frameNums[0][0]
                bgl.glPointSize(6)
                bgl.glColor4f(1.0, .8, .8, 0.8)
                bgl.glBegin(bgl.GL_POINTS)
                bgl.glVertex2i(int(screenPointsCOM[idx][0]), int(screenPointsCOM[idx][1]))
                bgl.glEnd()
                
    if context.scene.momentum_trail.showAngularMomentum:
      bgl.glColor4f(0.0, 1.0, 0.0, 0.5)
      bgl.glBegin(bgl.GL_LINES)
      for x, y in screenPointsAngularMomentum:
          bgl.glVertex2i(int(x), int(y))
      bgl.glEnd()    
    
    if context.scene.momentum_trail.showFreefallPath:
        print("doing freefall path")
        
    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

class MomentumTrailGroupItem(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Name", description="A group name", default="Untitled")
    isSystem = bpy.props.BoolProperty(name="isSystem", description="Is this group a momentum system", default = False)
    isValid = bpy.props.StringProperty(name="isValid", description="The group is configured correctly", default="-")
    blenderGroup = bpy.props.IntProperty(name="blenderGroup", description="", default=-1);

class MomentumTrailProps(bpy.types.PropertyGroup):
    centerOfMasses = []
    mass = []
    momentumVectors = []
    momentumImpulses = []
    angularMomentum = []
    frameNums = []
    enabled = bpy.props.IntProperty(default=0)
    path_after = bpy.props.IntProperty(name="After", min=0, default=0, description="Number of frames to show after the current frame, 0 = display all")
    path_before = bpy.props.IntProperty(name="Before", min=0, default=0, description="Number of frames to show before the current frame, 0 = display all")
    path_transparency = bpy.props.IntProperty(name="Path transparency", min=0, max=100, default=0, subtype='PERCENTAGE', description="Determines visibility of path")
    path_width = bpy.props.IntProperty(name="Path width", min=1, soft_max=5, default=2, description="Width in pixels")
    showCOM = bpy.props.BoolProperty(name="Show COM", description="Show Center Of Mass", default = True)
    showMomentum = bpy.props.BoolProperty(name="Show Momentum", description="Show Momentum", default = True)
    showImpulse = bpy.props.BoolProperty(name="Show Impulse", description="Show Impulse", default = False)
    showAngularMomentum = bpy.props.BoolProperty(name="Show Angular Momentum", description="Show Angular Momentum", default = False)
    showFreefallPath = bpy.props.BoolProperty(name="Show Freefall Path", description="Show Freefall Path starting at current frame", default = False)
    momentum_vector_scale = bpy.props.FloatProperty(name="Momentum Scale", min=.000001, soft_max=100000, default=1, description="Scale factor for momentum vector display")
    momentum_groups = bpy.props.CollectionProperty(type = MomentumTrailGroupItem)
    valid_momentum_groups = bpy.props.CollectionProperty(type = MomentumTrailGroupItem)
    index = bpy.props.IntProperty()

class SCENE_OT_list_populate(bpy.types.Operator):
    bl_idname = "scene.list_populate"
    bl_label = "Refresh Group List"
    
    def execute(self, context):
        newList = []
        newGroups = []
        for grpp in bpy.data.groups:
            #check if grpp exists in list if so then don't add
            foundGrp = False
            for moGrp in context.scene.momentum_trail.momentum_groups:
              if moGrp.name == grpp.name:
                newList.append([moGrp.name,moGrp.isSystem])
                foundGrp = True
                break
            if not foundGrp:
              newGroups.append(grpp.name)
        context.scene.momentum_trail.momentum_groups.clear()
        for moGrp in newList:
            item = context.scene.momentum_trail.momentum_groups.add()
            item.name = moGrp[0]
            item.isSystem = moGrp[1]
        for nGrop in newGroups:
            item = context.scene.momentum_trail.momentum_groups.add()
            item.name = nGrop
        return {'FINISHED'}

class SCENE_UL_list(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name", text="", emboss=False)
            layout.prop(item, "isSystem")
            layout.prop(item, "isValid", text="isValid", emboss=False)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class MomentumTrailsPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_label = "Momentum Trail"

    def draw(self, context):
        col = self.layout.column()
        #not sure if this works
        if context.scene.momentum_trail.enabled != 1:
            col.operator("view3d.momentum_trail", text="Enable momentum trail")
        else:
            col.operator("view3d.momentum_trail", text="Disable momentum trail")
        self.layout.operator("scene.list_populate")
        col.label("Momentum groups")
        self.layout.template_list("SCENE_UL_list", "", context.scene.momentum_trail, "momentum_groups", context.scene.momentum_trail, "index")
        box = self.layout.box()
        col = box.column()
        col.label("Path options")
        grouped = col.column(align=True)
        grouped.prop(context.scene.momentum_trail, "path_width", text="Width")
        grouped.prop(context.scene.momentum_trail, "path_transparency", text="Transparency")
        grouped.prop(context.scene.momentum_trail, "momentum_vector_scale", text="Momentum Scale")
        row = grouped.row(align=True)
        row.prop(context.scene.momentum_trail, "path_before")
        row.prop(context.scene.momentum_trail, "path_after")
        grouped.prop(context.scene.momentum_trail, "showCOM", text="Show Center Of Mass")
        grouped.prop(context.scene.momentum_trail, "showMomentum", text="Show Momentum")
        grouped.prop(context.scene.momentum_trail, "showImpulse", text="Show Impulse")
        grouped.prop(context.scene.momentum_trail, "showAngularMomentum", text="Show Angular Momentum")
        grouped.prop(context.scene.momentum_trail, "showFreefallPath", text="Show Freefall Path")
        col.operator("view3d.momentum_trail_update", text="Update Path Step 1")
        col.operator("view3d.momentum_trail_update2", text="Update Path Step 2")


class UpdateMomentumPathData(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "view3d.momentum_trail_update"
    bl_label = "Momentum Paths Update Operator"
    
    def invoke(self, context, event):
        if context.scene.momentum_trail.enabled:
          #TODO update the path data for all objects in momentum path

          print("calcCallback1")
          
          #clear the references to the blender groups
          for grpp in context.scene.momentum_trail.momentum_groups:
            grpp.blenderGroup = -1
            grpp.isValid = "False"
          
          #validate the momentum system and build a short list of valid systems
          momentumSystems = []
          for grpp in context.scene.momentum_trail.momentum_groups:
            if grpp.isSystem:
              grpp.isValid = "False"
              foundGroup = False
              for ndx, grppp in enumerate(bpy.data.groups):
                if (grppp.name == grpp.name):
                  foundGroup = True
                  for obj in grppp.objects:
                    #check if it has a mass
                    if (obj.get('mass') is None):
                      self.report({'ERROR'}, "Object {0} in group {1} does not have a 'mass' custom attribute".format(obj.name,grpp.name))
                      grpp.isValid = "False"            
                  grpp.blenderGroup = ndx
              if not foundGroup:
                pass
              else:
                grpp.isValid = "True"
                momentumSystems.append(grpp)
                      
          # ======== CALCULATE MOTION PATHS ========
          #TODO validate that the range is valid
          fs = context.scene.frame_current
          fe = context.scene.frame_current
          if context.scene.momentum_trail.path_before != 0:
            fs = fs - context.scene.momentum_trail.path_before
            if fs <= 0:
                fs = 1
          if context.scene.momentum_trail.path_after != 0:
            fe = fe + context.scene.momentum_trail.path_after
            if fe <= 0:
                fe = 1;
          if fe < fs:
            fe = fs
            self.report({'ERROR'}, "invalid before and after values")
          print("frame start and frame end",fs,fe)
          
          for grpp in momentumSystems:
            #deselect everything in scene          
            bpy.ops.object.select_all(action='DESELECT')
            #select all objects in this group
            bpy.ops.object.select_same_group(group=grpp.name)
            
            # can't set the frame range in paths_calculate because a popup is shown in invoke
            # which is not called when executing from code
            # might be able to fix this by calling paths_calculate(INVOKE_DEFAULT)
            # after calling paths_calculate can set params and call paths_update
            for obj in bpy.data.groups[grpp.blenderGroup].objects:
              obj.animation_visualization.motion_path.type = 'RANGE'
              obj.animation_visualization.motion_path.frame_start = fs
              obj.animation_visualization.motion_path.frame_end = fe
              obj.animation_visualization.motion_path.frame_before = context.scene.momentum_trail.path_before
              obj.animation_visualization.motion_path.frame_after = context.scene.momentum_trail.path_after         
            bpy.ops.object.paths_calculate('INVOKE_DEFAULT')  
              
          # TODO Need to be able to display these mometum values as a widget in the scene
          return {'FINISHED'}
        else:
          self.report({'WARNING'}, "Momentum Trails must be enabled")
          return {'CANCELLED'}

class UpdateMomentumPathData2(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "view3d.momentum_trail_update2"
    bl_label = "Momentum Paths Update Operator Part 2"
    
    def find_fcurve(id_data, path, index=0):
        anim_data = id_data.animation_data
        for fcurve in anim_data.action.fcurves:
            if fcurve.data_path == path and fcurve.array_index == index:
                return fcurve
    
    def invoke(self, context, event):
        if context.scene.momentum_trail.enabled:
          #TODO update the path data for all objects in momentum path
          #TODO start frame can be -ive if too close to start of animation

          print("calcCallback2")
          # ======== CALCULATE MOTION PATHS ========
          #TODO validate that the range is valid
          fs = context.scene.frame_current
          fe = context.scene.frame_current
          if context.scene.momentum_trail.path_before != 0:
            fs = fs - context.scene.momentum_trail.path_before
            if fs <= 0:
                fs = 1
          if context.scene.momentum_trail.path_after != 0:
            fe = fe + context.scene.momentum_trail.path_after
            if fe <= 0:
                fe = 1;
          if fe < fs:
            fe = fs
            self.report({'ERROR'}, "invalid before and after values")
          print("frame start and frame end",fs,fe)
          grpp2objPointData = {}
          
          for grpp in context.scene.momentum_trail.momentum_groups:
            if grpp.isSystem and grpp.isValid == "True":
              bpy.ops.object.select_all(action='DESELECT')
              #select all objects in this group
              bpy.ops.object.select_same_group(group=grpp.name)              
              
              #grab points for each obj's motion_path
              obj2points = {}
              for obj in bpy.data.groups[grpp.blenderGroup].objects:
                pnts = []
                for pnt in obj.motion_path.points:
                  pnts.append( mathutils.Vector(pnt.co) )
                obj2points[obj] = pnts
              #clear objects motion paths
              bpy.ops.object.paths_clear('INVOKE_DEFAULT')
              grpp2objPointData[grpp] = obj2points
              print("adding ", grpp)
              
          #TODO fs and fe should not exceed min and max range
          del context.scene.momentum_trail.centerOfMasses[:]
          del context.scene.momentum_trail.mass[:]
          del context.scene.momentum_trail.momentumVectors[:]
          del context.scene.momentum_trail.momentumImpulses[:]
          del context.scene.momentum_trail.angularMomentum[:]
          del context.scene.momentum_trail.frameNums[:]
          
          framePeriod = 1 / context.scene.render.fps
          rng = range(fs,fe)
          for grppp in context.scene.momentum_trail.momentum_groups:
            if grppp.isSystem and grppp.isValid == "True":
              grpp = bpy.data.groups[grppp.blenderGroup]
              
              centerOfMassPath = []
              momentumVectorPath = []
              momentumImpulsePath = []
              angularMomentum = []
              frameNums = []
              masses = []
              momentumPerObj = {}
              i = 0
              for frm in rng:
                centerOfMass = mathutils.Vector()
                centerOfMass.zero()
                totalMass = 0
                totalMomentumVector = mathutils.Vector()
                
                i = frm - fs
                momentumPerObj.clear()
                for obj in grpp.objects:
                  points = grpp2objPointData[grppp][obj]
                  position = points[i]
                  anim_data = obj.animation_data
                  massWasSet = False
                  if anim_data is not None:
                    for fcurve in anim_data.action.fcurves:
                        if "mass" in fcurve.data_path:
                            massWasSet = True
                            mass = fcurve.evaluate(frm)
                  if not massWasSet:
                    mass = obj["mass"]
                  totalMass += mass
                  centerOfMass += position * mass
                  if i == 0:
                    velForward = points[i + 1] - points[i]
                    velBack = velForward
                  elif i == len(points) - 1:
                    velBack = points[i] - points[i-1]
                    velForward = velBack
                  else:
                    velForward = points[i + 1] - points[i]
                    velBack = points[i] - points[i-1]
                  velocity = (velForward + velBack) / 2.0  
                  momentum = velocity * mass
                  totalMomentumVector += momentum
                  momentumPerObj[obj] = momentum
                  
                centerOfMass = centerOfMass / totalMass
                centerOfMassPath.append(centerOfMass)
                masses.append(totalMass)
                frameNums.append(frm)
                totalAngularMomentumVector = mathutils.Vector()
                #now that we have center of mass can find angular momentum
                for obj in grpp.objects:
                  points = grpp2objPointData[grppp][obj]
                  position = points[i]
                  momentum = momentumPerObj[obj]
                  r = position - centerOfMass
                  totalAngularMomentumVector += r.cross(momentum) 
                
                angularMomentum.append(totalAngularMomentumVector)
                momentumVectorPath.append(totalMomentumVector)
                
              #now calc impulses which is the change in momentum between frames
              for i in range(1,len(momentumVectorPath)):
                impulse = momentumVectorPath[i] - momentumVectorPath[i-1]
                momentumImpulsePath.append(impulse)
              
              context.scene.momentum_trail.centerOfMasses.append(centerOfMassPath)
              context.scene.momentum_trail.mass.append(masses)
              context.scene.momentum_trail.momentumVectors.append(momentumVectorPath)
              context.scene.momentum_trail.momentumImpulses.append(momentumImpulsePath)
              context.scene.momentum_trail.angularMomentum.append(angularMomentum)
              context.scene.momentum_trail.frameNums.append(frameNums)
              
          print("finished ", len(context.scene.momentum_trail.centerOfMasses))
          return {'FINISHED'}
        else:
          self.report({'WARNING'}, "Momentum Trails must be enabled")
          return {'CANCELLED'}

class CalculateMomentumPaths(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "view3d.momentum_trail"
    bl_label = "Draw Momentum Paths Operator"

    #_handle_calc = None
    _handle_draw = None

    @staticmethod
    def handle_add(self, context):
        #CalculateMomentumPaths._handle_calc = bpy.types.SpaceView3D.draw_handler_add(
        #    calc_callback, (self, context), 'WINDOW', 'POST_VIEW')
        CalculateMomentumPaths._handle_draw = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')

    @staticmethod
    def handle_remove():
        #if CalculateMomentumPaths._handle_calc is not None:
        #    bpy.types.SpaceView3D.draw_handler_remove(CalculateMomentumPaths._handle_calc, 'WINDOW')
        if CalculateMomentumPaths._handle_draw is not None:
            bpy.types.SpaceView3D.draw_handler_remove(CalculateMomentumPaths._handle_draw, 'WINDOW')
        #CalculateMomentumPaths._handle_calc = None
        CalculateMomentumPaths._handle_draw = None
    
    def modal(self, context, event):
        if not context.scene.momentum_trail.enabled:
            CalculateMomentumPaths.handle_remove()
            context.area.tag_redraw()
            return {'FINISHED'}
        context.area.tag_redraw()
        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            if not context.scene.momentum_trail.enabled:
              # the arguments we pass the the callback
              args = (self, context)
              # Add the region OpenGL drawing callback
              # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
              CalculateMomentumPaths.handle_add(self,context)
              context.scene.momentum_trail.centerOfMasses = []
              self.momentumGrp = []
              self.masses = {}
              #calc_callback(self,context)
              context.scene.momentum_trail.enabled = True
              context.window_manager.modal_handler_add(self)
              return {'RUNNING_MODAL'}
            else:
              context.scene.momentum_trail.centerOfMasses = []
              context.scene.momentum_trail.momentumVectors = []
              context.scene.momentum_trail.momentumImpulses = []
              CalculateMomentumPaths.handle_remove()
              context.scene.momentum_trail.enabled = False
              if context.area:
                  context.area.tag_redraw()
              return {'FINISHED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
            

def register():
    print("register")
    bpy.utils.register_class(MomentumTrailGroupItem)
    bpy.utils.register_class(MomentumTrailProps)
    bpy.utils.register_class( SCENE_OT_list_populate)
    bpy.utils.register_class(UpdateMomentumPathData)
    bpy.utils.register_class(UpdateMomentumPathData2)
    bpy.utils.register_class(CalculateMomentumPaths)
    bpy.utils.register_class(SCENE_UL_list)
    bpy.utils.register_class(MomentumTrailsPanel)
    bpy.types.Scene.momentum_trail = bpy.props.PointerProperty(type=MomentumTrailProps)
    bpy.types.Scene.momentum_trail_groups = bpy.props.CollectionProperty(type=MomentumTrailGroupItem)


def unregister():
    print("unregister")
    del bpy.types.Scene.momentum_trail
    del bpy.types.Scene.momentum_trail_groups
    bpy.utils.unregister_class(MomentumTrailsPanel)
    bpy.utils.unregister_class(SCENE_UL_list)
    bpy.utils.unregister_class(CalculateMomentumPaths)
    bpy.utils.unregister_class(UpdateMomentumPathData2)    
    bpy.utils.unregister_class(UpdateMomentumPathData)
    bpy.utils.unregister_class(SCENE_OT_list_populate)
    bpy.utils.unregister_class(MomentumTrailProps)
    bpy.utils.unregister_class(MomentumTrailGroupItem)

if __name__ == "__main__":
    register()
