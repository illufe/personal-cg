from pyfbsdk import *
import math

DEFAULT_HEIGHT = 180.0
BODY_SCALE_INDICES = [
    FBSkeletonNodeId.kFBSkeletonHeadIndex,
    FBSkeletonNodeId.kFBSkeletonNeckIndex,
    FBSkeletonNodeId.kFBSkeletonChestIndex,
    FBSkeletonNodeId.kFBSkeletonWaistIndex,
    FBSkeletonNodeId.kFBSkeletonHipsIndex,
    FBSkeletonNodeId.kFBSkeletonLeftHipIndex,
    FBSkeletonNodeId.kFBSkeletonRightHipIndex,
    FBSkeletonNodeId.kFBSkeletonLeftKneeIndex,
    FBSkeletonNodeId.kFBSkeletonRightKneeIndex,
    FBSkeletonNodeId.kFBSkeletonLeftAnkleIndex,
    FBSkeletonNodeId.kFBSkeletonRightAnkleIndex,
    FBSkeletonNodeId.kFBSkeletonLeftFootIndex,
    FBSkeletonNodeId.kFBSkeletonRightFootIndex,
]
TRC_NAMESPACE = 'TRC'
TRC_TOP_MARKER = 'Head_Back'
TRC_POS_MARKERS = [
    'RPelvis',
    'LPelvis',
    'RShoulder',
    'LShoulder',
    'Root',
    'LowerBack',
    'MiddleBack',
    'RShoulderOffset',
    'TopNeck',
    'LHeel',
    'RHeel',
]
TRC_POS_OFFSET = -2
LEG_ROTATE_Z = [
    (FBSkeletonNodeId.kFBSkeletonLeftHipIndex, ('LHeel','LToe')),
    (FBSkeletonNodeId.kFBSkeletonRightHipIndex, ('RHeel','RToe')),
]
SHOULDER_ROTATE_Z = [
    (FBSkeletonNodeId.kFBSkeletonLeftCollarIndex, ('LThumb','LWrist','LFinger'), 1),
    (FBSkeletonNodeId.kFBSkeletonRightCollarIndex, ('RThumb','RWrist','RFinger'), -1),
]
SHOULDER_ROTATE_Y = [
    (FBSkeletonNodeId.kFBSkeletonLeftCollarIndex, ('LThumb','LWrist','LFinger','LElbow'), -.7),
    (FBSkeletonNodeId.kFBSkeletonRightCollarIndex, ('RThumb','RWrist','RFinger','RElbow'), .7),
]
ARM_ROTATE_Y = [
    (FBSkeletonNodeId.kFBSkeletonLeftElbowIndex, 
     ('LThumb','LWrist','LFinger'), -1,
     FBSkeletonNodeId.kFBSkeletonLeftCollarIndex),
    (FBSkeletonNodeId.kFBSkeletonRightElbowIndex, 
     ('RThumb','RWrist','RFinger'), 1,
     FBSkeletonNodeId.kFBSkeletonRightCollarIndex),
]
ARM_HEIGHT_OFFSET = 4
ARM_SCALE_MAP = (FBSkeletonNodeId.kFBSkeletonLeftCollarIndex,
                 FBSkeletonNodeId.kFBSkeletonLeftWristIndex,
                 'LShoulder', 
                 'LWrist')
ARM_SCALE_INDICES = [
    FBSkeletonNodeId.kFBSkeletonLeftCollarIndex,
    FBSkeletonNodeId.kFBSkeletonLeftShoulderIndex,
    FBSkeletonNodeId.kFBSkeletonLeftElbowIndex,
    FBSkeletonNodeId.kFBSkeletonLeftWristIndex,
]

# Helper functions
def getTRC(name):
    node = FBFindModelByLabelName(':'.join([TRC_NAMESPACE,name]))
    assert node, 'Marker not found: %s' % name
    return node
    
def getTRC_Aver(nodes):
    aver = FBVector3d()
    for m in nodes:
        m = getTRC(m)
        aver += m.Translation.Data
    aver /= len(nodes)
    return aver

# Main function
def main():
    # Create new actor
    actor = FBActor('testActor')
    
    # Scale/Height offset
    topNode = getTRC(TRC_TOP_MARKER)
    
    ty = topNode.Translation[1]
    ratio = ty / DEFAULT_HEIGHT
    actor.HipsPosition *= ratio
    scale = FBVector3d((ratio,ratio,ratio))
    for i in BODY_SCALE_INDICES:
        actor.SetDefinitionScaleVector(i, scale)
        
    # Position offset
    aver = getTRC_Aver(TRC_POS_MARKERS)
    actor.HipsPosition = FBVector3d(aver[0], actor.HipsPosition[1], aver[2]+TRC_POS_OFFSET)
    
    # Legs rotation offset
    state = actor.GetCurrentSkeletonState()
    for i, markers in LEG_ROTATE_Z:
        m = FBMatrix()
        state.GetNodeMatrix(i, m)
        aver = getTRC_Aver(markers)
        
        a = aver[0] - m[12]
        b = m[13]
        r = math.atan2(a, b)
        d = math.degrees(r)
        v = FBVector3d(0, 0, d)
        actor.SetDefinitionRotationVector(i, v, False)
    
    # Shoulder rotation offset
    shoulderRotations = dict()
    for i, markers, comp in SHOULDER_ROTATE_Z:
        m = FBMatrix()
        state.GetNodeMatrix(i, m)
        aver = getTRC_Aver(markers)
        
        a = aver[1] - m[13] - ARM_HEIGHT_OFFSET
        b = abs(aver[0] - m[12])
        r = math.atan2(a, b)
        d = math.degrees(r)
        v = d*comp
        shoulderRotations.setdefault(i, [0,0,0])
        shoulderRotations.get(i)[2] = v
    
    for i, markers, comp in SHOULDER_ROTATE_Y:
        m = FBMatrix()
        state.GetNodeMatrix(i, m)
        aver = getTRC_Aver(markers)
        
        a = aver[2] - m[14]
        b = abs(aver[0] - m[12])
        r = math.atan2(a, b)
        d = math.degrees(r)
        v = d*comp
        shoulderRotations.setdefault(i, [0,0,0])
        shoulderRotations.get(i)[1] = v
        
    for i, l in shoulderRotations.items():
        v = FBVector3d(l)
        actor.SetDefinitionRotationVector(i, v, False)
    
    # Arm scale offset
    state = actor.GetCurrentSkeletonState()
    iShoulder, iWrist, tShoulder, tWrist = ARM_SCALE_MAP
    mShoulder = FBMatrix()
    mWrist = FBMatrix()
    state.GetNodeMatrix(iShoulder, mShoulder)
    state.GetNodeMatrix(iWrist, mWrist)
    
    vShoulder = FBVector3d((mShoulder[12], mShoulder[13], mShoulder[14]))
    vWrist = FBVector3d((mWrist[12], mWrist[13], mWrist[14]))
    tShoulder = getTRC(tShoulder).Translation.Data
    tWrist = getTRC(tWrist).Translation.Data
    
    lengthA = (vWrist - vShoulder).Length()
    lengthT = (tWrist - tShoulder).Length()
    ratio = lengthT / lengthA
    scale = FBVector3d((ratio,ratio,ratio))
    for i in ARM_SCALE_INDICES:
        actor.SetDefinitionScaleVector(i, scale, True)
        
    # Arm rotation offset
    state = actor.GetCurrentSkeletonState()
    for i, markers, comp, p in ARM_ROTATE_Y:
        m = FBMatrix()
        state.GetNodeMatrix(i, m)
        aver = getTRC_Aver(markers)
        
        a = aver[2] - m[14]
        b = abs(aver[0] - m[12])
        r = math.atan2(a, b)
        d = math.degrees(r)
        z = shoulderRotations.get(p)[2]
        v = FBVector3d(0, d*comp, z)
        actor.SetDefinitionRotationVector(i, v, False)
    
    return actor

if __name__ in ['__main__', '__builtin__']:
    main()
