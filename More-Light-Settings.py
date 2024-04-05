# More-Light-Settings V2
# by https://steamcommunity.com/id/FamesGER/
# Adds "hidden" settings to the light and unlocks remapping shadowAtten and noiseStrength
# Allows settings like shadows to be animated

import sfm, sfmUtils, sfmApp, vs
from vs import g_pDataModel as dm
from PySide import QtCore

# logging, error and debug messages
debug = False

class log():
    @staticmethod
    def info(msg):
        sfmApp.ExecuteGameCommand("echo [More-Light] " + str(msg))
        print("[More-Light] " + str(msg))

    @staticmethod
    def err(msg):
        dm.SetUndoEnabled(True)
        sfm.ErrMsg("[More-Light] " + msg + "\n")
    
    @staticmethod
    def debug(msg):
        if debug:
            sfmApp.ExecuteGameCommand("echo [More-Light] [DEBUG] " + str(msg))
            print("[More-Light] [DEBUG] " + str(msg))

class lightSettings():

    def __init__(self, animSet, shot):
        self.animSet = animSet
        self.shot = shot
        log.debug("Processing \'%s\'" %str(self.animSet.name))

        self.lightSet = self.animSet.light
        # add our own controlgroup to the light's control stack
        self.controlGroup = self.animSet.FindOrAddControlGroup(self.animSet.GetRootControlGroup(), 'More-Light')

        self.markName = "_MoreLight"

    # add a slider to the light animation set with the according internal controls/operators/channels
    def AddControl(self, ctrlName, attrName, varStart= 0.5, varDefault= 0.5, remap= False):
        log.debug("Adding control \'%s\' for \'%s\' in \'%s\'." % (ctrlName, attrName, str(self.animSet.name)))

        #elem = vs.CreateElement("")
        ctrl = sfmUtils.CreateControlAndChannel(str(attrName), vs.AT_FLOAT, float(varStart), self.animSet, self.shot)
        ctrl.SetValue("defaultValue", float(varDefault))
        ctrl.channel.SetOutput(self.lightSet, attrName)
        try:
            self.controlGroup.AddControl(ctrl)
        except:
            log.err("Failed to add \'%s\'!" %attrName)
            return
        else:
            log.debug("Added \'%s\'" % str(ctrl.channel.name))

        if remap:
            self.EnableRemap(ctrlName, attrName)

    # enable remapping on a control/lider
    def EnableRemap(self, ctrl, attr = None, min= 0, max= 1):
        # its very important to disable Undo/History logging to avoid crashse. Sorse™
        # "Here be dragons." - Valve VDC
        if attr is None:
            attr = ctrl

        log.debug("Remapping \'%s\'" %attr)

        # create a timer for memory-sensitive operations
        timer = QtCore.QTimer()

        # disable undo
        dm.SetUndoEnabled(False)
        # find corresponding control
        try:
            control = self.animSet.FindControl(ctrl)
        except:
            log.err("Could not find control for \'%s\' in \'%s\'!" %(ctrl, str(self.animSet.name)))
        else:
            log.debug("Found control for \'%s\'" %ctrl)

        # scaling operator
        try:
            op = vs.CreateElement("DmeExpressionOperator", str(control.name) + "_rescale", self.shot.GetFileId())
            op.SetValue("expr", "lerp(value, lo, hi)")
            op.AddAttribute("value", vs.AT_FLOAT)
            op.AddAttribute("lo", vs.AT_FLOAT)
            op.AddAttribute("hi", vs.AT_FLOAT)
            op.SetValue("lo", min)
            op.SetValue("hi", max)
            self.animSet.AddOperator(op)          
        except:
            log.err("Could not add scale operator to \'%s\'!" %ctrl)
            return
        else:
            log.debug("Added scale operator \'%s\' to \'%s\'" %(str(op.name),str(self.animSet.name)))

        # connection
        try:
            conn = sfmUtils.CreateConnection(str(control.name) + "_conn", op, "result", self.animSet)
            conn.AddOutput(self.lightSet, attr)
        except Exception as e:
            log.err("Could not connect \'%s\'!" %ctrl)
            log.debug()
            return
        else:
            log.debug("Connected \'%s\' to \'%s\' in \'%s\'" %(str(conn.name), str(attr), str(self.animSet.name)))

        # time sensitive stuff ahead. SFM *will* crash if they're done at the same time.
        timer.singleShot(10, lambda: (control.channel.SetValue("toAttribute", "value")))
        timer.singleShot(15, lambda: (control.channel.SetValue("toElement", op)))
        # enable undo
        timer.singleShot(30, lambda: (dm.SetUndoEnabled(True)))
        timer.singleShot(30, lambda: (dm.ClearUndo()))

    # mark the animationset so we know it was already processed
    def SetProcessed(self):
        log.debug("Marking \'%s\' as processed" %str(self.animSet.name))
        mark = self.animSet.AddAttributeAsBool(self.markName)
        mark.SetValue(True)

    def IsProcessed(self):
        if self.animSet.HasAttribute(self.markName):
            dm.SetUndoEnabled(True)
            return True

def main():
    # get animationset
    aSet = sfm.GetCurrentAnimationSet()
    # get shot
    shot = sfm.GetCurrentShot()
    # are we a light?
    try:
        foo = aSet.light
    except:
        log.err("Selected Animation Set \'%s\' is not a light!" %str(aSet.name))
        return

    light = lightSettings(aSet, shot)

    # check if we are already processed
    if light.IsProcessed():
        log.info("\'%s\' is already processed!" %str(aSet.name))
        return # exit if we are

    # add the controls
    light.AddControl("Ambient Occlusion", "ambientOcclusion", 1, 1)
    light.AddControl("Cast Shadows", "castsShadows", 1, 1)
    light.AddControl("Cast Volumetrics", "volumetric", 0, 0)
    light.AddControl("Show Light Frustum", "drawShadowFrustum", 0, 0)
    light.AddControl("Set as Uberlight", "uberlight", 0, 0)
    light.AddControl("Roundness", "roundness", 0.8, 0.8, True)
    # remap some stuff
    light.EnableRemap("shadowAtten")
    light.EnableRemap("noiseStrength")
    # mark the light as processed
    light.SetProcessed()

if __name__ ==  "__main__":
    main()