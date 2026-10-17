'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..'),base=process.argv[2];
if(!base)throw new Error('Use python verification/run_ui_checks.py');
const elements={},frames=[],labFrames=[],stationFrames=[];
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.listeners={};this.attrs={};this.style={};this.dataset={};this.textContent='';this.value='';this.disabled=false;this._id='';}
 set id(value){this._id=value;elements[value]=this;}get id(){return this._id;}
 set innerHTML(value){this.html=value;for(const m of value.matchAll(/id="([^"]+)"/g)){let e=new Element();e.id=m[1];}}
 append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
 addEventListener(type,fn){this.listeners[type]=fn;}setAttribute(key,value){this.attrs[key]=value;}
 getBoundingClientRect(){return {left:0,top:0,width:560,height:205};}click(){this.onclick?.();this.listeners.click?.();}
}
const html=fs.readFileSync(root+'/static/index.html','utf8');
for(const m of html.matchAll(/id="([^"]+)"/g)){let e=new Element();e.id=m[1];}
elements.zoom.value='full';elements.mode.value='full';elements.serial.value='UI-VERIFICATION';elements.operator.value='Harness';
let lastView,revealed=false,failure=false;
elements.model.contentWindow={__modelViewer:{state:{},setLabFrame:f=>labFrames.push(f),setStationState:f=>stationFrames.push(f),setView:v=>lastView=v,setReveal:v=>revealed=v}};
const context={console,document:{getElementById:id=>elements[id],createElement:tag=>new Element(tag)},window:{open(){}},requestAnimationFrame:f=>frames.push(f),setTimeout,Blob,URL,fetch:async(url,options)=>{if(failure)throw new Error('Connection interrupted');return fetch(base+url,options);}};
vm.createContext(context);
(async()=>{
 await vm.runInContext(fs.readFileSync(root+'/static/app.js','utf8'),context);
 for(let i=0;i<100&&elements.connection.textContent!=='Local solver ready';i++)await new Promise(r=>setTimeout(r,10));
 assert.equal(elements.connection.textContent,'Local solver ready');const app=context.window.__virtualLab;
 await app.simulate();assert.equal(elements['verdict-title'].textContent,'VIRTUAL SUITE PASS',elements['verdict-detail'].textContent);
 assert.equal(app.report.counts.PASS,10);assert.equal(app.report.hardware_release,false);assert.equal(elements.coverage.children.length,10);
 assert.equal(elements['json-export'].disabled,false);assert(elements['scope-2'].html.includes('polyline'));
 app.setCursor(76);assert(labFrames.at(-1).ic>50);assert(elements['live-current'].textContent.includes('A'));
 elements.zoom.value='off';elements.zoom.onchange();assert(elements.time.min>76);
 elements.play.onclick();assert(frames.length);frames.shift()(0);frames.shift()(6500);assert.equal(elements.play.textContent,'▶ Replay');
 app.chooseTrace('upper_protection');assert.equal(app.trace.kind,'circuit');app.setCursor(5.5);assert(elements.phase.textContent.startsWith('UPPER'));
 app.chooseTrace('lower_switching_shutdown');app.setCursor(2);assert(elements['time-label'].textContent.endsWith(' s'));assert(elements.phase.textContent.includes('stored'));assert(elements.zoom.disabled);
 app.chooseTrace('insulation');assert.equal(app.trace.channels.length,2);app.chooseTrace('driver');assert.equal(app.trace.channels.length,1);
 elements['view-dut'].click();assert.equal(lastView,'fixture');elements.reveal.click();assert(revealed);
 elements['p-ins_mohm'].value=.1;elements['p-ins_mohm'].listeners.input();assert(app.dirty);assert.equal(elements['verdict-title'].textContent,'INPUTS CHANGED');
 await app.simulate();assert.equal(elements['verdict-title'].textContent,'VIRTUAL SUITE FAIL');assert.equal(app.report.waveforms.length,0);
 elements.reset.click();elements.mode.value='static';await app.simulate();assert.equal(elements['verdict-title'].textContent,'VIRTUAL SUITE INCOMPLETE');
 elements['s-door_closed'].checked=false;elements['s-door_closed'].listeners.change();assert.equal(stationFrames.at(-1).doorClosed,false);
 await app.simulate();assert.equal(elements['verdict-title'].textContent,'VIRTUAL SUITE ABORTED');assert.equal(app.report.waveforms.length,0);
 elements.reset.click();const pending=app.simulate();for(let i=0;i<100&&!app.activeJob;i++)await new Promise(r=>setTimeout(r,5));await elements.stop.onclick();await pending;assert.equal(app.report.virtual_suite_verdict,'ABORTED');
 failure=true;await app.simulate();assert.equal(elements['verdict-title'].textContent,'NO VALID RESULT');assert.equal(app.report,null);assert.equal(elements['json-export'].disabled,true);assert.equal(elements['live-current'].textContent,'—');
 console.log(JSON.stringify({result:'PASS',checks:['real HTTP configuration and full calculation','ten mandatory groups rendered','hardware qualification remains false','waveform extrema and cursor-to-3D binding','edge zoom and six-second replay','upper protection and discharge selections','seconds versus microseconds','driver and insulation traces','camera and reveal bindings','changed inputs marked stale','insulation failure inhibits pulses','partial suite is incomplete','door state binds to interlock and 3D','active job stop returns aborted','network failure clears prior result'],limitation:'DOM and actual local network integration; not a graphical browser session.'},null,2));
})().catch(e=>{console.error(e);process.exit(1);});
