from pyfbsdk import *


TRC_NAMESPACE = 'TRC'
TRC_REFERENCE = 'optical'
TRC_MAP = {
    FBSkeletonNodeId.kFBSkeletonHipsIndex: ['LPelvis', 'RPelvis', 'LowerBack', 'Root'], 
    FBSkeletonNodeId.kFBSkeletonLeftHipIndex: ['LThighIn', 'LKnee'],
    FBSkeletonNodeId.kFBSkeletonLeftKneeIndex: ['LAnkle', 'LHeel'], 
    FBSkeletonNodeId.kFBSkeletonLeftAnkleIndex: ['LMidfoot'], 
    FBSkeletonNodeId.kFBSkeletonLeftFootIndex: ['LToe'],
    FBSkeletonNodeId.kFBSkeletonRightHipIndex: ['RThighIn', 'RKnee'], 
    FBSkeletonNodeId.kFBSkeletonRightKneeIndex: ['RAnkle', 'RHeel'], 
    FBSkeletonNodeId.kFBSkeletonRightAnkleIndex: ['RMidfoot'], 
    FBSkeletonNodeId.kFBSkeletonRightFootIndex: ['RToe'], 
    FBSkeletonNodeId.kFBSkeletonChestIndex: ['TopNeck', 'FrontSternum', 'RShoulderOffset', 'MiddleBack'], 
    FBSkeletonNodeId.kFBSkeletonLeftCollarIndex: ['LShoulder'],
    FBSkeletonNodeId.kFBSkeletonLeftShoulderIndex: ['LBicep', 'LElbow'], 
    FBSkeletonNodeId.kFBSkeletonLeftElbowIndex: ['LWrist', 'LThumb', 'LFinger'], 
    FBSkeletonNodeId.kFBSkeletonRightCollarIndex: ['RShoulder'], 
    FBSkeletonNodeId.kFBSkeletonRightShoulderIndex: ['RBicep', 'RElbow'], 
    FBSkeletonNodeId.kFBSkeletonRightElbowIndex: ['RWrist', 'RThumb', 'RFinger'],
    FBSkeletonNodeId.kFBSkeletonHeadIndex: ['Head_Front', 'Head_Left', 'Head_Right', 'Head_Back']
}


# Helper functions
def getTRC(name):
    node = FBFindModelByLabelName(':'.join([TRC_NAMESPACE,name]))
    assert node, 'Marker not found: %s' % name
    return node

# Main function
def main():
    scene = FBSystem().Scene
    actor = scene.Actors[-1]
    actor.MarkerSet = mset = FBMarkerSet('testSet')
    for index, markers in TRC_MAP.iteritems():
        for m in markers:
            mset.AddMarker(index, getTRC(m))
    ref = getTRC(TRC_REFERENCE)
    mset.SetReferenceModel(ref)
    ##actor.Lock = True
    actor.Active = True

if __name__ in ['__main__', '__builtin__']:
    main()