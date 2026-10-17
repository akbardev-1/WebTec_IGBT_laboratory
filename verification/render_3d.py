"""Offscreen GLES 3 renderer using the viewer's exact shaders and exported mesh."""
import ctypes as C, ctypes.util, json, math, re, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=(ROOT/'static/model.html').read_text()
DATA=json.loads(re.search(r'<script id="modelData" type="application/json">(.*?)</script>',TEMPLATE,re.S).group(1))
CUT='--cutaway' in sys.argv
W,H=1600,1200
E=C.CDLL(C.util.find_library('EGL'))
def efunc(name,result,args):
 f=getattr(E,name);f.restype=result;f.argtypes=args;return f
ptr=C.c_void_p;I=C.c_int;U=C.c_uint;F=C.c_float
getproc=efunc('eglGetProcAddress',ptr,[C.c_char_p])
getdisplay=C.CFUNCTYPE(ptr,U,ptr,C.POINTER(I))(getproc(b'eglGetPlatformDisplayEXT'))
display=getdisplay(0x31DD,None,None)
major,minor=I(),I()
assert efunc('eglInitialize',U,[ptr,C.POINTER(I),C.POINTER(I)])(display,C.byref(major),C.byref(minor))
assert efunc('eglBindAPI',U,[U])(0x30A0)
attrs=(I*15)(0x3033,1,0x3040,0x40,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3025,24,0x3038)
config=ptr();count=I()
assert efunc('eglChooseConfig',U,[ptr,C.POINTER(I),C.POINTER(ptr),I,C.POINTER(I)])(display,attrs,C.byref(config),1,C.byref(count)) and count.value
surface=efunc('eglCreatePbufferSurface',ptr,[ptr,ptr,C.POINTER(I)])(display,config,(I*5)(0x3057,W,0x3056,H,0x3038))
context=efunc('eglCreateContext',ptr,[ptr,ptr,ptr,C.POINTER(I)])(display,config,None,(I*3)(0x3098,3,0x3038))
assert context and surface
assert efunc('eglMakeCurrent',U,[ptr,ptr,ptr,ptr])(display,surface,surface,context)
def gf(name,result,args):
 p=getproc(('gl'+name).encode());assert p,name;return C.CFUNCTYPE(result,*args)(p)
gl={}
specs={
 'GetString':(C.c_char_p,[U]),'GetError':(U,[]),'CreateShader':(U,[U]),
 'ShaderSource':(None,[U,I,C.POINTER(C.c_char_p),C.POINTER(I)]),'CompileShader':(None,[U]),
 'GetShaderiv':(None,[U,U,C.POINTER(I)]),'GetShaderInfoLog':(None,[U,I,C.POINTER(I),ptr]),
 'CreateProgram':(U,[]),'AttachShader':(None,[U,U]),'LinkProgram':(None,[U]),'GetProgramiv':(None,[U,U,C.POINTER(I)]),
 'GetProgramInfoLog':(None,[U,I,C.POINTER(I),ptr]),'UseProgram':(None,[U]),'GetUniformLocation':(I,[U,C.c_char_p]),
 'UniformMatrix4fv':(None,[I,I,U,C.POINTER(F)]),'Uniform4fv':(None,[I,I,C.POINTER(F)]),'Uniform3fv':(None,[I,I,C.POINTER(F)]),'Uniform1f':(None,[I,F]),'Uniform1i':(None,[I,I]),
 'GenVertexArrays':(None,[I,C.POINTER(U)]),'BindVertexArray':(None,[U]),'GenBuffers':(None,[I,C.POINTER(U)]),'BindBuffer':(None,[U,U]),'BufferData':(None,[U,C.c_ssize_t,ptr,U]),
 'EnableVertexAttribArray':(None,[U]),'VertexAttribPointer':(None,[U,I,U,U,I,ptr]),'GenTextures':(None,[I,C.POINTER(U)]),'BindTexture':(None,[U,U]),
 'TexImage2D':(None,[U,I,I,I,I,I,U,U,ptr]),'TexParameteri':(None,[U,U,I]),'ActiveTexture':(None,[U]),
 'GenFramebuffers':(None,[I,C.POINTER(U)]),'BindFramebuffer':(None,[U,U]),'FramebufferTexture2D':(None,[U,U,U,U,I]),'DrawBuffers':(None,[I,C.POINTER(U)]),'ReadBuffer':(None,[U]),'CheckFramebufferStatus':(U,[U]),
 'Enable':(None,[U]),'Disable':(None,[U]),'DepthMask':(None,[U]),'Viewport':(None,[I,I,I,I]),'ClearColor':(None,[F,F,F,F]),'Clear':(None,[U]),
 'BlendFunc':(None,[U,U]),'DrawElements':(None,[U,I,U,ptr]),'Finish':(None,[]),'ReadPixels':(None,[I,I,I,I,U,U,ptr])}
for name,(r,a) in specs.items():gl[name]=gf(name,r,a)
print(gl['GetString'](0x1F02).decode(),flush=True)
def program(vs,fs):
 p=gl['CreateProgram']()
 for typ,src in ((0x8B31,vs),(0x8B30,fs)):
  s=gl['CreateShader'](typ);code=C.c_char_p(src.encode());gl['ShaderSource'](s,1,C.byref(code),None);gl['CompileShader'](s);status=I();gl['GetShaderiv'](s,0x8B81,C.byref(status))
  if not status.value:
   log=C.create_string_buffer(8192);gl['GetShaderInfoLog'](s,8192,None,log);raise RuntimeError(log.value.decode())
  gl['AttachShader'](p,s)
 gl['LinkProgram'](p);status=I();gl['GetProgramiv'](p,0x8B82,C.byref(status));assert status.value,'Program link failure'
 return p
vs=re.search(r'const vs=`(.*?)`;',TEMPLATE,re.S).group(1)
fs=re.search(r'const fs=`(.*?)`;',TEMPLATE,re.S).group(1)
prog=program(vs,fs)
depth=program('#version 300 es\nlayout(location=0) in vec3 aPos;uniform mat4 uModel,uLight;void main(){gl_Position=uLight*uModel*vec4(aPos,1.);}', '#version 300 es\nprecision highp float;void main(){}')
def loc(p,n):return gl['GetUniformLocation'](p,n.encode())
uni={n:loc(prog,n) for n in ['uModel','uVP','uLight','uColor','uEye','uSelected','uGround','uShadow']}
def m4(location,m):
 a=np.array(m.T,dtype=np.float32).copy();gl['UniformMatrix4fv'](location,1,0,a.ctypes.data_as(C.POINTER(F)))
def fv(location,a):
 x=(F*len(a))(*a);gl['Uniform%sfv'%len(a)](location,1,x)
def generated(fun):
 x=U();gl[fun](1,C.byref(x));return x.value
def mesh(m):
 m['vao']=generated('GenVertexArrays');gl['BindVertexArray'](m['vao'])
 for attribute,key in ((0,'positions'),(1,'normals')):
  arr=np.array(m[key],np.float32);b=generated('GenBuffers');gl['BindBuffer'](0x8892,b);gl['BufferData'](0x8892,arr.nbytes,arr.ctypes.data,0x88E4);gl['EnableVertexAttribArray'](attribute);gl['VertexAttribPointer'](attribute,3,0x1406,0,0,None)
 arr=np.array(m['indices'],np.uint32);b=generated('GenBuffers');gl['BindBuffer'](0x8893,b);gl['BufferData'](0x8893,arr.nbytes,arr.ctypes.data,0x88E4);m['count']=len(arr);return m
meshes=[mesh(m) for m in DATA['meshes'] if not(CUT and (m['cover'] or m['group']=='door'))]
ground=mesh(dict(positions=[-4,-.003,-4,4,-.003,-4,4,-.003,4,-4,-.003,4],normals=[0,1,0]*4,indices=[0,2,1,0,3,2],color=[.86,.91,.93],alpha=1))
def norm(v):return v/np.linalg.norm(v)
def look(eye,target):
 z=norm(eye-target);x=norm(np.cross([0,1,0],z));y=np.cross(z,x);m=np.eye(4);m[:3,:3]=[x,y,z];m[:3,3]=[-x@eye,-y@eye,-z@eye];return m
def ortho(l,r,b,t,n,f):
 m=np.eye(4);m[0,0]=2/(r-l);m[1,1]=2/(t-b);m[2,2]=-2/(f-n);m[:3,3]=[-(r+l)/(r-l),-(t+b)/(t-b),-(f+n)/(f-n)];return m
def perspective(f,a,n,fa):
 t=1/math.tan(f/2);m=np.zeros((4,4));m[0,0]=t/a;m[1,1]=t;m[2,2]=(fa+n)/(n-fa);m[2,3]=2*fa*n/(n-fa);m[3,2]=-1;return m
target=np.array([.19,.94,0]);yaw=.36;pitch=.14;radius=3.9
eye=target+np.array([math.sin(yaw)*math.cos(pitch)*radius,math.sin(pitch)*radius,math.cos(yaw)*math.cos(pitch)*radius])
vp=perspective(math.pi/4.5,W/H,.02,30)@look(eye,target)
light=ortho(-2.8,2.8,-2.5,2.5,.1,10)@look(np.array([2.8,5.5,3.5]),np.array([0,.7,0]))
tex=generated('GenTextures');gl['BindTexture'](0x0DE1,tex);gl['TexImage2D'](0x0DE1,0,0x81A6,2048,2048,0,0x1902,0x1405,None)
for k,v in [(0x2801,0x2600),(0x2800,0x2600),(0x2802,0x812F),(0x2803,0x812F)]:gl['TexParameteri'](0x0DE1,k,v)
fb=generated('GenFramebuffers');gl['BindFramebuffer'](0x8D40,fb);gl['FramebufferTexture2D'](0x8D40,0x8D00,0x0DE1,tex,0);gl['DrawBuffers'](1,(U*1)(0));gl['ReadBuffer'](0);assert gl['CheckFramebufferStatus'](0x8D40)==0x8CD5
gl['Enable'](0x0B71);gl['Disable'](0x0B44);gl['Viewport'](0,0,2048,2048);gl['Clear'](0x0100);gl['UseProgram'](depth);m4(loc(depth,'uLight'),light);m4(loc(depth,'uModel'),np.eye(4))
for m in meshes:
 if m['alpha']<1:continue
 gl['BindVertexArray'](m['vao']);gl['DrawElements'](4,m['count'],0x1405,None)
gl['BindFramebuffer'](0x8D40,0);gl['Viewport'](0,0,W,H);gl['ClearColor'](.93,.96,.98,1);gl['Clear'](0x4000|0x0100);gl['UseProgram'](prog)
m4(uni['uVP'],vp);m4(uni['uLight'],light);m4(uni['uModel'],np.eye(4));fv(uni['uEye'],eye);gl['Uniform1f'](uni['uSelected'],0);gl['ActiveTexture'](0x84C0);gl['BindTexture'](0x0DE1,tex);gl['Uniform1i'](uni['uShadow'],0)
gl['Enable'](0x0BE2);gl['BlendFunc'](0x0302,0x0303)
def draw(m,isground=0):
 fv(uni['uColor'],m['color']+[m['alpha']]);gl['Uniform1f'](uni['uGround'],isground);gl['BindVertexArray'](m['vao']);gl['DrawElements'](4,m['count'],0x1405,None)
draw(ground,1)
for m in meshes:
 if m['alpha']==1:draw(m)
gl['DepthMask'](0)
for m in meshes:
 if m['alpha']<1:draw(m)
gl['DepthMask'](1);gl['Finish']();err=gl['GetError']();assert err==0,hex(err)
pixels=np.empty((H,W,4),np.uint8);gl['ReadPixels'](0,0,W,H,0x1908,0x1401,pixels.ctypes.data)
name='IGBT_Test_Cell_Cutaway.png' if CUT else 'IGBT_Test_Cell_Preview.png'
Image.fromarray(pixels[::-1,:,:3]).save(ROOT/'verification'/name)
print('Viewer shaders compile and render successfully;',name,flush=True)
