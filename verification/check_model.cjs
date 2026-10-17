const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path').resolve(__dirname,'../static/model.html');
const html=fs.readFileSync(path,'utf8');
const json=html.match(/<script id="modelData" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const frames=[],elements={},views=[];let draws=0,serial=0,shaderSources=[];
const constants={VERTEX_SHADER:35633,FRAGMENT_SHADER:35632,COMPILE_STATUS:35713,LINK_STATUS:35714,ARRAY_BUFFER:34962,ELEMENT_ARRAY_BUFFER:34963,STATIC_DRAW:35044,FLOAT:5126,UNSIGNED_INT:5125,TRIANGLES:4,LINES:1,FRAMEBUFFER_COMPLETE:36053};
const gl=new Proxy(constants,{get:(target,key)=>{
 if(key in target)return target[key];if(key.startsWith('create'))return ()=>({id:++serial});
 if(key==='getShaderParameter'||key==='getProgramParameter')return ()=>true;
 if(key==='checkFramebufferStatus')return ()=>36053;if(key==='getError')return ()=>0;
 if(key==='getUniformLocation')return (p,n)=>({p,n});
 if(key==='shaderSource')return(s,src)=>shaderSources.push(src);
 if(key==='uniformMatrix4fv')return(loc,trans,m)=>assert([...m].every(Number.isFinite),'Matrix contains non-finite values');
 if(key==='drawElements')return(mode,count)=>{assert(count>0);draws++;};
 if(key.toUpperCase()===key){target[key]=++serial;return target[key];}
 return ()=>{};
}});
class Element{
 constructor(id=''){this.id=id;this.listeners={};this.attrs={};this.value='0';this.checked=true;this.textContent='';this.children=[];this.classSet=new Set();this.classList={add:x=>this.classSet.add(x),remove:x=>this.classSet.delete(x),toggle:(x,v)=>{if(v??!this.classSet.has(x))this.classSet.add(x);else this.classSet.delete(x);}};}
 addEventListener(e,f){this.listeners[e]=f;}
 setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k]??null;}
 append(e){this.children.push(e);}click(){if(this.onclick)this.onclick();if(this.listeners.click)this.listeners.click({target:this});}
 set innerHTML(h){this._html=h;let match=h.match(/id="([^"]+)"/);if(match){this.input=new Element(match[1]);elements[match[1]]=this.input;}}
 querySelector(){return this.input;}
 getBoundingClientRect(){return {left:0,top:0,width:this.clientWidth,height:this.clientHeight};}
 setPointerCapture(){}
}
for(const id of ['canvas','modelData','loading','viewName','viewAxis','meshCount','openDoor','cutaway','showDims','dimensionOverlay','cutawayPill','explode','explodeValue','parts','selection','selectedGroup','selectedName','selectedDetail','clearSelection','reset','downloadGlb'])elements[id]=new Element(id);
elements.modelData.textContent=json;Object.assign(elements.canvas,{clientWidth:1188,clientHeight:914,getContext:()=>gl});
for(const name of ['iso','front','side','top','fixture']){let e=new Element();e.dataset={view:name};views.push(e);}
const context={console,Float32Array,Uint32Array,Uint8Array,Map,Set,JSON,Math,Number,Array,Object,Infinity,Error,Blob,URL,atob,devicePixelRatio:1,setTimeout,document:{getElementById:id=>elements[id],querySelectorAll:()=>views,createElement:()=>new Element()},requestAnimationFrame:f=>frames.push(f),ResizeObserver:class{constructor(f){this.f=f;}observe(){this.f();}},window:{}};
vm.createContext(context);vm.runInContext(code,context,{timeout:10000});
let time=0;function tick(n=1){for(let i=0;i<n;i++){let f=frames.shift();f(time+=16.67);}}
tick();const viewer=context.window.__modelViewer;assert(viewer.visibleCount===608);assert(viewer.drawCount===608);assert(shaderSources.length===4);
elements.openDoor.click();tick(80);assert(viewer.state.door>.99);
elements.cutaway.click();tick();assert(viewer.visibleCount<608);const cutCount=viewer.visibleCount;
elements.explode.value='65';elements.explode.listeners.input({target:elements.explode});tick();assert(viewer.state.explode===.65);
elements['group-rack'].checked=false;elements['group-rack'].listeners.change({target:elements['group-rack']});tick();assert(viewer.visibleCount<cutCount);
elements.showDims.click();assert(elements.dimensionOverlay.classSet.has('visible'));
elements.reset.click();tick();assert(viewer.state.explode===0&&viewer.state.door===0&&viewer.visibleCount===608);
for(const name of ['front','side','top','fixture','iso']){viewer.setView(name);tick();assert(viewer.state.view===name);}
elements.reset.click();viewer.setView('front');tick();
const point=viewer.project([-.37,1.28,.15]);
elements.canvas.listeners.pointerdown({pointerId:1,clientX:point[0],clientY:point[1],button:0,shiftKey:false});
elements.canvas.listeners.pointerup({pointerId:1,clientX:point[0],clientY:point[1]});tick();
assert(viewer.state.selected>=0,'Ray selection failed');
assert(elements.selectedGroup.textContent==='IGBT assembly','Wrong group selected: '+elements.selectedGroup.textContent);
let before=viewer.state.radius;elements.canvas.listeners.wheel({preventDefault(){},deltaY:-100});tick();assert(viewer.state.radius<before);
let yaw=viewer.state.yaw;elements.canvas.listeners.pointerdown({pointerId:2,clientX:600,clientY:300,button:0,shiftKey:false});elements.canvas.listeners.pointermove({pointerId:2,clientX:670,clientY:330,shiftKey:false});elements.canvas.listeners.pointerup({pointerId:2,clientX:670,clientY:330});tick();assert(viewer.state.yaw!==yaw);
elements.reset.click();tick();
console.log(JSON.stringify({result:'PASS',parts:608,cutawayVisible:cutCount,drawCalls:draws,checks:['initial render command stream','finite camera and model matrices','door animation','cutaway','explode','group visibility','dimension toggle','reset','all camera presets','ray-triangle component selection','zoom','orbit'],limitation:'DOM and WebGL command harness; no installed browser binary for an end-to-end browser render.'},null,2));

viewer.setLabFrame({ic:60,id:0,status:'MODEL PASS'});tick();assert(viewer.DATA.meshes.find(m=>m.id===601).color[1]>.8);viewer.setLabFrame({ic:0,id:60,status:'MODEL FAIL'});tick();assert(viewer.DATA.meshes.find(m=>m.id===605).color[0]>.9);viewer.setReveal(true);tick();assert(viewer.visibleCount<608);console.log('Simulation frame colour and cutaway bindings: PASS');

viewer.setStationState({doorClosed:false,clamped:true,estopReleased:true});tick(80);assert(viewer.state.door>.99);viewer.setStationState({doorClosed:true,clamped:true,estopReleased:true});tick(80);assert(viewer.state.door<.01);viewer.setLabFrame({ic:30,id:0,status:"PASS"});tick();assert(viewer.DATA.meshes.find(m=>m.id===601).color[1]>.8);console.log("Final-suite status and station-door bindings: PASS");
