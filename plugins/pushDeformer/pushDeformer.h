#ifndef PUSHDEFORMER_H
#define PUSHDEFORMER_H


#include <string.h>
#include <map>
#include <maya/MIOStream.h>
#include <math.h>

#include <stdio.h>
#include <map>

#include <maya/MPxDeformerNode.h>
#include <maya/MItGeometry.h>
#include <maya/MPxLocatorNode.h>

#include <maya/MFnNumericAttribute.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MFnMatrixData.h>

#include <maya/MFnPlugin.h>
#include <maya/MFnDependencyNode.h>

#include <maya/MTypeId.h>
#include <maya/MPlug.h>

#include <maya/MDataBlock.h>
#include <maya/MDataHandle.h>
#include <maya/MArrayDataHandle.h>

#include <maya/MPoint.h>
#include <maya/MFloatPointArray.h>
#include <maya/MVector.h>
#include <maya/MMatrix.h>
#include <maya/MFloatMatrix.h>

#include <maya/MDagModifier.h>
#include <maya/MMeshIntersector.h>

#include <maya/MFnTypedAttribute.h>
#include <maya/MFnMesh.h>
#include <maya/MPointArray.h>
#include <maya/MItMeshVertex.h>

#include <maya/MFnNumericAttribute.h>
#include <maya/MFnCompoundAttribute.h>
#include <maya/MFnMatrixAttribute.h>
#include <maya/MRampAttribute.h>
#include <maya/MFnEnumAttribute.h>
#include <maya/MGlobal.h>
#include <maya/MScriptUtil.h>
#include <maya/MThreadUtils.h>

using namespace std;

class pushDeformer : public MPxDeformerNode
{
public:
  pushDeformer();
  virtual ~pushDeformer();
  static  void* creator();
  static  MStatus initialize();

  // deformation function
  //
  virtual MStatus deform(MDataBlock& 		block,
			 MItGeometry& 	iter,
			 const MMatrix& 	mat,
			 unsigned int		multiIndex);

  virtual MStatus accessoryNodeSetup(MDagModifier& cmd);

public:
  // local node attributes
  static MTypeId id;
  static MObject mshCollider;
  static MObject blend;
  static MObject bulgeextend;
  static MObject bulge;
  static MObject offset;
  static MObject colliderMatrix;
  static MObject bulgeshape;
  static MObject threshold;

private:

};

#endif
