import os
import sys

class FEM:
    def __init__(self):
        self.nnodes = 0
        self.nelems = 0
        self.nnodesets = 0
        self.nelemsets = 0
        self.nodes = []
        self.elems = []
        self.nodesets = []
        self.elemsets = []

class Node:
    def __init__(self, id, coords):
        self.id = id
        self.coords = coords

class Element:
    def __init__(self, id, type, material, color, nnodes, cntvt):
        self.id = id
        self.type = type
        self.material = material
        self.color = color
        self.nnodes = nnodes
        self.cntvt = cntvt

class Group:
    def __init__(self, id, name):
        self.id = id
        self.type = 0
        self.name = name.strip()
        self.nitems = 0
        self.items = []

def Line2Float(line):
    return list(map(float, line.split()))

def Line2Int(line):
    return list(map(int, line.split()))

def UNV2411Reader(file, FEM):
    endFlag = '    -1'
    while True:
        line1 = file.readline()
        line2 = file.readline()
        if not line2:
            break
        if line1.startswith(endFlag):
            break
        dataline = Line2Int(line1)
        line2 = line2.replace('D', 'E')
        coords = Line2Float(line2)
        FEM.nodes.append(Node(dataline[0], coords))
        FEM.nnodes += 1
    return FEM

def UNV2412Reader(file, FEM):
    endFlag = '    -1'
    while True:
        line1 = file.readline()
        line2 = file.readline()
        if not line2:
            break
        if line1.startswith(endFlag):
            break
        dataline = Line2Int(line1)
        eltype = dataline[1]
        nnodes = dataline[-1]
        if eltype < 33:
            line3 = file.readline()
            cntvt = Line2Int(line3)
        else:
            cntvt = Line2Int(line2)
            if nnodes > 8:
                cntvt.extend(Line2Int(file.readline()))
            if nnodes > 16:
                cntvt.extend(Line2Int(file.readline()))
            if nnodes > 24:
                cntvt.extend(Line2Int(file.readline()))
        FEM.elems.append(Element(dataline[0], eltype, 0, 0, dataline[5], cntvt))
        FEM.nelems += 1
    return FEM

def UNV2467Reader(file, FEM):
    endFlag = '    -1'
    while True:
        line1 = file.readline()
        line2 = file.readline()
        if not line2:
            break
        if line1.startswith(endFlag):
            break
        dataline = Line2Int(line1)
        groupname = line2.strip()
        id = dataline[0]
        nitems = dataline[7]
        nlines = (nitems + 1) // 2
        lst = []
        for _ in range(nlines):
            dat = Line2Int(file.readline())
            lst.append(dat[0:3])
            if len(dat) > 4:
                lst.append(dat[4:7])
        nset = Group(id, groupname)
        elset = Group(id, groupname)
        nset.type = 7
        elset.type = 8
        for item in lst:
            if item[0] == 7:
                nset.items.append(item[1])
            elif item[0] == 8:
                elset.items.append(item[1])
        nset.nitems = len(nset.items)
        elset.nitems = len(elset.items)
        if nset.nitems > 0:
            FEM.nodesets.append(nset)
        if elset.nitems > 0:
            FEM.elemsets.append(elset)
        FEM.nnodesets = len(FEM.nodesets)
        FEM.nelemsets = len(FEM.elemsets)
    return FEM

class UNVParser:
    def __init__(self, filename):
        self.filename = filename
        self.FEM = FEM()
        self.startFlag = '    -1'
        self.endFlag = '    -1'
        self.datasetsIds = [2411, 2412, 2467, 2477]
        self.datasetsHandlers = [UNV2411Reader, UNV2412Reader, UNV2467Reader, UNV2467Reader]
        self.sections = []

    def scanfile(self):
        while True:
            line = self.file.readline()
            if not line:
                break
            if line.startswith(self.startFlag):
                id = int(self.file.readline())
                offset = self.file.tell()
                self.sections.append([id, offset])
                while not self.file.readline().startswith(self.endFlag):
                    pass
        self.file.seek(0)

    def parse(self):
        with open(self.filename, 'r', encoding='utf-8', errors='ignore') as f:
            self.file = f
            self.scanfile()
            for sectionId, offset in self.sections:
                if sectionId in self.datasetsIds:
                    self.file.seek(offset)
                    func = self.datasetsHandlers[self.datasetsIds.index(sectionId)]
                    self.FEM = func(self.file, self.FEM)
        return self.FEM
