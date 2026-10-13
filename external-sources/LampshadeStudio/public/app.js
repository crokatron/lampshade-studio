import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';

const $=id=>document.getElementById(id);
const status=$('status');
const state={params:null,presets:null,styles:null,bulbs:null,nx:null,valid:false,version:0,busy:false,color:'#e9ded1',lit:false,previous:null,exportFormat:'step',stlQuality:'balanced'};
let pending,timer,model,box,bulbGroup;
const scene=new THREE.Scene();
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setClearColor(0x000000,0);
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.45;
$('viewer').append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(34,1,0.1,4000);
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;controls.dampingFactor=.08;controls.minDistance=90;controls.maxDistance=1600;
scene.add(new THREE.HemisphereLight(0xfff4e8,0x687990,2.5));
const key=new THREE.DirectionalLight(0xffecce,3.8);key.position.set(-200,340,220);scene.add(key);
const rim=new THREE.DirectionalLight(0xbdcee8,2);rim.position.set(250,150,-220);scene.add(rim);
const fill=new THREE.DirectionalLight(0xffdeb9,1.2);fill.position.set(0,120,360);scene.add(fill);
const grid=new THREE.GridHelper(500,25,0x59606e,0x464c57);grid.material.transparent=true;grid.material.opacity=.28;grid.position.y=-1;scene.add(grid);
const ground=new THREE.Mesh(new THREE.CircleGeometry(550,96),new THREE.MeshBasicMaterial({color:0x15191e,transparent:true,opacity:.08,depthWrite:false}));
ground.rotation.x=-Math.PI/2;ground.position.y=-1.1;scene.add(ground);

function resize(){const rect=$('viewer').getBoundingClientRect();renderer.setSize(rect.width,rect.height);camera.aspect=rect.width/rect.height;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe($('viewer'));
function frame(){requestAnimationFrame(frame);controls.update();renderer.render(scene,camera);}frame();

function setStatus(text,error=false){status.textContent=text;status.classList.toggle('error',error);}
const isNx=fmt=>['x_b','x_t'].includes(fmt);
const exportLabel=fmt=>isNx(fmt)?'Parasolid':fmt.toUpperCase();
function exportButtons(){const disabled=!state.valid||state.busy;$('export').disabled=disabled||(isNx(state.exportFormat)&&!state.nx?.available);$('exportBulb').disabled=disabled;$('exportFormat').disabled=state.busy;$('stlQuality').disabled=state.busy;}
function updateExport(){
  const fmt=state.exportFormat;
  $('exportFormat').value=fmt;$('stlQuality').value=state.stlQuality;$('stlQualityControl').hidden=fmt!=='stl';
  if(!state.busy)$('export').firstChild.textContent=`Export ${isNx(fmt)?'NX':exportLabel(fmt)} `;
  $('exportDetail').textContent=isNx(fmt)?`Parasolid ${fmt==='x_b'?'binary':'text'} · ${state.nx?.version||'requires NX'} · millimetres`:fmt==='stl'?`Binary STL · ${state.stlQuality} · import as millimetres` : fmt==='brep'?'OpenCascade BREP · CAD surfaces · millimetres':'STEP · CAD surfaces · millimetres';
  $('nxHint').hidden=!isNx(fmt);
  exportButtons();
}
function pendingFit(){if(state.params?.bulbVisible)$('bulbBadge').querySelector('b').textContent='Checking fit…';$('clearanceReport').textContent='Checking clearance…';}
function updateFields(){
  const p=state.params;
  for(const [k,v] of Object.entries(p)){if($(k)){if($(k).type==='checkbox')$(k).checked=v;else $(k).value=v;} const slider=document.querySelector(`[data-key="${k}"] input[type=range]`);if(slider)slider.value=v;}
  document.querySelectorAll('[data-style]').forEach(el=>{el.classList.toggle('selected',el.dataset.style===p.style);el.setAttribute('aria-pressed',el.dataset.style===p.style);});
  for(const [selector,visible] of [['.facet-only',p.texture==='facet'],['.woven-only',p.texture==='woven'],['.square-only',p.section==='square'],['.capsule-only',p.profile==='capsule'],['.bands-only',['lantern','helix'].includes(p.profile)]])document.querySelectorAll(selector).forEach(el=>el.hidden=!visible);
  $('textureNote').hidden=p.texture!=='woven';
  $('ribsLabel').textContent=p.texture==='facet'?'Facets around':p.texture==='woven'?'Weave around':'Ribs around';
  document.querySelector('[data-key="depth"]').hidden=p.texture==='smooth';
  document.querySelector('[data-key="ribs"]').hidden=p.texture==='smooth';
  const info=state.styles[p.style];
  $('modelTitle').textContent=info.name;
  $('currentStyleName').textContent=info.name;
  $('currentStyleDescription').textContent=info.description;
  $('undoVariation').disabled=!state.previous;
  $('wallControl').hidden=p.exportMode==='solid';
  $('exportHint').textContent=p.exportMode==='hollow'?'Open at both ends, ready for your mounting details. Wall is measured radially, not normal to the ribs.':'A filled outer volume for spiral vase slicing. Set wall width in the slicer; use zero bottom layers for open ends.';
  $('geometryLabel').textContent=p.exportMode==='hollow'?'Hollow CAD body · Z up':'Solid export · printed sleeve preview';
  $('bulbToggle').setAttribute('aria-pressed',p.bulbVisible);
  $('bulbSource').href=state.bulbs[p.bulbType].source;
  if(bulbGroup)bulbGroup.visible=p.bulbVisible;
  $('bulbBadge').hidden=!p.bulbVisible;
}
function dispose(obj){if(!obj)return;scene.remove(obj);obj.traverse(c=>{c.geometry?.dispose();if(c.material)for(const m of [].concat(c.material))m.dispose();});}
function makeGeometry(data,p,inside=true){
  const outer=data.positions;const positions=outer.slice();const indices=data.triangles.slice();
  if(inside){
    const count=positions.length/3;const n=data.bottom.length;const thickness=p.exportMode==='hollow'?p.wall:p.lineWidth;
    for(let i=0;i<count;i++){const x=outer[i*3],y=outer[i*3+1],z=outer[i*3+2];const r=Math.hypot(x,y);positions.push(x*(1-thickness/r),y*(1-thickness/r),z);}
    for(let i=0;i<data.triangles.length;i+=3)indices.push(data.triangles[i+2]+count,data.triangles[i+1]+count,data.triangles[i]+count);
    for(let i=0;i<n;i++){const j=(i+1)%n;indices.push(i,i+count,j,j,j+count,i+count);const a=count-n+i,b=count-n+j;indices.push(a,b,a+count,b,b+count,a+count);}
  }
  let geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setIndex(indices);geometry.computeVertexNormals();
  if(p.texture==='facet'){const original=geometry;geometry=geometry.toNonIndexed();original.dispose();geometry.computeVertexNormals();}
  return geometry;
}
function showModel(data,p){
  dispose(model);
  const geometry=makeGeometry(data,p);
  const material=new THREE.MeshStandardMaterial({color:state.color,roughness:.63,metalness:0,side:THREE.DoubleSide});
  model=new THREE.Mesh(geometry,material);model.rotation.x=-Math.PI/2;scene.add(model);setLighting();
  dispose(box);
  const edges=new THREE.EdgesGeometry(new THREE.BoxGeometry(p.boxWidth,p.height,p.boxDepth));
  box=new THREE.LineSegments(edges,new THREE.LineBasicMaterial({color:0xc6a47f,transparent:true,opacity:.27}));box.position.y=p.height/2;box.visible=$('boxToggle').getAttribute('aria-pressed')==='true';scene.add(box);
  controls.target.set(0,p.height*.48,0);
  $('bounds').innerHTML=`${p.boxWidth} × ${p.boxDepth} × ${p.height} <span>mm</span>`;
  updateExport();
  showBulb(data.bulb,p);
}
function showBulb(data,p){
  dispose(bulbGroup);bulbGroup=new THREE.Group();bulbGroup.visible=p.bulbVisible;
  const yAt=z=>p.bulbZ+(p.bulbOrientation==='pendant'?p.bulbHeight-z:z);
  const points=data.profile.map(([r,z])=>new THREE.Vector2(r,yAt(z)));
  const glass=new THREE.Mesh(new THREE.LatheGeometry(points,64),new THREE.MeshBasicMaterial({color:0xffd89d,transparent:true,opacity:.075,depthWrite:false,depthTest:false,side:THREE.DoubleSide}));glass.renderOrder=6;bulbGroup.add(glass);
  const lines=[];
  for(let j=0;j<8;j++){
    const angle=j*Math.PI/4;
    for(let i=1;i<data.profile.length;i++){
      const [a,z0]=data.profile[i-1],[b,z1]=data.profile[i];
      lines.push(a*Math.cos(angle),yAt(z0),a*Math.sin(angle),b*Math.cos(angle),yAt(z1),b*Math.sin(angle));
    }
  }
  for(const [r,z] of data.profile.filter((v,i)=>i%12===0||v[1]===25||v[1]===5)){
    for(let i=0;i<64;i++){const a=i*Math.PI/32,b=(i+1)*Math.PI/32;lines.push(r*Math.cos(a),yAt(z),r*Math.sin(a),r*Math.cos(b),yAt(z),r*Math.sin(b));}
  }
  const lineGeom=new THREE.BufferGeometry();lineGeom.setAttribute('position',new THREE.Float32BufferAttribute(lines,3));
  const wire=new THREE.LineSegments(lineGeom,new THREE.LineBasicMaterial({color:data.state==='collision'?0xff735f:0xffcd88,transparent:true,opacity:.85,depthTest:false,depthWrite:false}));wire.renderOrder=7;bulbGroup.add(wire);scene.add(bulbGroup);
  const fmt=n=>`${n>=0?'+':''}${n.toFixed(1)} mm`;
  const titles={clear:'Full-width envelope clears',check:'Check the actual bulb profile',collision:'Bulb profile intersects shade',outside:'Bulb is outside shade height'};
  const report=$('clearanceReport');report.dataset.state=data.state;report.replaceChildren();
  const title=document.createElement('b');title.textContent=titles[data.state];report.append(title);
  for(const text of [data.gap===null?'No overlapping height':`Approx. radial gap: ${fmt(data.gap)}`,data.envelopeGap===null?null:`Full-width envelope gap: ${fmt(data.envelopeGap)}`,`Target radial gap: ${p.bulbClearance} mm`,`Top opening: ${fmt(data.topOpeningGap)} · Bottom: ${fmt(data.bottomOpeningGap)}`,data.above>0?`Extends ${data.above} mm above the shade`:null,data.below>0?`Extends ${data.below} mm below the shade`:null]){if(text){const line=document.createElement('span');line.textContent=text;report.append(line);}}
  $('bulbBadge').dataset.state=data.state;$('bulbBadge').querySelector('span').textContent=`E27 · ${p.bulbType.toUpperCase()} · Ø${p.bulbDiameter}`;
  $('bulbBadge').querySelector('b').textContent=data.gap===null?'Outside shade':`${fmt(data.gap)} radial gap`;
  $('bulbBadge').hidden=!p.bulbVisible;applyXray();
}
function applyXray(){if(model){model.material.transparent=$('xrayShade').checked;model.material.opacity=$('xrayShade').checked?.24:1;model.material.depthWrite=!$('xrayShade').checked;model.material.needsUpdate=true;}}
function setLighting(){
  if(!model)return;
  model.material.color.set(state.color);model.material.emissive.set(state.lit?0xffb45c:0x000000);model.material.emissiveIntensity=state.lit?.5:0;
  key.intensity=state.lit?1.2:3.8;rim.intensity=state.lit?.6:2;fill.intensity=state.lit?.5:1.2;
  $('studioLight').classList.toggle('selected',!state.lit);$('glowLight').classList.toggle('selected',state.lit);
}
function setView(view='perspective'){
  const p=state.params;const s=Math.max(p.boxWidth,p.boxDepth,p.height);const y=p.height*.5;
  if(view==='top')camera.position.set(0,y+s*2.7,.001);
  else if(view==='front')camera.position.set(0,y,s*2.8);
  else camera.position.set(s*1.8,y+s*.95,s*2.2);
  controls.target.set(0,y,0);controls.update();
  document.querySelectorAll('[data-view]').forEach(el=>el.classList.toggle('selected',el.dataset.view===view));
}
async function preview(){
  clearTimeout(timer);const version=++state.version;const params={...state.params};pending?.abort();pending=new AbortController();state.valid=false;exportButtons();pendingFit();
  setStatus('Updating geometry…');
  try{
    const response=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(params),signal:pending.signal});
    const data=await response.json();if(version!==state.version)return;
    if(!response.ok)throw new Error(data.error||'Could not update the model.');
    showModel(data,params);state.valid=true;exportButtons();
    if(!state.busy)setStatus('Ready to export your shade');
  }catch(error){if(error.name==='AbortError')return;setStatus(error.message,true);}
}
function schedule(){clearTimeout(timer);state.version++;pending?.abort();state.valid=false;exportButtons();pendingFit();timer=setTimeout(preview,120);}
function remember(){state.previous={...state.params};}
function applyPreset(style,keepSize=true){
  remember();const preserved={exportMode:state.params.exportMode,wall:state.params.wall};
  for(const [key,value] of Object.entries(state.params))if(key.startsWith('bulb'))preserved[key]=value;
  if(keepSize)Object.assign(preserved,{boxWidth:state.params.boxWidth,boxDepth:state.params.boxDepth,height:state.params.height});
  state.params={...state.presets[style],...preserved};$('round').checked=state.params.boxWidth===state.params.boxDepth;updateFields();preview();setView();
}

const libraryOrder=['silk','lantern','orbit','woven','square','bloom','dune','hourglass','spiral','wave','facet'];
let thumbsStarted=false;
function makeLibrary(){
  for(const style of libraryOrder){
    const info=state.styles[style];const p=state.presets[style];
    const card=document.createElement('button');card.className='style-card';card.dataset.style=style;
    card.setAttribute('aria-label',`${info.name}: ${info.description}`);
    card.innerHTML=`<div class="thumb"><span class="thumb-loading">Preparing preview…</span><img alt="${info.name} shade preview" hidden><span class="style-group">${info.group}</span></div><div class="card-copy"><b>${info.name}</b><span>${info.description}</span><small>${p.boxWidth} × ${p.boxDepth} × ${p.height} mm</small></div>`;
    card.addEventListener('click',()=>{applyPreset(style,$('keepEnvelope').checked);$('libraryDialog').close();});
    $('libraryGrid').append(card);
  }
}
async function renderThumbnails(){
  if(thumbsStarted)return;thumbsStarted=true;
  const thumbRenderer=new THREE.WebGLRenderer({antialias:true,alpha:true,preserveDrawingBuffer:true});
  thumbRenderer.setSize(320,250);thumbRenderer.setPixelRatio(1);thumbRenderer.toneMapping=THREE.ACESFilmicToneMapping;thumbRenderer.toneMappingExposure=1.15;
  const thumbScene=new THREE.Scene();thumbScene.add(new THREE.HemisphereLight(0xfff1dc,0x525e72,2));
  const light=new THREE.DirectionalLight(0xffdfba,3);light.position.set(-140,260,200);thumbScene.add(light);
  const edgeLight=new THREE.DirectionalLight(0xb3c4df,1.3);edgeLight.position.set(160,140,-80);thumbScene.add(edgeLight);
  const cam=new THREE.PerspectiveCamera(32,320/250,1,3000);
  for(const style of libraryOrder){
    const card=$('libraryGrid').querySelector(`[data-style="${style}"]`);
    try{
      const response=await fetch(`/api/thumbnail/${style}`);if(!response.ok)throw new Error('Preview unavailable');const data=await response.json();
      const p=state.presets[style];const geo=makeGeometry(data,p,false);const mat=new THREE.MeshStandardMaterial({color:style==='orbit'||style==='lantern'?0xd5a776:0xe6d6bd,roughness:.67,side:THREE.DoubleSide});
      const obj=new THREE.Mesh(geo,mat);obj.rotation.x=-Math.PI/2;thumbScene.add(obj);
      const s=Math.max(p.height,p.boxWidth,p.boxDepth);cam.position.set(s*1.4,p.height*.5+s*.65,s*2.1);cam.lookAt(0,p.height*.49,0);
      thumbRenderer.render(thumbScene,cam);const img=card.querySelector('img');img.src=thumbRenderer.domElement.toDataURL('image/png');img.hidden=false;card.querySelector('.thumb-loading').remove();
      thumbScene.remove(obj);geo.dispose();mat.dispose();
      await new Promise(resolve=>requestAnimationFrame(resolve));
    }catch(error){card.querySelector('.thumb-loading').textContent='Select to preview';}
  }
  thumbRenderer.dispose();
}
$('browseStyles').addEventListener('click',()=>{$('libraryDialog').showModal();renderThumbnails();});
$('closeLibrary').addEventListener('click',()=>$('libraryDialog').close());
$('vary').addEventListener('click',()=>{
  remember();const p={...state.params};const base=state.presets[p.style];const between=(a,b)=>a+(b-a)*Math.random();
  p.twist=Math.round(Math.max(-160,Math.min(160,p.twist+between(-22,22))));
  p.depth=+(Math.max(.4,Math.min(7,base.depth*between(.7,1.4)))).toFixed(1);
  p.bulge=Math.round(Math.max(-30,Math.min(48,base.bulge+between(-6,6))));
  p.top=Math.round(base.top*between(.88,1.12));p.bottom=Math.round(base.bottom*between(.88,1.12));
  if(p.texture==='woven')p.weaveRows=Math.max(8,Math.min(30,base.weaveRows+Math.round(between(-4,4))));
  else if(p.texture==='ribs')p.ribs=Math.max(12,Math.min(80,base.ribs+Math.round(between(-6,6))));
  if(['lantern','helix'].includes(p.profile)){p.bands=Math.round(between(3,6));p.bandDepth=+between(7,13).toFixed(1);}
  if(base.sway>0)p.sway=Math.round(Math.min(32,base.sway*between(.7,1.2)));
  state.params=p;updateFields();preview();
});
$('undoVariation').addEventListener('click',()=>{if(!state.previous)return;state.params=state.previous;state.previous=null;$('round').checked=state.params.boxWidth===state.params.boxDepth;updateFields();preview();setView();});

document.querySelectorAll('.control').forEach(control=>{
  const k=control.dataset.key;control.querySelectorAll('input').forEach(input=>input.addEventListener('input',()=>{
    const value=Number(input.value);state.params[k]=value;
    control.querySelectorAll('input').forEach(other=>{if(other!==input)other.value=value;});schedule();
  }));
});
for(const key of ['boxWidth','boxDepth','height'])$(key).addEventListener('input',()=>{
  state.params[key]=Number($(key).value);
  if($('round').checked&&key!=='height'){const other=key==='boxWidth'?'boxDepth':'boxWidth';state.params[other]=state.params[key];$(other).value=state.params[key];}schedule();
});
$('round').addEventListener('change',()=>{if($('round').checked){state.params.boxDepth=state.params.boxWidth;$('boxDepth').value=state.params.boxDepth;schedule();}});
$('exportMode').addEventListener('change',()=>{state.params.exportMode=$('exportMode').value;updateFields();preview();});
for(const field of ['exportFormat','stlQuality'])$(field).addEventListener('change',()=>{state[field]=$(field).value;updateExport();if(state.valid)setStatus(state.exportFormat==='stl'&&state.params.exportMode==='hollow'?'For vase mode, choose Solid envelope in step 04.':'Ready to export your shade');});
for(const field of ['texture','profile','section'])$(field).addEventListener('change',()=>{state.params[field]=$(field).value;updateFields();preview();});
for(const field of ['bulbDiameter','bulbHeight'])$(field).addEventListener('input',()=>{state.params[field]=Number($(field).value);schedule();});
$('bulbType').addEventListener('change',()=>{const type=$('bulbType').value;state.params.bulbType=type;state.params.bulbDiameter=state.bulbs[type].diameter;state.params.bulbHeight=state.bulbs[type].height;updateFields();preview();});
$('bulbOrientation').addEventListener('change',()=>{state.params.bulbOrientation=$('bulbOrientation').value;preview();});
$('bulbVisible').addEventListener('change',()=>{state.params.bulbVisible=$('bulbVisible').checked;updateFields();});
$('bulbToggle').addEventListener('click',()=>{state.params.bulbVisible=!state.params.bulbVisible;updateFields();});
$('xrayShade').addEventListener('change',applyXray);
$('bulbBadge').addEventListener('click',()=>$('bulbSection').scrollIntoView({behavior:'smooth',block:'start'}));
$('reset').addEventListener('click',()=>applyPreset(state.params.style));
document.querySelectorAll('[data-view]').forEach(el=>el.addEventListener('click',()=>setView(el.dataset.view)));
$('boxToggle').addEventListener('click',()=>{const show=$('boxToggle').getAttribute('aria-pressed')!=='true';$('boxToggle').setAttribute('aria-pressed',show);if(box)box.visible=show;});
document.querySelectorAll('[data-color]').forEach(el=>el.addEventListener('click',()=>{state.color=el.dataset.color;document.querySelectorAll('[data-color]').forEach(b=>b.classList.toggle('selected',b===el));setLighting();}));
$('studioLight').addEventListener('click',()=>{state.lit=false;setLighting();});$('glowLight').addEventListener('click',()=>{state.lit=true;setLighting();});
$('help').addEventListener('click',()=>$('helpDialog').showModal());$('closeHelp').addEventListener('click',()=>$('helpDialog').close());
function download(blob,name){const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000);}
$('save').addEventListener('click',()=>download(new Blob([JSON.stringify({app:'lampshade-studio',version:2,parameters:state.params,exportOptions:{exportFormat:state.exportFormat,stlQuality:state.stlQuality}},null,2)],{type:'application/json'}),`lampshade-${state.params.style}.json`));
$('load').addEventListener('click',()=>$('designFile').click());
$('designFile').addEventListener('change',async()=>{
  const file=$('designFile').files[0];if(!file)return;
  try{if(file.size>16000)throw new Error('This design file is too large.');const saved=JSON.parse(await file.text());if(saved.app!=='lampshade-studio'||![1,2].includes(saved.version)||!saved.parameters)throw new Error('Choose a Lampshade Studio design file.');
    const response=await fetch('/api/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(saved.parameters)});const data=await response.json();if(!response.ok)throw new Error(data.error);
    state.params={...state.presets[saved.parameters.style||'spiral'],...saved.parameters};
    if(['step','stl','brep','x_b','x_t'].includes(saved.exportOptions?.exportFormat))state.exportFormat=saved.exportOptions.exportFormat;
    if(['lite','balanced','fine'].includes(saved.exportOptions?.stlQuality))state.stlQuality=saved.exportOptions.stlQuality;
    state.previous=null;$('round').checked=state.params.boxWidth===state.params.boxDepth;updateFields();updateExport();await preview();setView();
  }catch(error){setStatus(error.message,true);}finally{$('designFile').value='';}
});
$('export').addEventListener('click',async()=>{
  if(!state.valid||state.busy)return;
  const fmt=state.exportFormat;const params={...state.params,exportFormat:fmt,stlQuality:state.stlQuality};
  state.busy=true;exportButtons();$('export').firstChild.textContent=`Building ${isNx(fmt)?'NX':exportLabel(fmt)}… `;
  setStatus(isNx(fmt)?'Converting and checking the body in NX…':fmt==='stl'?'Building and checking the print mesh…':'Building and checking the CAD body…');
  try{const response=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(params)});if(!response.ok){const data=await response.json();throw new Error(data.error||'Export failed.');}
    const blob=await response.blob();const quality=fmt==='stl'?`-${params.stlQuality}`:'';download(blob,`lampshade-${params.style}-${params.boxWidth}x${params.boxDepth}x${params.height}-${params.exportMode}${quality}.${fmt}`);
    const triangles=Number(response.headers.get('X-Mesh-Triangles'));
    setStatus(`${exportLabel(fmt)} exported · ${(blob.size/1000000).toFixed(1)} MB${fmt==='stl'?` · ${Math.round(triangles/1000)}k triangles`:isNx(fmt)?' · NX verified':' · body verified'}`);
  }catch(error){setStatus(error.message,true);}finally{state.busy=false;exportButtons();updateExport();}
});
$('exportBulb').addEventListener('click',async()=>{
  if(!state.valid||state.busy)return;state.busy=true;exportButtons();
  const p={...state.params};setStatus('Building the bulb reference…');
  try{const response=await fetch('/api/bulb-export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});if(!response.ok){const data=await response.json();throw new Error(data.error||'Bulb export failed.');}download(await response.blob(),`bulb-reference-e27-${p.bulbType}-${p.bulbDiameter}x${p.bulbHeight}.step`);setStatus('Bulb reference STEP exported');}
  catch(error){setStatus(error.message,true);}finally{state.busy=false;exportButtons();}
});

try{const response=await fetch('/api/config');if(!response.ok)throw new Error('Could not connect to the local design engine.');const config=await response.json();state.presets=config.presets;state.styles=config.styles;state.bulbs=config.bulbs;state.nx=config.nx;for(const option of $('exportFormat').options)if(isNx(option.value))option.disabled=!state.nx?.available;state.params={...config.presets.spiral};makeLibrary();updateFields();updateExport();setView();await preview();}catch(error){setStatus(error.message,true);}
