#ifndef PUSHCOLLIDER_H
#define PUSHCOLLIDER_H

#include "pushDeformer.h"

class PushCollider
{
 public:
  PushCollider(MDataHandle& handle,
	       MDataHandle& matHandle,
	       float scale) ;
  ~PushCollider() {};

  void changeVolume(float value);
  void resetVolume();

  void setBBS(MDataHandle &handle);
  bool allIntersections(MFloatPoint raySource,
			MFloatPoint rayDir,
			MMeshIsectAccelParams intersectAccel,
			MFloatPointArray &hitPoints,
			MFloatArray& hitRayParams);
  int thresholdValue() {return _thresholdValue;};

  MPointOnMesh getClosestPoint(MPoint pt);
  MMatrix colliderMat() { return _colliderMat; };

 private:
  MFloatPointArray _points;
  MFloatPointArray _newPoints;
  MFnMesh _fn ;
  MStatus _status;
  MObject _object;

  int _polycount;
  MIntArray _pcounts;
  MIntArray _pconnect;
  MMeshIntersector _mIntersector;
  MMatrix _colliderMat;
  int _colliderBBSize;
  int _thresholdValue;
};

PushCollider::PushCollider(MDataHandle& handle,
			   MDataHandle& matHandle,
			   float scale)
:_object(handle.asMesh()),_fn(MFnMesh(_object,&_status))

{

  _points.clear();
  _fn.getPoints(_points,MSpace::kObject);
  _newPoints.clear();
  _fn.getPoints(_newPoints,MSpace::kObject);
  _colliderMat = matHandle.asMatrix();

  changeVolume(scale);
}

void
PushCollider::resetVolume()
{
  _fn.createInPlace(_points.length(),_polycount,_points,_pcounts,_pconnect);
}

MPointOnMesh
PushCollider::getClosestPoint(MPoint pt)
{
  MPointOnMesh ptOnMesh;
  _mIntersector.getClosestPoint(pt, ptOnMesh);
  return ptOnMesh;
}

void
PushCollider::changeVolume(float value)
{
    int colnum = _points.length();

    MVector colliderPointNormalInit;
    _fn.getVertexNormal(0, colliderPointNormalInit , MSpace::kObject);
    _newPoints[0] = _points[0] + (colliderPointNormalInit*value);

#ifdef _OPENMP
#pragma omp parallel for
#else
#endif
    for (int i = 1 ; i < colnum ; i ++) {
      MVector colliderPointNormal;
      _fn.getVertexNormal(i, colliderPointNormal , MSpace::kObject);
      _newPoints[i] = _points[i] + (colliderPointNormal*value);
    }

    _polycount = _fn.numPolygons();
    _fn.getVertices(_pcounts, _pconnect);
    _fn.createInPlace(_points.length(),_polycount,_newPoints,_pcounts,_pconnect);

    _mIntersector.create(_object,_colliderMat);
}


void
PushCollider::setBBS(MDataHandle &handle)
{
  // get collider boundingbox for threshold
  double3& colliderBBSizeValue = handle.asDouble3();
  MVector colliderBBVector(colliderBBSizeValue[0], colliderBBSizeValue[1], colliderBBSizeValue[2]);
  _colliderBBSize = colliderBBVector.length();
  _thresholdValue = _colliderBBSize*2;
}

bool
PushCollider::allIntersections(MFloatPoint raySource,
			       MFloatPoint rayDir,
			       MMeshIsectAccelParams intersectAccel,
			       MFloatPointArray& hitPoints,
			       MFloatArray& hitRayParams)
{
  return _fn.allIntersections(raySource, rayDir, NULL, NULL, true,  MSpace::kWorld, _thresholdValue, true, &intersectAccel, true, hitPoints, &hitRayParams, NULL, NULL, NULL, NULL, 0.000001f, &_status);
}


#endif
