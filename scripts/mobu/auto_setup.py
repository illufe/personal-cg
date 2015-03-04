import os

from pyfbsdk import FBFilePopup, FBFilePopupStyle, FBApplication, FBSystem

import create_actor_from_opticals
reload(create_actor_from_opticals)
import map_opticals_to_actor
reload(map_opticals_to_actor)


# Construction of this are expensive, so we create them once.
gSYSTEM = FBSystem()
gAPPLICATION = FBApplication()

# Get take object by it's name.
def GetTakeByName(pName):
    lFound = [lTake for lTake in gSYSTEM.Scene.Takes if lTake.Name==pName]
    if lFound:
        return lFound[0]
    else:
        return None

# Create take with pName.
def createTake(pName):
    #bug in here
    #lTake = FBTake(pName)
    #gSYSTEM.Scene.Components.append(lTake)
    #workaround
    lIsNew = True
    lTakeName = pName
    lTake = GetTakeByName(lTakeName)
    if lTake == None:
        lTake = gSYSTEM.CurrentTake.CopyTake(lTakeName)
        count = lTake.GetLayerCount()
        while (count > 1 ):
            count = count - 1
            lTake.RemoveLayer(count)
    else:
        lIsNew = False
    gSYSTEM.CurrentTake = lTake
    return lTake, lIsNew


def main():
    # Create the popup and set necessary initial values.
    lFp = FBFilePopup()
    lFp.Caption = "Select T-Pose"
    lFp.Style = FBFilePopupStyle.kFBFilePopupOpen

    # BUG: If we do not set the filter, we will have an exception.
    lFp.Filter = "*.trc"

    # Set the default path.
    lFp.Path = r"Z:\wanghuan\mocap"

    # Get the GUI to show.
    lRes = lFp.Execute()

    if not lRes:
        return

    gAPPLICATION.FileNew()
    res = gAPPLICATION.FileImport(lFp.FullFilename)
    if not res:
        return

    create_actor_from_opticals.main()
    map_opticals_to_actor.main()

    dirname = os.path.dirname(lFp.FullFilename)
    files = os.listdir(dirname)
    for f in files:
        if not f.endswith('.trc'):
            continue

        if 'Unnamed' in f:
            continue

        path = os.path.join(dirname, f)
        createTake(os.path.splitext(f)[0])
        gAPPLICATION.FileImport(path, True)


if __name__ in ['__main__', '__builtin__']:
    main()
