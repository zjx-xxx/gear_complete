# -*- coding: mbcs -*-
# Do not delete the following import lines
from abaqus import *
from abaqusConstants import *
import __main__


def Macro2():
    import section
    import regionToolset
    import displayGroupMdbToolset as dgm
    import part
    import material
    import assembly
    import step
    import interaction
    import load
    import mesh
    import optimization
    import job
    import sketch
    import visualization
    import xyPlot
    import displayGroupOdbToolset as dgo
    import connectorBehavior
    from datetime import datetime

    timenow = datetime.now().strftime("%Y%m%d_%H%M")

    import numpy as np
    ##创建模型
    step = mdb.openStep('../gear_step/assembled_gear_pair.step',
                        scaleFromFile=OFF)
    mdb.models['Model-1'].PartFromGeometryFile(name='assembled_gear_pair-1',
                                               geometryFile=step, combine=False, dimensionality=THREE_D,
                                               type=DEFORMABLE_BODY)
    mdb.models['Model-1'].PartFromGeometryFile(name='assembled_gear_pair-2',
                                               geometryFile=step, bodyNum=2, combine=False, dimensionality=THREE_D,
                                               type=DEFORMABLE_BODY)
    a = mdb.models['Model-1'].rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    p1 = mdb.models['Model-1'].parts['assembled_gear_pair-1']
    p2 = mdb.models['Model-1'].parts['assembled_gear_pair-2']
    a.Instance(name='assembled_gear_pair-1-1', part=p1, dependent=ON)
    a.Instance(name='assembled_gear_pair-2-1', part=p2, dependent=ON)
    ##创建材料
    mdb.models['Model-1'].Material(name='Material-1')
    mdb.models['Model-1'].materials['Material-1'].Elastic(table=((210000.0, 0.3),
                                                                 ))
    mdb.models['Model-1'].materials['Material-1'].Density(table=((7.85e-09,),
                                                                 ))
    mdb.models['Model-1'].HomogeneousSolidSection(name='Section-1',
                                                  material='Material-1', thickness=None)
    ##应用材料
    c1 = p1.cells
    cells1 = c1.getSequenceFromMask(mask=('[#1 ]',), )
    region = regionToolset.Region(cells=cells1)
    p1.SectionAssignment(region=region, sectionName='Section-1', offset=0.0,
                         offsetType=MIDDLE_SURFACE, offsetField='',
                         thicknessAssignment=FROM_SECTION)
    with open('results.txt', 'w') as f:
        f.write(f"p1 cell:{len(p1.cells)}\n")

    c2 = p2.cells
    cells2 = c2.getSequenceFromMask(mask=('[#1 ]',), )
    region = regionToolset.Region(cells=cells2)
    p2.SectionAssignment(region=region, sectionName='Section-1', offset=0.0,
                         offsetType=MIDDLE_SURFACE, offsetField='',
                         thicknessAssignment=FROM_SECTION)

    elemType1 = mesh.ElemType(elemCode=C3D20R)
    elemType2 = mesh.ElemType(elemCode=C3D15)
    elemType3 = mesh.ElemType(elemCode=C3D10)

    # #齿轮1网格划分
    # p1.seedEdgeBySize(
    #     edges=p1.edges.getByBoundingBox(
    #         xMin=25, xMax=50,  # 通常设置为包含 contact_faces 的 box
    #         yMin=-15, yMax=15,
    #         zMin=-20, zMax=20
    #     ),
    #     size=4.0,  # ⬅️ 更小的种子尺寸（根据精度需求调整）
    #     deviationFactor=0.05,
    #     minSizeFactor=0.01
    # )

    # p1.setMeshControls(regions=cells1, algorithm=MEDIAL_AXIS)
    p1.setMeshControls(regions=cells1, elemShape=TET, technique=FREE, allowMapped=False)
    pickedRegions = (cells1,)
    p1.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2,
                                                        elemType3))
    p1.seedPart(size=6.0, deviationFactor=0.1, minSizeFactor=0.1)
    p1.generateMesh()
    # #齿轮2网格划分
    # p2.seedEdgeBySize(
    #     edges=p2.edges.getByBoundingBox(
    #         xMin=25, xMax=50,  # 通常设置为包含 contact_faces 的 box
    #         yMin=-15, yMax=15,
    #         zMin=-20, zMax=20
    #     ),
    #     size=4.0,  # ⬅️ 更小的种子尺寸（根据精度需求调整）
    #     deviationFactor=0.05,
    #     minSizeFactor=0.01
    # )

    # p2.setMeshControls(regions=cells2, algorithm=MEDIAL_AXIS)
    p2.setMeshControls(regions=cells2, elemShape=TET, technique=FREE, allowMapped=False)
    pickedRegions = (cells2,)
    p2.setElementType(regions=pickedRegions, elemTypes=(elemType1, elemType2,
                                                        elemType3))
    p2.seedPart(size=8.0, deviationFactor=0.1, minSizeFactor=0.1)
    p2.generateMesh()

    a.regenerate()
    mdb.saveAs(pathName='./mesh.cae')

    with open('results.txt', 'a') as f:
        f.write('mesh success\n')

    ##Node-Surface接触
    # 取得齿轮1实例所有面
    s1 = a.instances['assembled_gear_pair-1-1'].faces
    # 直接获取实例所有面（getSequenceFromMask可以省略）
    all_faces_gear1 = s1[:]
    # 在装配中定义名为 'Surf-1' 的面集合，包含齿轮1所有面
    a.Surface(side1Faces=all_faces_gear1, name='Surf-1')

    # 取得齿轮2实例所有面
    s2 = a.instances['assembled_gear_pair-2-1'].faces
    # 直接获取实例所有面（getSequenceFromMask可以省略）
    all_faces_gear2 = s2[:]
    # 在装配中定义名为 'Surf-2' 的面集合，包含齿轮1所有面
    a.Surface(side1Faces=all_faces_gear2, name='Surf-2')

    ##获取从动轮齿面上的点
    import numpy as np

    a = mdb.models['Model-1'].rootAssembly
    faces = a.instances['assembled_gear_pair-2-1'].faces

    tol = 10  # 容差，单位 mm
    gear_teeth_faces = []

    # 1. 选中齿面
    for face in faces:
        normal = np.array(face.getNormal())
        center = np.array(face.pointOn[0])

        if abs(normal[2]) < 0.5:  # 排除上下盖面
            if abs(center[0]) > tol:  # 排除中轴面
                gear_teeth_faces.append(face)

    # 2. 从这些面提取所有节点
    nodes_on_teeth = []
    labels_seen = set()

    for face in gear_teeth_faces:
        for node in face.getNodes():
            if node.label not in labels_seen:
                nodes_on_teeth.append(node)
                labels_seen.add(node.label)

    # 先获取所有节点标签（int）
    node_labels = [node.label for node in nodes_on_teeth]

    # 从实例中用标签提取 MeshNodeArray
    nodes_seq = a.instances['assembled_gear_pair-2-1'].nodes.sequenceFromLabels(node_labels)

    # 用这个 sequence 构建 Set
    a.Set(name='Set-1', nodes=nodes_seq)

    mdb.models['Model-1'].ContactProperty('IntProp-1')
    mdb.models['Model-1'].interactionProperties['IntProp-1'].TangentialBehavior(
        formulation=PENALTY,
        table=((0.15,),),
        fraction=0.01
    )
    mdb.models['Model-1'].interactionProperties['IntProp-1'].NormalBehavior(
        pressureOverclosure=HARD, allowSeparation=ON, contactStiffness=DEFAULT,
        clearanceAtZeroContactPressure=0.0,
        constraintEnforcementMethod=AUGMENTED_LAGRANGE)
    region1 = a.surfaces['Surf-1']
    region2 = a.sets['Set-1']
    mdb.models['Model-1'].SurfaceToSurfaceContactStd(name='Int-1',
                                                     createStepName='Initial', main=region1, secondary=region2,
                                                     sliding=FINITE, thickness=ON, interactionProperty='IntProp-1',
                                                     adjustMethod=NONE, initialClearance=OMIT, datumAxis=None,
                                                     clearanceRegion=None)


    with open('results.txt', 'a') as f:
        f.write('surface success\n')

    x, y, z = 0.0, 0.0, 0.0
    rp = a.ReferencePoint(point=(x, y, z))
    rpId = rp.id  # 获取ID
    r1 = a.referencePoints
    refPoints1 = (r1[rpId],)  # 取最后一个参考点对象
    x, y, z = 73.135, 0.0, 0.0
    rp = a.ReferencePoint(point=(x, y, z))
    rpId = rp.id  # 获取ID
    r1 = a.referencePoints
    refPoints2 = (r1[rpId],)  # 取最后一个参考点对象

    ##主动轮约束
    region1_1 = regionToolset.Region(referencePoints=refPoints1)

    faces = a.instances['assembled_gear_pair-1-1'].faces

    # 提供一个包围盒，筛选出处于该范围内的面（返回 FaceArray 类型）
    gear_teeth_faces = faces.getByBoundingBox(
        xMin=-10, xMax=10,
        yMin=-10, yMax=10,
        zMin=-20, zMax=20
    )

    # 使用 face 对象列表创建 region
    region1_2 = regionToolset.Region(side1Faces=gear_teeth_faces)
    mdb.models['Model-1'].Coupling(name='Constraint-1', controlPoint=region1_1,
                                   surface=region1_2, influenceRadius=WHOLE_SURFACE,
                                   couplingType=DISTRIBUTING,
                                   rotationalCouplingType=ROTATIONAL_STRUCTURAL, weightingMethod=UNIFORM,
                                   localCsys=None, u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

    ## 从动轮约束
    region2_1 = regionToolset.Region(referencePoints=refPoints2)

    faces = a.instances['assembled_gear_pair-2-1'].faces

    # 提供一个包围盒，筛选出处于该范围内的面（返回 FaceArray 类型）
    gear_teeth_faces = faces.getByBoundingBox(
        xMin=63.135, xMax=83.135,
        yMin=-10, yMax=10,
        zMin=-7.5, zMax=7.5
    )

    # 使用 face 对象列表创建 region
    region2_2 = regionToolset.Region(side1Faces=gear_teeth_faces)
    mdb.models['Model-1'].Coupling(name='Constraint-2', controlPoint=region2_1,
                                   surface=region2_2, influenceRadius=WHOLE_SURFACE,
                                   couplingType=DISTRIBUTING,
                                   rotationalCouplingType=ROTATIONAL_STRUCTURAL, weightingMethod=UNIFORM,
                                   localCsys=None, u1=ON, u2=ON, u3=ON, ur1=ON, ur2=ON, ur3=ON)

    with open('results.txt', 'a') as f:
        f.write('boundary success\n')

    mdb.models['Model-1'].ImplicitDynamicsStep(name='Step-1', previous='Initial',
                                               timePeriod=0.0058, maxNumInc=1000, initialInc=5.8e-05, minInc=5.8e-08,
                                               maxInc=1.16e-03,
                                               nlgeom=ON)
    region1 = regionToolset.Region(referencePoints=refPoints1)
    region2 = regionToolset.Region(referencePoints=refPoints2)
    mdb.models['Model-1'].Moment(name='Load-1', createStepName='Step-1',
                                 region=region1, cm3=62200.0, distributionType=UNIFORM, field='',
                                 localCsys=None)
    mdb.models['Model-1'].Moment(name='Load-2', createStepName='Step-1',
                                 region=region2, cm3=-60800.0, distributionType=UNIFORM, field='',
                                 localCsys=None)
    mdb.models['Model-1'].TabularAmplitude(name='Amp-1', timeSpan=STEP,
                                           smooth=SOLVER_DEFAULT, data=((0.0, 0.0), (0.0058, 1.0)))
    # mdb.models['Model-1'].VelocityBC(name='BC-1', createStepName='Step-1',
    #     region=region1, v1=0.0, v2=0.0, v3=0.0, vr1=0.0, vr2=0.0, vr3=1125.0,
    #     amplitude='Amp-1', localCsys=None, distributionType=UNIFORM,
    #     fieldName='')
    mdb.models['Model-1'].DisplacementBC(name='BC-1', createStepName='Step-1',
                                         region=region1, u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=UNSET,
                                         amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                                         localCsys=None)
    mdb.models['Model-1'].DisplacementBC(name='BC-2', createStepName='Step-1',
                                         region=region2, u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=UNSET,
                                         amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                                         localCsys=None)
    mdb.saveAs(pathName=f'./ZZ35_{timenow}.cae')
    import os
    try:
        os.remove('ZZ35.lck')
    except FileNotFoundError:
        pass
    mdb.Job(name=f'ZZ35_{timenow}', model='Model-1', description='', type=ANALYSIS,
        atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
        memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
        explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
        modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
        scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=0, numCpus=6,
        numDomains=6, numGPUs=1)
    mdb.jobs[f'ZZ35_{timenow}'].submit(consistencyChecking=OFF)
    mdb.jobs[f'ZZ35_{timenow}'].waitForCompletion()
    with open('results.txt', 'a') as f:
        f.write('calculate success\n')


Macro2()