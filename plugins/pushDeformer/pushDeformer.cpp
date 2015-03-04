#include "pushDeformer.h"
#include "omp.h"


struct hitData {
  MFloatPoint hitPoint;
  int collisionStatus;
  float dist;
};


MTypeId     pushDeformer::id( 0x8101c );
MObject     pushDeformer::mshCollider;
MObject     pushDeformer::blend;
MObject     pushDeformer::bulgeextend;
MObject     pushDeformer::bulge;
MObject     pushDeformer::offset;
MObject     pushDeformer::colliderMatrix;
MObject     pushDeformer::bulgeshape;
MObject     pushDeformer::threshold;


pushDeformer::pushDeformer() {}
pushDeformer::~pushDeformer() {}

void* pushDeformer::creator()
{
  return new pushDeformer();
}

MStatus pushDeformer::initialize()
{
  MStatus status;

  MFnTypedAttribute typedAttr;
  MFnNumericAttribute nAttr;
  MFnCompoundAttribute cmpAttr;
  MFnMatrixAttribute mAttr;
  MRampAttribute rAttr;
  MFnEnumAttribute eAttr;

  mshCollider = typedAttr.create("collider","col",MFnData::kMesh);
  nAttr.setHidden(true);
  nAttr.setStorable(true);
  nAttr.setUsesArrayDataBuilder(true);
  addAttribute(mshCollider);
  attributeAffects(mshCollider,outputGeom);

  blend = nAttr.create("blend","ble",MFnNumericData::kFloat,0.0,&status);
  nAttr.setKeyable(true);
  nAttr.setStorable(true);
  nAttr.setSoftMin(0);
  nAttr.setSoftMax(1);
  addAttribute(blend);
  attributeAffects(blend,outputGeom);

  bulgeextend = nAttr.create("bulgeextend","bex",MFnNumericData::kFloat,0.0,&status);
  nAttr.setKeyable(true);
  nAttr.setStorable(true);
  nAttr.setSoftMin(0);
  nAttr.setSoftMax(10);
  addAttribute(bulgeextend);
  attributeAffects(bulgeextend,outputGeom);

  bulge = nAttr.create("bulge","blg",MFnNumericData::kFloat,1.0,&status);
  nAttr.setKeyable(true);
  nAttr.setStorable(true);
  nAttr.setSoftMin(0);
  nAttr.setSoftMax(10);
  addAttribute(bulge);
  attributeAffects(bulge,outputGeom);

  offset = nAttr.create("offset","off",MFnNumericData::kFloat,0.0,&status);
  nAttr.setKeyable(true);
  nAttr.setStorable(true);
  nAttr.setSoftMin(0);
  nAttr.setSoftMax(1);
  addAttribute(offset);
  attributeAffects(offset,outputGeom);

  threshold = nAttr.create("threshold","thr",MFnNumericData::kFloat,69.0,&status);
  nAttr.setKeyable(true);
  nAttr.setStorable(true);
  nAttr.setSoftMin(0);
  nAttr.setSoftMax(100);
  addAttribute(threshold);
  attributeAffects(threshold,outputGeom);

  colliderMatrix=mAttr.create("colliderMatrix","collMatr");
  addAttribute(colliderMatrix);
  attributeAffects(colliderMatrix,outputGeom);

  bulgeshape=rAttr.createCurveRamp("bulgeshape","blgshp");
  addAttribute(bulgeshape);
  attributeAffects(bulgeshape,outputGeom);

  return MStatus::kSuccess;
}


MStatus
pushDeformer::deform( MDataBlock& block,
		      MItGeometry& iter,
		      const MMatrix& inMatrix,
		      unsigned int geomIndex)

{
  MThreadUtils::syncNumOpenMPThreads();
  MStatus status = MStatus::kUnknownParameter;

  MDataHandle envData = block.inputValue(envelope, &status);
  if (MS::kSuccess != status) return status;
  float env = envData.asFloat();

  if (env == 0.0) {
    return MS::kSuccess;
  }

  MDataHandle offsetData = block.inputValue(offset, &status);
  if (MS::kSuccess != status) return status;
  float offsetValue = offsetData.asFloat();

  MDataHandle bulgeExtendData = block.inputValue(bulgeextend, &status);
  if (MS::kSuccess != status) return status;
  float bulgeExtendValue = bulgeExtendData.asFloat();

  MDataHandle bulgeData = block.inputValue(bulge, &status);
  if (MS::kSuccess != status) return status;
  float bulgeValue = bulgeData.asFloat();

  MDataHandle blendData = block.inputValue(blend, &status);
  if (MS::kSuccess != status) return status;
  float blendValue = blendData.asFloat();

  MDataHandle thresholdData = block.inputValue(threshold, &status);
  if (MS::kSuccess != status) return status;
  float thresholdValue = thresholdData.asFloat();

  MObject thisNode = thisMObject();
  MRampAttribute bulgeshapeHandle(thisNode,bulgeshape);

  MArrayDataHandle outputData = block.outputArrayValue( outputGeom, &status );
  MDataHandle outMesh = outputData.outputValue( &status );
  MObject meshObj;
  meshObj = outMesh.asMesh();
  MObject meshTObj = outMesh.asMeshTransformed();
  MFnMesh meshTFn(meshTObj, &status) ;
  if (MS::kSuccess != status) {
    cout << "meshTFn is not established. " << endl;
    return status;
  }

  //------------Get Mesh and Collider---------------
  MMeshIsectAccelParams intersectAccel;
  intersectAccel = meshTFn.autoUniformGridParams();

  MFloatPointArray meshPoints;
  meshPoints.clear();
  meshTFn.getPoints(meshPoints, MSpace::kWorld);

  MFloatPointArray outPoints;
  outPoints.clear();
  meshTFn.getPoints(outPoints, MSpace::kWorld);

  int nPoints = iter.count();

  // set this in to array
  MFloatVectorArray normals;
  status = meshTFn.getVertexNormals(false, normals, MSpace::kWorld);

  // --- Collider
  MDataHandle colliderHandle = block.inputValue( mshCollider, &status );
  if (colliderHandle.type() != MFnData::kMesh) {
    printf("Incorrect deformer geometry type %d\n", colliderHandle.type());
    return MStatus::kFailure;
  }
  if (MS::kSuccess != status) return status;

  MDataHandle colliderMatrixHandle = block.inputValue(colliderMatrix, &status);
  if (MS::kSuccess != status) return status;

  MObject colObject = colliderHandle.asMesh();
  if (colObject.isNull() ) return MS::kSuccess;

  MFnMesh colfn(colObject, &status) ;
  if (MS::kSuccess != status) {
    cout << "error to get colfn" << endl;
    return status;
  }

  // collision geometry data
  int polycount;
  MIntArray pcounts;
  MIntArray pconnect;

  MFloatPointArray colPoints;
  colPoints.clear();
  colfn.getPoints(colPoints,MSpace::kObject);

  MMatrix colliderMat;
  colliderMat = colliderMatrixHandle.asMatrix();

  if (offsetValue){
    int colnum = colPoints.length();

    MFloatPointArray colNewPoints;
    colNewPoints.clear();
    colNewPoints.setLength(colnum);
    MFloatVectorArray colNormals;
    colfn.getVertexNormals(false, colNormals, MSpace::kObject);

#ifdef _OPENMP
#pragma omp parallel for
#endif
    for (int i = 0 ; i < colnum ; i ++) {
      colNewPoints[i] = colPoints[i] + colNormals[i]*offsetValue;
    }

    polycount = colfn.numPolygons();
    colfn.getVertices(pcounts, pconnect);
    colfn.createInPlace(colnum,polycount,colNewPoints,pcounts,pconnect);
  }

  //------------Get Intersection---------------
  map<int,hitData> hitMap;
  // set mesh index array, weights.
  MIntArray _ids; // this can be in the object local scoop
  MFloatArray _weights; // this can be in the object local scoop
  _ids.setLength(nPoints);
  _weights.setLength(nPoints);

  bool noIntersections = true;

  int i = 0;
  for(iter.reset();!iter.isDone();iter.next()) {
    int id = iter.index();
    _ids[i] = id;
    float weight = weightValue(block,geomIndex,id);
    _weights[i] = weight;
    if(weight==0.0) continue;

    MFloatPoint raySource;
    raySource.x = meshPoints[id].x;
    raySource.y = meshPoints[id].y;
    raySource.z = meshPoints[id].z;

    MFloatVector rayDir;
    rayDir = normals[id] ;
    rayDir *= -1;

    MFloatPointArray hitPoints;
    hitPoints.clear();

    bool gotHit = colfn.allIntersections(raySource, rayDir, NULL, NULL, true,  MSpace::kWorld,
					 thresholdValue, false, &intersectAccel, true,
					 hitPoints, NULL, NULL, NULL, NULL, NULL,
					 0.000001f, &status);
    hitData data;
    data.collisionStatus = 0;
    if (gotHit) {
      unsigned int hitCount = hitPoints.length();
      if((hitCount % 2) == 1) {
	data.collisionStatus = 1;
	data.hitPoint = hitPoints[0];
	noIntersections = false;
      }
    }
    data.dist = 0.0;
    hitMap[i]=data;
    i++;
  }

  // No collistion at all, then return this deformer
  if (noIntersections) {
    if (offsetValue)
      colfn.createInPlace(colPoints.length(),polycount,colPoints,pcounts,pconnect);
    block.setClean(outputGeom);
    return MS::kSuccess;
  }

  //------------Get Closest Point---------------
  MPointArray closestPoints;
  closestPoints.setLength(nPoints);

  MMeshIntersector mIntersector;
  mIntersector.create(colObject,colliderMat);

  float max_dist = 0.0;

#ifdef _OPENMP
#pragma omp parallel for schedule(guided)
#endif
  for (i = 0 ; i < nPoints ; i ++ ) {
    float weight = _weights[i];
    if(weight==0.0) continue;

    int id = _ids[i];
    MPoint pt;
    pt.x = meshPoints[id].x;
    pt.y = meshPoints[id].y;
    pt.z = meshPoints[id].z;

    MPointOnMesh ptOnMesh;
    mIntersector.getClosestPoint(pt,ptOnMesh);
    MPoint closestPoint = ptOnMesh.getPoint();
    closestPoint *= colliderMat;
    closestPoints.set(closestPoint, i);
    if (hitMap[i].collisionStatus) {
      hitMap[i].dist = pt.distanceTo(closestPoint);
      if (hitMap[i].dist > max_dist) max_dist = hitMap[i].dist;
    }
  }

  //------------Main Loop---------------
  float maxDeformation = 0.0;

#ifdef _OPENMP
#pragma omp parallel for
#endif
  for (i = 0 ; i < nPoints ; i ++ ) {
    float weight = _weights[i];
    if(weight==0.0) continue;

    hitData data = hitMap[i];
    if(data.collisionStatus) {
      int id = _ids[i];
      MPoint pt;
      pt.x = meshPoints[id].x;
      pt.y = meshPoints[id].y;
      pt.z = meshPoints[id].z;

      MPoint worldPoint;
      worldPoint = closestPoints[i];
      if ( blendValue > 0) {
	MPoint hitPoint = MPoint(data.hitPoint);
	worldPoint = worldPoint + ((hitPoint-worldPoint) * (blendValue*(data.dist/max_dist)));
	MPointOnMesh ptOnMesh;
	mIntersector.getClosestPoint(worldPoint,ptOnMesh);
	MPoint closestPoint = ptOnMesh.getPoint();
	worldPoint = closestPoint * colliderMat;
      }

      // update the maximum deformation distance for the bulge strength
      float deformationDistance = pt.distanceTo(worldPoint);
      if (maxDeformation < deformationDistance) maxDeformation = deformationDistance;

      pt +=(worldPoint-pt)*env*weight;
      outPoints[id].x = pt.x;
      outPoints[id].y = pt.y;
      outPoints[id].z = pt.z;
    }
  }

  //------------Bulge---------------

#ifdef _OPENMP
#pragma omp parallel for
#endif
  for (i = 0 ; i < nPoints ; i ++ ) {
    int id = _ids[i];
    float weight = _weights[i];
    hitData data = hitMap[i];
    if((weight==0.0) or (data.collisionStatus)) continue;

    MPoint pt = outPoints[id];
    float bulgePntsDist = pt.distanceTo(closestPoints[i]);

    // calculate the relative distance of the meshpoint based on the maximum bulgerange
    float relativedistance = bulgePntsDist/(bulgeExtendValue+0.00001);

    //get the bulge curve
    float bulgeAmount;
    bulgeshapeHandle.getValueAtPosition(relativedistance, bulgeAmount);
    pt += normals[id]*bulgeExtendValue*(bulgeValue/5)*env*bulgeAmount *maxDeformation*weight;

    outPoints[id].x = pt.x;
    outPoints[id].y = pt.y;
    outPoints[id].z = pt.z;
  }

  //------------Finishing---------------
  for(iter.reset();!iter.isDone();iter.next()) {
    int id = iter.index();
    MPoint pt = outPoints[id];
    pt *= inMatrix.inverse(); //Put point in object space
    iter.setPosition(pt);
  }

  if (MS::kSuccess != status) {
    cout << " setAllPosition got failed." << endl;
  }

  if (offsetValue) {
    colfn.createInPlace(colPoints.length(),polycount,colPoints,pcounts,pconnect);
  }

  block.setClean(outputGeom);

  return status;
}



MStatus
pushDeformer::accessoryNodeSetup(MDagModifier& cmd)
{
  MStatus result;

  MObject thisNode = thisMObject();
  MRampAttribute bulgeshapeattr(thisNode,bulgeshape,&result);
  MFloatArray a1,b1;
  MIntArray c1;

  a1.append(float(0.0));
  a1.append(float(0.2));
  a1.append(float(1.0));

  b1.append(float(0.0));
  b1.append(float(1.0));
  b1.append(float(0.0));

  c1.append(MRampAttribute::kSpline);
  c1.append(MRampAttribute::kSpline);
  c1.append(MRampAttribute::kSpline);

  bulgeshapeattr.addEntries(a1,b1,c1);
  return result;
}


// standard initialization procedures
//

MStatus initializePlugin( MObject obj )
{
  MStatus result;
  MFnPlugin plugin( obj, PLUGIN_COMPANY, "1.0", "Any");
  result = plugin.registerNode("pushDeformer", pushDeformer::id, pushDeformer::creator,
			       pushDeformer::initialize, MPxNode::kDeformerNode );
  cout << "PushDeformer 1.0.1" << " (built " << __DATE__ << " " << __TIME__ ")" << endl;
  return result;
}

MStatus uninitializePlugin( MObject obj)
{
  MStatus result;
  MFnPlugin plugin( obj );
  result = plugin.deregisterNode( pushDeformer::id );
  return result;
}
