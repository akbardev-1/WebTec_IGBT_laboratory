"""Parametric concept CAD: automated locomotive IGBT assembly test cell.

All dimensions in mm. No OEM dimensional drawing was supplied; dimensions,
equipment envelopes and internal arrangements are provisional planning geometry.
Run with Python 3 and CadQuery 2.7: python build_model.py [output_directory]
"""
from pathlib import Path
import sys, json, math, struct, time
import cadquery as cq
import numpy as np

OUT = Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
PARTS=[]
COLORS={
 'frame': '#25303b', 'panel':'#c5ced5', 'stainless':'#a1afb8',
 'silver':'#d5dde0', 'black':'#151e28', 'white':'#eeeede',
 'red':'#cb3842', 'yellow':'#efbd32', 'green':'#39af79',
 'blue':'#43a8de', 'copper':'#ba7747', 'screen':'#122b3e',
 'glass':'#a7d2e2', 'orange':'#ed9538', 'ceramic':'#dfcfad',
}
GROUPS={
 'structure':('Cabinet & frame',[0,-0.30,0]),
 'enclosure':('Test chamber',[0,0.20,-0.32]),
 'door':('Interlocked access door',[-0.35,0,0.50]),
 'fixture':('Sliding fixture',[-0.12,0,0.38]),
 'dut':('IGBT assembly',[-0.12,0.20,0.58]),
 'rack':('Measurement rack',[0.35,0.15,0]),
 'power':('Pulse power & load',[-0.35,-0.08,0.30]),
 'controls':('Control cabinet',[0.30,-0.08,0.28]),
 'operator':('Operator interface',[0.52,0.06,0.20]),
}

def rgb(c):
    c=COLORS.get(c,c).lstrip('#')
    return [int(c[i:i+2],16)/255 for i in (0,2,4)]

def add(name,shape,group,color='panel',alpha=1,cover=False,detail=''):
    if hasattr(shape,'val'): shape=shape.val()
    if not shape.isValid(): raise ValueError('Invalid solid: '+name)
    PARTS.append(dict(name=name,shape=shape,group=group,color=rgb(color),alpha=alpha,cover=cover,detail=detail))
    return shape

def box(name,x,y,z,w,d,h,group,color='panel',**kwargs):
    return add(name,cq.Workplane('XY').box(w,d,h).translate((x,y,z)),group,color,**kwargs)

def cylinder(name,x,y,z,r,h,group,color='silver',axis='z',**kwargs):
    shape=cq.Workplane('XY').circle(r).extrude(h).translate((0,0,-h/2))
    if axis=='y': shape=shape.rotate((0,0,0),(1,0,0),90)
    elif axis=='x': shape=shape.rotate((0,0,0),(0,1,0),90)
    return add(name,shape.translate((x,y,z)),group,color,**kwargs)

def tube(name,a,b,r,group,color):
    a,b=cq.Vector(*a),cq.Vector(*b)
    v=b-a
    return add(name,cq.Solid.makeCylinder(r,v.Length,a,v.normalized()),group,color)

def screw(name,x,y,z,group='fixture',r=5,cover=False):
    cylinder(name+' washer',x,y+1,z,r+3,2,group,'stainless',axis='y',cover=cover)
    shape=cq.Workplane('XZ').polygon(6,2*r).extrude(5).translate((x,y,z))
    add(name,shape,group,'silver',cover=cover)

def label_bar(name,x,y,z,w,h,group,color,cover=False):
    box(name,x,y,z,w,1.5,h,group,color,cover=cover)

# 1. Floor-standing enclosure, 1,800 x 850 mm cabinet body.
for x in (-840,840):
    for y in (-365,365):
        cylinder('Leveling foot %s %s'%(x,y),x,y,17,48,24,'structure','black')
        cylinder('Foot pad %s %s'%(x,y),x,y,35,36,14,'structure','silver')
        cylinder('Adjustable stem %s %s'%(x,y),x,y,83,13,90,'structure','stainless')
        box('Corner post %s %s'%(x,y),x,y,484,55,55,738,'structure','frame')
for z in (145,815):
    for y in (-395,395):
        box('Horizontal frame %s %s'%(y,z),0,y,z,1800,60,60,'structure','frame')
    for x in (-870,870):
        box('Side rail %s %s'%(x,z),x,0,z,60,790,60,'structure','frame')
box('Lower mounting floor',0,0,185,1740,790,7,'structure','stainless')
box('Workbench top',0,0,850,1840,890,24,'structure','stainless')
box('Red fascia',0,-448,831,1840,4,12,'structure','red')
box('Rear lower panel',0,424,495,1790,3,600,'structure','panel',cover=True)
for x in (-898,898):
    box('Lower side cover '+str(x),x,0,495,3,840,600,'structure','panel',cover=True)
box('Power control partition',175,0,490,3,800,600,'structure','stainless')

for idx,(x,w) in enumerate(((-603,548),(-31,548),(571,596))):
    door=cq.Workplane('XY').box(w,5,578).translate((x,-427,497))
    # Slots are genuine openings in the CAD panels.
    cuts=[]
    for row in range(5):
        for col in range(12):
            cuts.append(cq.Workplane('XY').box(24,12,7).translate((x-176+col*32,-427,310+row*16)).val())
    door=door.cut(cq.Compound.makeCompound(cuts))
    add('Lower service door '+str(idx+1),door,'structure','panel',cover=True)
    box('Door latch '+str(idx+1),x+w/2-35,-438,510,19,16,90,'structure','black',cover=True)
    for zz in (285,695):
        cylinder('Service door hinge %s %s'%(idx,zz),x-w/2+8,-431,zz,6,45,'structure','frame',cover=True)
    label_bar('Cabinet title plate '+str(idx+1),x-75,-431,700,205,25,'structure','frame',cover=True)
    for sx in (-1,1): screw('Service panel screw %s %s'%(idx,sx),x+sx*(w/2-18),-431,766,'structure',3,cover=True)

# 2. Test chamber and removable covers.
for x in (-885,145):
    for y in (-405,405):
        box('Chamber column %s %s'%(x,y),x,y,1290,35,35,850,'enclosure','frame')
for z in (885,1692):
    for y in (-405,405): box('Chamber width rail %s %s'%(y,z),-370,y,z,1065,35,35,'enclosure','frame')
    for x in (-885,145): box('Chamber depth rail %s %s'%(x,z),x,0,z,35,810,35,'enclosure','frame')
box('Chamber roof',-370,0,1712,1065,845,3,'enclosure','panel',cover=True)
box('Chamber left cover',-905,0,1290,3,845,840,'enclosure','panel',cover=True)
box('Chamber rear cover',-370,425,1290,1065,3,840,'enclosure','panel',cover=True)
box('Chamber instrument partition',165,0,1290,3,845,840,'enclosure','stainless',cover=True)
box('Chamber work surface',-370,0,890,995,750,8,'enclosure','silver')
box('Overhead task light housing',-370,-100,1665,600,60,20,'enclosure','frame')
box('Task light diffuser',-370,-100,1653,555,40,4,'enclosure','white')
box('Cable entry cover',-370,393,1065,420,25,190,'enclosure','black')

# Hinged door: all door components use one common pivot in the viewer.
for x in (-861,123): box('Access door stile '+str(x),x,-444,1294,65,35,817,'door','panel')
for z in (918,1670): box('Access door cross rail '+str(z),-369,-444,z,920,35,65,'door','panel')
for x in (-820,82): box('Window gasket vertical '+str(x),x,-444,1294,14,38,690,'door','black')
for z in (955,1633): box('Window gasket horizontal '+str(z),-369,-444,z,902,38,14,'door','black')
box('Transparent access window',-369,-447,1294,892,6,668,'door','glass',alpha=.17)
for z in (1045,1540):
    cylinder('Door hinge barrel '+str(z),-895,-438,z,12,85,'enclosure','frame')
    box('Door hinge leaf '+str(z),-869,-463,z,50,8,85,'door','frame')
for z in (1145,1400): tube('Handle standoff '+str(z),(112,-469,z),(112,-510,z),9,'door','black')
tube('Door pull handle',(112,-510,1145),(112,-510,1400),12,'door','black')
box('Coded door interlock body',175,-440,1065,36,40,75,'enclosure','red',detail='Independent access interlock envelope; architecture requires validation.')
box('Door interlock actuator',142,-451,1065,24,15,40,'door','silver')

# 3. Sliding DUT fixture and support, designed around a heavy replaceable assembly.
for x in (-700,-40):
    box('Linear rail '+str(x),x,-10,913,28,620,24,'fixture','stainless')
    for y in (-210,190): box('Rail carriage %s %s'%(x,y),x,y,933,60,80,24,'fixture','frame')
box('Slide-out fixture tray',-370,-30,952,790,640,14,'fixture','silver')
box('Tray front lip',-370,-350,975,790,12,50,'fixture','stainless')
tube('Tray handle left',(-480,-359,973),(-480,-405,973),8,'fixture','black')
tube('Tray handle right',(-260,-359,973),(-260,-405,973),8,'fixture','black')
tube('Tray pull handle',(-480,-405,973),(-260,-405,973),10,'fixture','black')
for x in (-620,-120):
    box('DUT support foot '+str(x),x,-40,979,95,255,40,'fixture','stainless')
    box('DUT locating upright '+str(x),x,70,1115,35,35,260,'fixture','frame')
    box('Insulating cradle pad '+str(x),x,-55,1005,80,160,12,'fixture','white')
    box('Retaining clamp base '+str(x),x,-175,1010,60,55,30,'fixture','silver')
    cylinder('Retaining clamp spindle '+str(x),x,-175,1042,7,48,'fixture','stainless')
    tube('Retaining clamp lever '+str(x),(x,-175,1060),(x+45,-175,1080),8,'fixture','red')

# 4. Recognizable IGBT package. Shape follows the supplied photograph; no scale was supplied.
CX=-370
box('IGBT rear body',CX,-10,1245,455,145,470,'dut','black',detail='Photo-based envelope, approximately 500 x 560 x 180 mm; verify OEM drawing.')
box('IGBT rear thermal plate',CX,72,1245,435,18,460,'dut','stainless')
for i in range(13): box('Rear cooling rib %02d'%i,CX-195+i*32,99,1245,8,38,432,'dut','frame')
box('IGBT lower frame bridge',CX,-80,1014,555,86,36,'dut','black')
for s in (-1,1):
    x=CX+s*264
    rail=cq.Workplane('XY').box(55,85,485).translate((x,-80,1250))
    for z in (1065,1170,1275,1380):
        cut=cq.Workplane('XZ').center(x,z).slot2D(70,26,90).extrude(110,both=True).translate((0,-80,0))
        rail=rail.cut(cut)
    rail=rail.cut(cq.Workplane('XZ').center(x,1450).circle(15).extrude(110,both=True).translate((0,-80,0)))
    add('IGBT side mounting rail '+str(s),rail,'dut','black')

profile=[(-145,1028),(145,1028),(145,1440),(63,1440),(63,1500),(-25,1500),(-25,1440),(-110,1440),(-110,1355),(-145,1280)]
plate=cq.Workplane('XZ').polyline([(CX+x,z) for x,z in profile]).close().extrude(13).translate((0,-119,0))
for x in (CX-53,CX+77):
    plate=plate.cut(cq.Workplane('XZ').center(x,1403).circle(15).extrude(30).translate((0,-110,0)))
add('IGBT white insulated front',plate,'dut','white')
tab=cq.Workplane('XY').box(88,10,54).translate((CX+19,-123,1523))
for x in (CX-3,CX+41):
    tab=tab.cut(cq.Workplane('XZ').center(x,1524).circle(11).extrude(30).translate((0,-110,0)))
add('Upper dual-hole terminal tab',tab,'dut','silver')
for row,z in enumerate((1055,1130,1205,1280)):
    for col,x in enumerate((CX-113,CX,CX+113)):
        screw('IGBT front bolt %s-%s'%(row+1,col+1),x,-137,z,'dut',8)
for x in (CX-53,CX+77):
    ring=cq.Workplane('XZ').circle(21).circle(15).extrude(3).translate((x,-134,1403))
    add('Upper terminal ring '+str(x),ring,'dut','silver')
box('Terminal insulating separator',CX,-139,1170,285,12,12,'dut','white')
box('Assembly ID label',CX,-134,1340,90,1,25,'dut','silver')

box('OEM gate driver envelope',CX+204,-19,1245,45,120,250,'dut','frame',detail='Keep the OEM driver and interface; connector and electronics details are placeholders.')
cylinder('Gate-driver connector shell',CX+242,-65,1130,18,30,'dut','stainless',axis='x')
for yy,zz in ((-73,1122),(-57,1122),(-73,1138),(-57,1138)):
    cylinder('Interface pin %s %s'%(yy,zz),CX+260,yy,zz,2.5,12,'dut','silver',axis='x')
for s in (-1,1):
    box('Insulated terminal adapter '+str(s),CX+s*244,10,1465,105,85,55,'fixture','red')
    box('Adapter clamp '+str(s),CX+s*244,-38,1465,60,8,35,'fixture','frame')
    # Short conceptual connections only: no cable sizing or electrical topology implied.
    tube('Protected power link '+str(s),(CX+s*244,48,1465),(CX+s*300,200,1350),13,'fixture','black')
    tube('Protected power drop '+str(s),(CX+s*300,200,1350),(CX+s*300,200,975),13,'fixture','black')
for i in range(2):
    tube('Driver cable drop '+str(i),(CX+277,-20+i*15,1130),(CX+320,160+i*15,980),5,'fixture','orange')

# 5. Instrument rack: generic commercial envelopes, not a selected vendor product.
for x in (230,835): box('Rack upright '+str(x),x,-330,1290,35,50,830,'rack','frame')
box('Rack rear cover',532,365,1290,640,5,830,'rack','panel',cover=True)
box('Rack right side',867,10,1290,5,720,830,'rack','panel',cover=True)
box('Rack top',535,10,1712,665,720,5,'rack','panel',cover=True)
for row,(z,h,title) in enumerate(((1550,215,'Oscilloscope'),(1330,175,'Static measurement'),(1140,175,'Insulation tester'),(955,150,'PXI and test controller'))):
    box(title+' chassis',532,-10,z,562,610,h,'rack','frame')
    box(title+' front panel',532,-324,z,580,14,h-8,'rack','panel')
    for x in (248,816):
        box(title+' rack ear '+str(x),x,-323,z,22,15,h,'rack','stainless')
        for zz in (-h/2+15,h/2-15): screw(title+' fixing %s %s'%(x,zz),x,-335,z+zz,'rack',3)
    if row<3:
        box(title+' display bezel',440,-337,z+10,300,7,h-42,'rack','black')
        box(title+' screen',440,-342,z+10,277,2,h-64,'rack','screen')
        for col in range(4):
            for rr in range(3): cylinder(title+' key %s %s'%(col,rr),635+col*38,-338,z+45-rr*30,6,8,'rack','stainless',axis='y')
        cylinder(title+' encoder',763,-343,z-36,21,17,'rack','black',axis='y')
        for col,c in enumerate(('green','black','red')): cylinder(title+' input '+str(col),626+col*38,-343,z-h/2+22,9,12,'rack',c,axis='y')
    else:
        for i in range(8):
            box('Controller slot %02d'%i,310+i*61,-337,z,49,9,122,'rack','black')
            label_bar('Slot status %02d'%i,310+i*61,-344,z+44,14,4,'rack','green')
            for j in range(3): box('Slot socket %s %s'%(i,j),310+i*61,-344,z+20-j*24,18,4,12,'rack','stainless')
    box(title+' shelf',532,0,z-h/2-8,600,660,6,'rack','stainless')

# Scope screen grid and pulse trace are modeled geometry, visible in any CAD/GLB app.
for x in range(315,566,25): label_bar('Scope grid x '+str(x),x,-344,1560,1,140,'rack','#23465b')
for z in range(1495,1626,22): label_bar('Scope grid z '+str(z),440,-344,z,260,1,'rack','#23465b')
wave=[(316,1532),(361,1532),(361,1598),(407,1598),(407,1532),(458,1532),(458,1574),(490,1574),(490,1532),(565,1532)]
for i,(a,b) in enumerate(zip(wave,wave[1:])): tube('Scope pulse segment '+str(i),(a[0],-347,a[1]),(b[0],-347,b[1]),1.6,'rack','yellow')
for z in (1350,1322,1295): label_bar('Measurement screen readout '+str(z),414,-346,z,210 if z==1350 else 135,5,'rack','blue')
for z in (1170,1145,1120): label_bar('Insulation screen readout '+str(z),413,-346,z,215 if z==1170 else 120,5,'rack','green')

# 6. Lower pulse-power and load compartment, separated from controls.
box('Power equipment backplate',-340,288,498,980,10,548,'power','stainless')
box('Pulse supply envelope',-650,40,330,335,475,250,'power','frame',detail='Generic supply envelope; voltage, current and stored energy are not specified.')
box('Pulse supply face',-650,-202,330,320,8,230,'power','panel')
box('Supply display',-690,-209,383,130,3,48,'power','screen')
for i in range(9): box('Supply vent '+str(i),-650,-209,275+i*7,220,3,2,'power','black')
for i,x in enumerate((-510,-350,-190)):
    cylinder('DC link capacitor '+str(i+1),x,130,594,58,205,'power','frame')
    cylinder('Capacitor insulating top '+str(i+1),x,130,700,57,8,'power','white')
    for y in (109,151): cylinder('Capacitor stud %s %s'%(i,y),x,y,717,7,26,'power','copper')
box('DC positive busbar',-350,109,730,420,30,5,'power','copper')
box('DC negative busbar',-350,151,730,420,30,5,'power','copper')
box('Busbar insulating cover',-350,130,751,455,104,18,'power','red')
box('Pulse inductor base',-135,-142,223,340,330,35,'power','frame')
box('Pulse inductor core',-135,-142,366,85,85,255,'power','frame')
for i in range(11):
    ring=cq.Workplane('XY').circle(118).circle(95).extrude(12).translate((-135,-142,247+i*19))
    add('Inductor copper turn %02d'%i,ring,'power','copper')
for x in (-285,15): box('Inductor clamp '+str(x),x,-142,373,18,275,278,'power','stainless')
box('Discharge resistor mounting plate',-725,278,650,230,10,245,'power','frame')
for j in range(3):
    box('Discharge resistor body '+str(j),-725,245,570+j*76,190,48,42,'power','ceramic')
    for x in (-832,-618): cylinder('Resistor terminal %s %s'%(j,x),x,244,570+j*76,5,18,'power','copper',axis='x')
box('Main contactor',50,245,635,115,100,135,'power','black')
box('Contactor label',50,190,635,68,4,62,'power','white')
for x in (18,80): cylinder('Contactor connection '+str(x),x,237,715,8,30,'power','copper')

# 7. Control equipment with independent safety hardware envelope.
box('Control mounting backplate',523,295,498,615,12,550,'controls','stainless')
for z in (350,555,735): box('DIN rail '+str(z),523,275,z,565,12,26,'controls','silver')
for i,x in enumerate((300,358,416,474)):
    box('Safety relay module '+str(i+1),x,220,568,45,96,135,'controls','yellow')
    label_bar('Safety module label '+str(i),x,170,580,30,54,'controls','white')
for i in range(5):
    x=576+i*44
    box('PLC IO module '+str(i+1),x,224,570,36,90,143,'controls','frame')
    for j in range(5): box('IO status LED %s %s'%(i,j),x,176,615-j*14,4,3,4,'controls','green')
box('Control power supply',356,220,360,175,100,150,'controls','silver')
for i in range(15): box('24 V terminal '+str(i+1),505+i*18,250,350,14,48,55,'controls','blue' if i%3==0 else 'frame')
for x in (240,800): box('Vertical cable duct '+str(x),x,255,505,45,55,535,'controls','white')
box('Bottom cable duct',520,252,260,590,58,45,'controls','white')
box('Controller PC',565,-60,330,290,320,210,'controls','frame')
for i in range(9): box('PC cooling fin '+str(i),430+i*33,-60,442,12,320,14,'controls','black')

# 8. Monitor, keyboard and physical operator controls.
box('Monitor mounting bracket',889,80,1400,40,105,160,'operator','frame')
tube('Monitor arm segment 1',(900,80,1410),(1060,80,1410),27,'operator','stainless')
tube('Monitor arm segment 2',(1060,80,1410),(1130,-170,1410),23,'operator','stainless')
cylinder('Monitor arm pivot',1060,80,1410,36,85,'operator','black')
box('Operator monitor housing',1115,-204,1415,540,58,340,'operator','black')
box('Operator monitor screen',1115,-235,1415,504,3,304,'operator','screen')
label_bar('HMI header',1115,-238,1536,482,37,'operator','blue')
box('HMI assembly preview',970,-239,1415,153,2,177,'operator','#243e52')
box('HMI assembly silhouette',969,-242,1415,66,2,118,'operator','white')
for i in range(5):
    label_bar('HMI sequence line '+str(i),1190,-239,1480-i*31,240,19,'operator','#d2dfe6')
    cylinder('HMI sequence marker '+str(i),1082,-242,1480-i*31,5,3,'operator','green' if i==0 else 'stainless',axis='y')
label_bar('Output off status area',1115,-239,1297,482,40,'operator','white')
label_bar('Output off indicator',1010,-242,1297,100,9,'operator','frame')
tube('Keyboard support',(885,0,950),(1115,-330,970),24,'operator','frame')
box('Keyboard shelf',1115,-400,1000,560,320,16,'operator','frame')
box('Keyboard base',1050,-410,1015,370,143,16,'operator','black')
for row in range(5):
    for col in range(15):
        if row==4 and 4<=col<=8: continue
        box('Key %02d %02d'%(row,col),884+col*23,-462+row*25,1026,19,19,7,'operator','stainless')
box('Space bar',1022,-362,1026,111,19,7,'operator','stainless')
mouse=cq.Workplane('XY').ellipse(28,45).extrude(20).translate((1320,-409,1008))
add('Mouse',mouse,'operator','black')
box('Operator button panel',900,-450,930,320,75,120,'operator','panel')
for name,x,color,rad in (('Emergency stop',795,'red',29),('Start',910,'green',19),('Reset',1005,'blue',19)):
    cylinder(name+' bezel',x,-493,936,rad+6,7,'operator','yellow' if name=='Emergency stop' else 'black',axis='y')
    cylinder(name+' button',x,-507,936,rad,25,'operator',color,axis='y')
    label_bar(name+' nameplate',x,-490,895,70,12,'operator','frame')
cylinder('Stack light mount',786,195,1745,21,67,'operator','stainless')
for i,color in enumerate(('green','yellow','red')):
    cylinder('Stack light '+color,786,195,1794+i*47,31,42,'operator',color)
    cylinder('Stack light separator '+str(i),786,195,1771+i*47,33,5,'operator','black')
cylinder('Stack light cap',786,195,1910,34,8,'operator','black')

print('Built',len(PARTS),'valid components',flush=True)

# Export an assembly STEP retaining individual named solids and colors.
assembly=cq.Assembly(name='IGBT_Test_Cell_Concept')
for index,p in enumerate(PARTS):
    assembly.add(p['shape'],name='%03d_%s'%(index,p['name'].replace(' ','_')),color=cq.Color(*p['color'],p['alpha']))
assembly.save(str(OUT/'IGBT_Test_Cell.step'),exportType='STEP')
print('STEP exported',flush=True)

# Triangulate once, then use the same physical geometry in the GLB and offline viewer.
meshes=[]
for index,p in enumerate(PARTS):
    vertices,triangles=p['shape'].tessellate(0.8,0.22)
    v=np.array([(q.x,q.z,-q.y) for q in vertices],dtype=np.float32)/1000
    t=np.array(triangles,dtype=np.uint32)
    normals=np.zeros_like(v)
    n=np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]])
    for corner in range(3): np.add.at(normals,t[:,corner],n)
    norms=np.linalg.norm(normals,axis=1)
    normals/=np.maximum(norms[:,None],1e-9)
    meshes.append(dict(id=index,name=p['name'],group=p['group'],color=p['color'],alpha=p['alpha'],cover=p['cover'],detail=p['detail'],
      positions=np.round(v,6).reshape(-1).tolist(),normals=np.round(normals,5).reshape(-1).tolist(),indices=t.reshape(-1).tolist(),
      bounds=[v.min(axis=0).tolist(),v.max(axis=0).tolist()]))
    if index%150==0: print('Meshed',index,flush=True)

model=dict(title='Automated IGBT Test Cell',revision='Concept 01',units='metres',
 groups={k:dict(label=v[0],explode=v[1]) for k,v in GROUPS.items()},meshes=meshes,
 doorPivot=[-.895,1.294,.438],provisional=True,
 dimensions=dict(cabinetWidth_mm=1800,cabinetDepth_mm=850,worktopHeight_mm=850,chamberRoofHeight_mm=1714,stackLightHeight_mm=1914),
 note='Provisional concept geometry based on the supplied project presentation and proposed test cell. OEM dimensions, ratings, circuits, containment and safety validation remain required.')
(OUT/'model_data.json').write_text(json.dumps(model,separators=(',',':')))

# glTF 2.0 binary: Y-up, metres, named nodes and PBR materials.
doc=dict(asset=dict(version='2.0',generator='CadQuery concept assembly; provisional dimensions',copyright='Project concept model'),scene=0,
 scenes=[dict(name='IGBT Test Cell',nodes=[])],nodes=[],meshes=[],materials=[],buffers=[],bufferViews=[],accessors=[],extras=dict(revision='Concept 01',dimensions=model['dimensions'],note=model['note']))
binary=bytearray()
def accessor(array,typ,ctype,limits=False):
    while len(binary)%4: binary.append(0)
    arr=np.array(array,dtype=np.float32 if ctype==5126 else np.uint32)
    offset=len(binary); binary.extend(arr.tobytes())
    bview=len(doc['bufferViews']); doc['bufferViews'].append(dict(buffer=0,byteOffset=offset,byteLength=arr.nbytes))
    components={'SCALAR':1,'VEC3':3}[typ]
    a=dict(bufferView=bview,componentType=ctype,count=arr.size//components,type=typ)
    if limits:
        a['min']=arr.reshape(-1,components).min(axis=0).tolist();a['max']=arr.reshape(-1,components).max(axis=0).tolist()
    ai=len(doc['accessors']); doc['accessors'].append(a);return ai

matmap={}
for mesh in meshes:
    key=tuple(mesh['color'])+(mesh['alpha'],)
    if key not in matmap:
        matmap[key]=len(doc['materials'])
        mat=dict(name='material_'+str(len(matmap)),pbrMetallicRoughness=dict(baseColorFactor=mesh['color']+[mesh['alpha']],metallicFactor=.25,roughnessFactor=.48),doubleSided=True)
        if mesh['alpha']<1: mat.update(alphaMode='BLEND')
        doc['materials'].append(mat)
    pa=accessor(mesh['positions'],'VEC3',5126,True);na=accessor(mesh['normals'],'VEC3',5126);ia=accessor(mesh['indices'],'SCALAR',5125)
    mi=len(doc['meshes']);doc['meshes'].append(dict(name=mesh['name'],primitives=[dict(attributes=dict(POSITION=pa,NORMAL=na),indices=ia,material=matmap[key])]))
    ni=len(doc['nodes']);doc['nodes'].append(dict(name=mesh['name'],mesh=mi,extras=dict(group=mesh['group'],removableCover=mesh['cover'],detail=mesh['detail'])))
    doc['scenes'][0]['nodes'].append(ni)
doc['buffers']=[dict(byteLength=len(binary))]
js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
binary.extend(b'\0'*((-len(binary))%4))
glb=struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4E4F534A)+js+struct.pack('<II',len(binary),0x004E4942)+binary
(OUT/'IGBT_Test_Cell.glb').write_bytes(glb)
manifest=[dict(id=m['id'],name=m['name'],group=m['group'],removable_cover=m['cover'],detail=m['detail']) for m in meshes]
(OUT/'parts_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(parts=len(PARTS),triangles=sum(len(m['indices'])//3 for m in meshes),step_bytes=(OUT/'IGBT_Test_Cell.step').stat().st_size,glb_bytes=len(glb)),indent=2),flush=True)
