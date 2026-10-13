import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {renderNavigator} from './chandelier-navigator.js';
import {createDesignStore} from './chandelier-store.js';

const $=id=>document.getElementById(id);
const api=new URL('api/chandelier',location.href);
const nas=location.pathname.startsWith('/lampshade/');
const store=nas?createDesignStore(fetch.bind(window),new URL('../api/designs/lampshade',location.href).pathname):null;
const descriptions={sunburst:'Spokes of light around an open centre. Add staggered tiers for a branching silhouette.',halo:'A polygon of light. Three bars make a triangle; add more to draw a luminous halo.',parallel:'A quiet, linear canopy. Good for a long table or a row of plants.',spiral:'One continuous descent around the centre, with a different height for every light.',lantern:'Upright bars make an open lantern, with the light faces pointing towards the centre.'};
const drawings={sunburst:'M33 23L33 3M27 27L8 39M39 27L58 39',halo:'M33 3L7 42L59 42Z',parallel:'M10 9H56M10 24H56M10 39H56',spiral:'M20 5L50 12M8 20L37 27M28 32L58 39',lantern:'M13 9V39M33 3V43M53 9V39'};
const titles={sunburst:'Points of light.',halo:'Draw a luminous circle.',parallel:'A canopy of light.',spiral:'Let the light descend.',lantern:'An open lantern.'};
let params,defaults,model,pending,timer,requestId=0,busy=false,valid=false,dirty=false,group,guideGroup,plugGroup,lastFit=false,currentView='perspective',nxAvailable=false;
const componentObjects=new Map();let selectionBoxes=[];
const scene=new THREE.Scene();
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setClearColor(0,0);renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;
$('viewer').append(renderer.domElement);
const camera=new THREE.PerspectiveCamera(38,1,1,30000);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=50;controls.maxDistance=15000;
scene.add(new THREE.HemisphereLight(0xf1ffe6,0x455742,2.8));
const key=new THREE.DirectionalLight(0xfff0d2,3);key.position.set(700,900,500);scene.add(key);
const fill=new THREE.DirectionalLight(0xd7edff,2);fill.position.set(-600,200,-600);scene.add(fill);
const grid=new THREE.GridHelper(4000,40,0x667764,0x536550);grid.material.transparent=true;grid.material.opacity=.16;grid.position.y=-5;scene.add(grid);
function resize(){const {width,height}=$('viewer').getBoundingClientRect();renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe($('viewer'));
renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function savePayload(){return {app:'grow-light-chandelier',version:1,parameters:{...params},exportOptions:{format:$('format').value,scope:$('scope').value}};}
function download(data,name,type){const blob=data instanceof Blob?data:new Blob([data],{type});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),60000);}
function buttons(){
  const blocked=!valid||busy||(!['single','strap','hub','arm','web','web-collar','collector'].includes($('scope').value)&&(!!model?.clashes.length||!!model?.mountClashes.length));
  $('exportBom').disabled=!valid||busy;$('exportTree').disabled=!valid;
  $('export').disabled=blocked;$('saveNas').disabled=!valid||busy;
  $('export').textContent=busy?'Building…':`Export ${$('format').value.toUpperCase()} ↗`;
  $('exportNote').textContent=({collector:'One printed cord junction',web:'One printed connector','web-collar':'One web retaining collar',hub:'Printed centre hub',arm:'One spoke, flat',parts:'Printed components',strap:'Longest webbing strap, flat',single:'One retaining collar',saddles:'Retaining collars'}[$('scope').value]||`Full CAD assembly · ${model?.assemblySummary?.modeledComponents??'—'} components`)+' · mm';
}
function sync(){
  for(const [k,v] of Object.entries(params)){if($(k)){if(typeof v==='boolean')$(k).checked=v;else $(k).value=v;}}
  $('scope').querySelector('[value="strap"]').disabled=params.hanging!=='webbing'||!params.printedWebbing;
  if(params.hanging!=='webbing'&&$('scope').value==='strap')$('scope').value='assembly';
  for(const scope of ['hub','arm'])$('scope').querySelector(`[value="${scope}"]`).disabled=params.support!=='hub';
  $('scope').querySelector('[value="arm"]').disabled=params.support!=='hub'||params.spokeType!=='printed';
  if(params.support!=='hub'&&['hub','arm'].includes($('scope').value))$('scope').value='assembly';
  if(params.spokeType==='t5'&&$('scope').value==='arm')$('scope').value='assembly';
  document.querySelectorAll('[data-count]').forEach(b=>b.classList.toggle('active',Number(b.dataset.count)===params.count));
  document.querySelectorAll('[data-layout]').forEach(b=>{b.classList.toggle('active',b.dataset.layout===params.layout);b.setAttribute('aria-pressed',String(b.dataset.layout===params.layout));});
  document.querySelectorAll('[data-layouts]').forEach(e=>e.hidden=!e.dataset.layouts.split(' ').includes(params.layout));
  document.querySelectorAll('[data-tier]').forEach(e=>e.hidden=params.tiers<=1||params.layout==='spiral');
  document.querySelectorAll('[data-hanging]').forEach(e=>e.hidden=e.dataset.hanging!==params.hanging);
  document.querySelectorAll('[data-flexible]').forEach(e=>e.hidden=params.support==='hub'||(e.dataset.layouts&&!e.dataset.layouts.split(' ').includes(params.layout)));
  $('hubSettings').hidden=params.support!=='hub';
  const webAllowed=params.support==='hub'&&params.spokeType==='t5';
  $('webSection').hidden=!webAllowed;$('webSettings').hidden=!params.webEnabled;
  $('hangerSettings').hidden=!webAllowed||!params.webEnabled;
  $('keepHubLabel').hidden=params.hangerFrom!=='web';
  const included=params.support==='hub'&&(params.hangerFrom!=='web'||params.keepHub);
  $('scope').querySelector('[value="hub"]').disabled=!included;
  $('scope').querySelector('[value="single"]').disabled=params.support==='hub'&&!included;
  for(const scope of ['web','web-collar'])$('scope').querySelector(`[value="${scope}"]`).disabled=!params.webEnabled;
  const integrated=params.webConstruction==='integrated';
  $('scope').querySelector('[value="web-collar"]').disabled=!params.webEnabled||integrated;
  $('scope').querySelector('[value="saddles"]').disabled=!included&&params.support==='hub'&&integrated;
  const hasCollector=params.webEnabled&&params.hangerFrom==='web'&&params.hanging==='paracord';
  $('collectorSettings').hidden=!hasCollector;
  $('scope').querySelector('[value="collector"]').disabled=!hasCollector||!params.cordCollector;
  document.querySelectorAll('[data-integrated]').forEach(e=>e.hidden=!integrated);
  document.querySelectorAll('[data-bolted]').forEach(e=>e.hidden=integrated);
  $('connectorNote').textContent=integrated?'One identical printed connector per gap, patterned around the lights. Its integral clips are offset along each T5 so neighbouring copies fit. Print broad face down, openings up. Verify clip fit, flex and retention on the actual housing.':'One identical flat panel per gap, bolted to separate collars along the T5. Neighbouring panels share collars.';
  if($('scope').selectedOptions[0]?.disabled)$('scope').value='assembly';
  document.querySelectorAll('[data-direct]').forEach(e=>e.hidden=params.spokeType!=='t5');
  document.querySelectorAll('[data-printed-arm]').forEach(e=>e.hidden=params.spokeType!=='printed');
  $('radius').closest('.field').hidden=params.layout==='parallel'||(params.support==='hub'&&params.spokeType==='t5');
  $('supportNote').textContent=params.hangerFrom==='web'?(params.keepHub?'Web eyelets carry the paracord; the centre hub keeps the spoke roots together.':'Open centre: repeated printed connectors clip neighbouring T5 lights together and carry the paracord.') : params.support==='hub'?(params.spokeType==='t5'?'The T5s are the spokes. Their inner ends attach beneath one printed hub, with one central hanger.':'One hanger, on the printed hub. Bolted carrier spokes keep the bars apart.'):'Layout study only: angled slings pull the bars inward. Add a rigid spreader in CAD, or choose the printed centre hub.';
  $('hubDesignNote').textContent=params.spokeType==='t5'?'Two collars hold each T5’s inner end beneath the hub. Set the engagement length and refine the supplied-clip fixings in CAD. The light housings and root joints have not been load-tested.':'Spokes bolt beneath the hub and onto both saddles. One centred hanger carries the assembly. Fasteners and T5 clips are separate hardware; these supports have not been load-tested.';
  $('layoutDescription').textContent=params.support==='hub'?(params.spokeType==='t5'?'The lights form the spokes. Curved webs and an optional centre hub connect them.':'Radial carrier spokes hold the lights around a printed centre hub.'):descriptions[params.layout];$('suspensionLabel').replaceChildren(document.createTextNode(params.support==='hub'?'Rise above hub plane':'Space above lights'),Object.assign(document.createElement('span'),{textContent:'mm'}));buttons();
}
function autoSpace(){
  const p=params,n=Math.ceil(p.count/p.tiers),t=p.saddleWall;
  const opening=p.hanging==='paracord'?p.cordDiameter+.8:p.webbingThickness+1;
  const width=p.width+2*p.clearance+6*t+2*opening;
  const pad=20+p.endSpace;
  if(p.layout==='sunburst')p.radius=Math.ceil((p.length/2+pad)+width/(2*Math.tan(Math.PI/n)));
  else if(p.layout==='lantern')p.radius=Math.ceil(Math.max(90,(width+20)/(2*Math.sin(Math.PI/n))));
  else p.radius=Math.ceil(Math.max(100,(p.length+2*pad)/(2*Math.tan(Math.PI/n))+width/2));
  p.spacing=Math.ceil(width+35);
  const vertical=p.layout==='lantern'?p.length:p.height+2*t+p.clearance+p.length*Math.abs(Math.sin(p.tilt*Math.PI/180));
  p.tierGap=Math.max(p.tierGap,Math.ceil(vertical+40));
  p.radius=Math.min(2000,p.radius);
  if(p.support==='hub'){
    if(p.spokeType==='t5'){
      const min=p.engagement-p.saddleLength/2+(p.width+2*p.clearance+2*p.saddleWall+3)/(2*Math.sin(Math.PI/p.count));
      p.hubRadius=Math.max(p.hubRadius,Math.ceil(min),Math.ceil(p.engagement+p.endSpace+p.width/(2*Math.tan(Math.PI/p.count))));
      if(p.webEnabled&&p.webConstruction==='bolted'){const half=Math.PI/p.count,earY=p.width/2+p.clearance+3*p.saddleWall+p.webHole/2;
        p.hubRadius=Math.max(p.hubRadius,Math.ceil((p.webHole/2+4+p.webRib+earY*Math.cos(half))/Math.sin(half)-p.webReach));}
      if(p.webEnabled&&p.webConstruction==='integrated'){
        const half=Math.PI/p.count,offset=p.width/2+p.clearance+p.saddleWall-2;
        p.webReach=Math.max(p.webReach,p.bridgeClipLength+4);
        p.hubRadius=Math.max(p.hubRadius,Math.ceil(((12+p.bridgeBandWidth)/.9+offset*Math.cos(half))/Math.sin(half)-p.webReach));
      }
      p.radius=p.hubRadius-p.engagement+p.length/2;
    }else{p.hubRadius=Math.max(p.hubRadius,Math.ceil(38+(p.armWidth+3)/(2*Math.sin(Math.PI/p.count))));p.radius=Math.max(p.radius,Math.ceil(p.hubRadius+5+p.length*.32+p.saddleLength/2));}
  }
}
function queue(){dirty=true;valid=false;buttons();clearTimeout(timer);pending?.abort();requestId++;status('Updating arrangement…');timer=setTimeout(preview,140);}
async function preview(){
  const id=++requestId;pending?.abort();pending=new AbortController();
  try{
    const r=await fetch(api+'/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(params),signal:pending.signal});
    const data=await r.json();if(id!==requestId)return;if(!r.ok)throw Error(data.error||'Could not build this arrangement.');
    params=data.parameters;model=data;valid=true;sync();draw(data);
    const problems=data.clashes.length+data.mountClashes.length;
    status(problems?'Parts overlap · adjust spacing':params.hangerFrom==='web'?`${params.count} T5 spokes · web hangers · ${params.keepHub?'with hub':'open centre'}`:data.hub?(params.spokeType==='t5'?`${params.count} T5 spokes · one printed hub`:`${params.count} lights · centre hub + ${params.count} spokes`):`${params.count} lights · suspension study` ,!!problems);buttons();
  }catch(e){if(e.name==='AbortError'||id!==requestId)return;valid=false;status(e.message,true);$('fitReport').textContent='Preview is not current. Correct the highlighted setting above.';$('fitReport').classList.add('error');buttons();}
}
function dispose(root){const geometries=new Set(),materials=new Set(),textures=new Set();root.traverse(o=>{if(o.geometry)geometries.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:o.material?[o.material]:[]){materials.add(m);if(m.map)textures.add(m.map);}});for(const g of geometries)g.dispose();for(const m of materials)m.dispose();for(const t of textures)t.dispose();}
function orient(object,item){const a=item.axes.map(v=>new THREE.Vector3(...v));object.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(...a));object.position.set(...item.center);}
function meshBox(size,material,position=[0,0,0]){const o=new THREE.Mesh(new THREE.BoxGeometry(...size),material);o.position.set(...position);return o;}
function numberLabel(text){const c=document.createElement('canvas');c.width=96;c.height=64;const x=c.getContext('2d');x.fillStyle='#dceba2';x.font='500 36px Arial';x.textAlign='center';x.fillText(text,48,44);const texture=new THREE.CanvasTexture(c);const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,depthTest:false,transparent:true,opacity:.95}));sprite.scale.set(23,15,1);return sprite;}
function saddlePreview(p,d){
  const g=new THREE.Group(),t=p.saddleWall,half=p.width/2+p.clearance+t;
  const material=new THREE.MeshStandardMaterial({color:0xcc2636,roughness:.65,metalness:.1});
  const outline=new THREE.Shape(),x=p.saddleLength/2,y=half+d.ear;
  outline.moveTo(-x,-y);outline.lineTo(x,-y);outline.lineTo(x,y);outline.lineTo(-x,y);outline.closePath();
  function round(cx,cy,r){const hole=new THREE.Path();hole.absarc(cx,cy,r,0,Math.PI*2,true);outline.holes.push(hole);}
  round(0,0,p.clipHole/2);
  for(const s of [-1,1]){
    if(p.support==='slings'){
      if(p.hanging==='paracord')round(0,s*d.earY,(p.cordDiameter+.8)/2);
      else {const hole=new THREE.Path(),hx=(p.webbingWidth+1)/2,hy=(p.webbingThickness+1)/2,cy=s*d.earY;hole.moveTo(-hx,cy-hy);hole.lineTo(-hx,cy+hy);hole.lineTo(hx,cy+hy);hole.lineTo(hx,cy-hy);hole.closePath();outline.holes.push(hole);}
    }
    g.add(meshBox([p.saddleLength,t,p.height+p.clearance+t],material,[0,s*(p.width/2+p.clearance+t/2),(p.clearance+t)/2]));
  }
  const plate=new THREE.Mesh(new THREE.ExtrudeGeometry(outline,{depth:t,bevelEnabled:false,curveSegments:12}),material);plate.position.z=p.height/2+p.clearance;g.add(plate);return g;
}
function clearSelection(){for(const box of selectionBoxes){scene.remove(box);box.geometry.dispose();box.material.dispose();}selectionBoxes=[];}
function selectComponent(number,id){clearSelection();group.updateMatrixWorld(true);for(const [key,item]of componentObjects)if(id?key===id:item.number===number){const box=new THREE.BoxHelper(item.object,0xe6f9a8);box.material.depthTest=false;box.renderOrder=10;scene.add(box);selectionBoxes.push(box);}}
function registerComponent(data,object,kind,unit,label){const entry=data.occurrences.find(o=>data.bom.find(p=>p.partNumber===o.partNumber)?.kind===kind&&(!unit||o.group===unit)&&(!label||o.name===label));if(entry)componentObjects.set(entry.id,{object,number:entry.partNumber});}
function draw(data){
  clearSelection();componentObjects.clear();
  if(group){scene.remove(group);dispose(group);}group=new THREE.Group();group.rotation.x=-Math.PI/2;scene.add(group);
  const p=data.parameters,bad=new Set([...data.clashes,...data.mountClashes].flat());
  const bodyMat=new THREE.MeshStandardMaterial({color:0x087de0,roughness:.38,metalness:.3});
  const capMat=new THREE.MeshStandardMaterial({color:0x21a2ef,roughness:.7});
  const glowMat=new THREE.MeshStandardMaterial({color:0x298dff,emissive:0x1065b8,emissiveIntensity:.35,roughness:.55});
  const badMat=new THREE.MeshStandardMaterial({color:0xe78669,roughness:.6});
  plugGroup=new THREE.Group();group.add(plugGroup);
  for(const b of data.bars){
    const bar=new THREE.Group();orient(bar,b);group.add(bar);registerComponent(data,bar,'light',`Light_unit_${String(b.id).padStart(2,'0')}`);
    bar.add(meshBox(data.size,bad.has(b.id)?badMat:bodyMat));
    bar.add(meshBox([p.length-12,p.width*.78,1.2],glowMat,[0,0,-p.height/2-.3]));
    for(const side of [-1,1])bar.add(meshBox([5,p.width+.3,p.height+.3],capMat,[side*(p.length/2-2.5),0,0]));
    const label=numberLabel(String(b.id));label.position.set(...b.center);label.position.z+=p.height/2+18;group.add(label);
    if(p.endSpace>0){const plugs=new THREE.Group();orient(plugs,b);plugGroup.add(plugs);for(const s of [-1,1])plugs.add(meshBox([p.endSpace,p.width,p.height],new THREE.MeshBasicMaterial({color:0xe7cd82,transparent:true,opacity:.16,depthWrite:false}),[s*(p.length+p.endSpace)/2,0,0]));}
  }
  const master=data.mounts.length?saddlePreview(p,data.saddle):null;
  for(const m of data.mounts){const carrier=master.clone();orient(carrier,m);group.add(carrier);registerComponent(data,carrier,'collar',`Light_unit_${String(m.bar).padStart(2,'0')}`,`Root collar ${m.number}`);}
  if(data.hub?.included){
    const h=data.hub,mat=new THREE.MeshStandardMaterial({color:0xcc2636,roughness:.7});
    const hole=(shape,x,y,r)=>{const path=new THREE.Path();path.absarc(x,y,r,0,Math.PI*2,true);shape.holes.push(path);};
    const disk=new THREE.Shape();disk.absarc(0,0,p.hubRadius,0,Math.PI*2,false);
    if(p.hanging==='paracord')hole(disk,0,0,p.hangerHole/2);
    else{const path=new THREE.Path(),x=(p.webbingWidth+1)/2,y=(p.webbingThickness+1)/2;path.moveTo(-x,-y);path.lineTo(-x,y);path.lineTo(x,y);path.lineTo(x,-y);path.closePath();disk.holes.push(path);}
    const arm=new THREE.Shape(),half=p.armWidth/2;
    arm.moveTo(h.armRoot,-half);arm.lineTo(h.armEnd,-half);arm.lineTo(h.armEnd,half);arm.lineTo(h.armRoot,half);arm.closePath();
    for(const radius of h.fixingRadii)hole(arm,radius,0,p.hubFixing/2);
    for(const radius of [p.radius-p.length*.32,p.radius+p.length*.32])hole(arm,radius,0,p.clipHole/2);
    const armGeo=p.spokeType==='printed'?new THREE.ExtrudeGeometry(arm,{depth:p.armThickness,bevelEnabled:false,curveSegments:12}):null;
    for(const b of data.bars){const a=b.yaw*Math.PI/180;for(const radius of h.fixingRadii)hole(disk,radius*Math.cos(a),radius*Math.sin(a),(p.spokeType==='t5'?p.clipHole:p.hubFixing)/2);if(armGeo){const spoke=new THREE.Mesh(armGeo,mat);spoke.rotation.z=a;spoke.position.z=h.armBottom;group.add(spoke);registerComponent(data,spoke,'arm',`Light_unit_${String(b.id).padStart(2,'0')}`);}}
    const hub=new THREE.Mesh(new THREE.ExtrudeGeometry(disk,{depth:p.hubThickness,bevelEnabled:false,curveSegments:48}),mat);hub.position.z=h.bottom;group.add(hub);registerComponent(data,hub,'hub');
  }
  if(data.web){
    const web=data.web,geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(web.mesh.positions,3));geo.setIndex(web.mesh.indices);geo.computeVertexNormals();
    const mat=new THREE.MeshStandardMaterial({color:0xcc2636,roughness:.7});
    for(const [i,item]of web.panels.entries()){const panel=new THREE.Mesh(geo,mat);panel.rotation.z=item.angle*Math.PI/180;panel.position.z=web.z;group.add(panel);registerComponent(data,panel,'web',null,`${p.webConstruction==='integrated'?'Clip bridge':'Web panel'} ${String(i+1).padStart(2,'0')}`);}
    if(web.collars.length){const collar=saddlePreview({...p,support:'slings',hanging:'paracord',cordDiameter:p.webHole-.8},{ear:p.webHole+2*p.saddleWall,earY:web.earY});
    for(const item of web.collars){const copy=collar.clone();orient(copy,item);group.add(copy);registerComponent(data,copy,'web-collar',`Light_unit_${String(item.bar).padStart(2,'0')}`);}}
  }
  if(data.collector){const item=data.collector,geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(item.mesh.positions,3));geo.setIndex(item.mesh.indices);geo.computeVertexNormals();const junction=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:0xcc2636,roughness:.7}));junction.position.z=item.z;group.add(junction);registerComponent(data,junction,'collector');}
  guideGroup=new THREE.Group();group.add(guideGroup);
  const cordMaterial=new THREE.MeshStandardMaterial({color:p.hanging==='paracord'?0xffd51f:(p.printedWebbing?0xcc2636:0xa5a5a5),roughness:1});
  for(const [index,a] of data.anchors.entries()){
    const start=new THREE.Vector3(...a.bottom),end=new THREE.Vector3(...a.top),delta=end.clone().sub(start);
    const span=delta.length();let geometry;
    if(p.hanging==='webbing'&&p.printedWebbing){
      const shape=new THREE.Shape(),hx=p.webbingWidth/2,hy=span/2+p.strapEnd;
      shape.moveTo(-hx,-hy);shape.lineTo(hx,-hy);shape.lineTo(hx,hy);shape.lineTo(-hx,hy);shape.closePath();
      for(const sign of [-1,1]){const hole=new THREE.Path();hole.absarc(0,sign*span/2,p.strapHole/2,0,Math.PI*2,true);shape.holes.push(hole);}
      geometry=new THREE.ExtrudeGeometry(shape,{depth:p.webbingThickness,bevelEnabled:false,curveSegments:8});geometry.translate(0,0,-p.webbingThickness/2);
    }else geometry=p.hanging==='paracord'?new THREE.CylinderGeometry(p.cordDiameter/2,p.cordDiameter/2,span,6):new THREE.BoxGeometry(p.webbingWidth,span,p.webbingThickness);
    const line=new THREE.Mesh(geometry,cordMaterial);delta.normalize();
    if(p.hanging==='webbing'){
      const x=new THREE.Vector3(1,0,0).cross(delta);if(x.length()<1e-6)x.set(0,1,0).cross(delta);x.normalize();const z=x.clone().cross(delta);
      line.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(x,delta,z));
    }else line.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta);
    line.position.copy(start.add(end).multiplyScalar(.5));guideGroup.add(line);if(p.hanging==='webbing'&&p.printedWebbing)registerComponent(data,line,'strap',null,`Suspension strap ${String(index+1).padStart(2,'0')}`);
  }
  const r=data.hub?12:Math.max(45,...data.anchors.map(a=>Math.hypot(a.top[0],a.top[1])))+10;
  const canopy=new THREE.Mesh(new THREE.CylinderGeometry(r,r,6,64),new THREE.MeshStandardMaterial({color:0x26352a,metalness:.5,roughness:.5}));canopy.rotation.x=Math.PI/2;canopy.position.z=data.ceiling+3;guideGroup.add(canopy);
  guideGroup.visible=$('showGuides').getAttribute('aria-pressed')==='true';plugGroup.visible=$('showPlugs').getAttribute('aria-pressed')==='true';
  $('title').textContent=p.count===3&&p.layout==='sunburst'?'Three points of light.':titles[p.layout];
  $('subtitle').textContent=`${p.count} × Barrina T5 · ${p.length} mm · ${p.hanging==='paracord'?'Paracord':'Webbing'}`;
  $('bounds').textContent=data.bounds.size.map(n=>Math.round(n)).join(' × ');$('drop').textContent=Math.round(data.ceiling);
  const collision=data.clashes.length||data.mountClashes.length;
  $('fitReport').classList.toggle('error',!!collision);
  $('fitReport').textContent=data.clashes.length?`Light bars overlap: ${data.clashes.slice(0,3).map(a=>a.join(' & ')).join(', ')}. Increase spacing.`:data.mountClashes.length?`Saddles touch other parts: ${data.mountClashes.slice(0,3).map(a=>a.join(' & ')).join(', ')}. Increase spacing or tier separation.`:data.connectorClashes.length?'Light bodies clear · plug spaces overlap. Allow more room for connectors.':p.hangerFrom==='web'?`Web eyelets carry the hanging spans · ${p.keepHub?'centre hub included':'open centre'}`:data.hub?(p.spokeType==='t5'?'T5s held at the hub · one central hanger':'Printed hub + bolted spokes · one central hanger'):'Slings need a rigid spreader to prevent inward movement';

  const oversize=data.printChecks.filter(check=>!check.fits);
  if(oversize.length){$('fitReport').textContent+=` · ${oversize.length} printed part type(s) exceed ${p.printSize} mm`;$('fitReport').classList.add('error');}
  $('partDetail').textContent='Select a component to locate it in the preview. Repeated parts share the same part number.';
  renderNavigator(data,selectComponent);
  if(!lastFit){fitView();lastFit=true;}
}
function fitView(){
  if(!model)return;
  const bounds=new THREE.Box3().setFromObject(group),center=bounds.getCenter(new THREE.Vector3()),size=bounds.getSize(new THREE.Vector3());
  const scale=Math.max(size.y,size.x/Math.max(.3,camera.aspect),size.z)*1.65+100;
  controls.target.copy(center);const dir=currentView==='top'?new THREE.Vector3(0,1,.001):currentView==='front'?new THREE.Vector3(0,.05,1):new THREE.Vector3(1.1,.65,1.25);
  camera.position.copy(center).add(dir.normalize().multiplyScalar(scale));camera.near=.5;camera.far=Math.max(30000,scale*5);camera.updateProjectionMatrix();controls.update();
}
async function init(){
  try{
    const r=await fetch(api);if(!r.ok)throw Error('The chandelier service is unavailable.');const config=await r.json();defaults=config.defaults;params={...defaults};nxAvailable=!!config.nx?.available;
    for(const fmt of ['x_b','x_t'])$('format').querySelector(`[value="${fmt}"]`).disabled=!nxAvailable;
    $('nxNote').textContent='Simple planes and cylindrical holes keep these components easy to edit. '+(nxAvailable?'Parasolid export uses your installed NX translator and checks every body by importing it back. STEP retains the named assembly structure; Parasolid contains named solid bodies.':'The NAS generates STEP assemblies for NX. Parasolid needs the Windows edition of this tool with Siemens NX installed; it is unavailable on this NAS.');
    for(const [id,name]of Object.entries(config.layouts)){
      const b=document.createElement('button');b.dataset.layout=id;b.innerHTML=`<svg viewBox="0 0 66 48" aria-hidden="true"><path d="${drawings[id]}"/></svg><span>${name}</span>`;
      b.onclick=()=>{params.layout=id;params.support=id==='sunburst'?'hub':'slings';if(id==='spiral'||params.support==='hub')params.tiers=1;if(params.support==='hub')params.tilt=0;else{params.webEnabled=false;params.hangerFrom='hub';}autoSpace();lastFit=false;sync();queue();};$('layouts').append(b);
    }
    if(nas){$('saveNas').hidden=false;try{const saved=await store.load();if(saved.chandelier?.parameters)params=restoreParameters(saved.chandelier.parameters);if(saved.chandelier?.exportOptions)applyExportOptions(saved.chandelier.exportOptions);}catch(e){status(e.message,true);}}
    else {try{const saved=JSON.parse(localStorage.getItem('chandelier-draft-v1'));if(saved?.parameters)params=restoreParameters(saved.parameters);if(saved?.exportOptions)applyExportOptions(saved.exportOptions);}catch{}}
    for(const k of Object.keys(defaults))if($(k))$(k).addEventListener('input',()=>{
      params[k]=typeof defaults[k]==='boolean'?$(k).checked:typeof defaults[k]==='number'?Number($(k).value):$(k).value;
      if(k==='support'&&params.support==='hub'){params.layout='sunburst';params.tiers=1;params.tilt=0;autoSpace();lastFit=false;}
      if(k==='support'&&params.support==='slings'){params.webEnabled=false;params.hangerFrom='hub';}
      if(k==='spokeType'){if(params.spokeType==='printed'){params.webEnabled=false;params.hangerFrom='hub';}autoSpace();lastFit=false;}
      if(k==='webEnabled'&&!params.webEnabled)params.hangerFrom='hub';
      if(k==='hangerFrom'&&params.hangerFrom==='web')params.webEnabled=true;
      if(k==='count'&&Number.isInteger(params.count)&&params.count>=3){params.tiers=Math.min(params.tiers,Math.floor(params.count/3));autoSpace();lastFit=false;}
      if(k==='hanging'){const opening=params.hanging==='paracord'?params.cordDiameter+.8:params.webbingWidth+1;params.saddleLength=Math.max(params.saddleLength,Math.ceil(opening+2*params.saddleWall));autoSpace();}
      sync();queue();
    });
    document.querySelectorAll('[data-count]').forEach(b=>b.onclick=()=>{params.count=Number(b.dataset.count);params.tiers=Math.min(params.tiers,Math.floor(params.count/3));autoSpace();lastFit=false;sync();queue();});
    sync();await preview();dirty=false;
  }catch(e){status(e.message,true);}
}
function restoreParameters(p){return {...defaults,...p,support:p.support||'slings',spokeType:p.spokeType||'printed',webEnabled:p.webEnabled??false,hangerFrom:p.hangerFrom||'hub',keepHub:p.keepHub??true,webConstruction:p.webConstruction||'bolted',cordCollector:p.cordCollector??false};}
function applyExportOptions(o){if(['step','brep','stl',...(nxAvailable?['x_b','x_t']:[])].includes(o.format))$('format').value=o.format;if(['assembly','saddles','single','strap','parts','hub','arm','web','web-collar','collector'].includes(o.scope))$('scope').value=o.scope;}
$('drawingLayout').onclick=()=>{Object.assign(params,{layout:'sunburst',support:'hub',spokeType:'t5',tiers:1,tilt:0,webEnabled:true,webConstruction:'integrated',webReach:20,hubRadius:90,bridgeClipLength:16,bridgeBandWidth:24,bridgeLip:.8,webThickness:3,hangerFrom:'web',keepHub:false,hanging:'paracord',cordCollector:true});if(params.count!==3)autoSpace();lastFit=false;sync();queue();};
$('autoSpace').onclick=()=>{autoSpace();lastFit=false;sync();queue();};
$('format').onchange=buttons;$('scope').onchange=buttons;
$('fit').onclick=fitView;
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{currentView=b.dataset.view;document.querySelectorAll('[data-view]').forEach(v=>v.classList.toggle('active',v===b));fitView();});
for(const [id,get]of [['showGuides',()=>guideGroup],['showPlugs',()=>plugGroup]])$(id).onclick=()=>{const visible=$(id).getAttribute('aria-pressed')!=='true';$(id).setAttribute('aria-pressed',visible);if(get())get().visible=visible;};
$('saveDesign').onclick=()=>{download(JSON.stringify(savePayload(),null,2),'grow-light-chandelier.json','application/json');if(!nas){try{localStorage.setItem('chandelier-draft-v1',JSON.stringify(savePayload()));}catch{}}dirty=false;status('Design JSON exported');};
$('saveNas').onclick=async()=>{if(!valid||busy)return;busy=true;buttons();try{await store.save({chandelier:savePayload()});dirty=false;status('Chandelier saved on NAS');}catch(e){status(e.message,true);}finally{busy=false;buttons();}};
$('openDesign').onclick=()=>$('designFile').click();
$('designFile').onchange=async()=>{const file=$('designFile').files[0];if(!file)return;try{
  if(file.size>64000)throw Error('Choose a chandelier JSON file under 64 KB.');const value=JSON.parse(await file.text());const saved=value.app==='lampshade-studio'?value.chandelier:value;
  if(saved?.app!=='grow-light-chandelier'||saved.version!==1||!saved.parameters)throw Error('Choose a Grow-light Chandelier design JSON.');
  const candidate=restoreParameters(saved.parameters);const r=await fetch(api+'/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(candidate)});const data=await r.json();if(!r.ok)throw Error(data.error||'Invalid chandelier design.');
  pending?.abort();requestId++;clearTimeout(timer);params=data.parameters;model=data;valid=true;dirty=true;lastFit=false;applyExportOptions(saved.exportOptions||{});sync();draw(data);status('Chandelier design opened');buttons();
}catch(e){status(e.message,true);}finally{$('designFile').value='';}};
$('exportBom').onclick=async()=>{
  if(!valid)return;try{const response=await fetch(api+'/bom',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(params)});if(!response.ok){const error=await response.json();throw Error(error.error||'BOM export failed.');}download(await response.blob(),`chandelier-${params.count}-lights-bom.csv`);status('BOM exported · quantities for the full arrangement');}catch(e){status(e.message,true);}
};
$('exportTree').onclick=()=>{if(valid)download(JSON.stringify({app:'grow-light-chandelier',parameters:params,tree:model.tree,bom:model.bom,occurrences:model.occurrences},null,2),'chandelier-assembly-structure.json','application/json');};
$('export').onclick=async()=>{
  if(!valid||busy)return;const format=$('format').value,scope=$('scope').value,snapshot={...params,format,scope};busy=true;buttons();status('Building and checking your '+format.toUpperCase()+'…');
  try{const r=await fetch(api+'/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(snapshot)});if(!r.ok){const error=await r.json();throw Error(error.error||'Export failed.');}
    const blob=await r.blob();download(blob,`chandelier-${snapshot.layout}-${snapshot.count}-${scope}.${format}`);status(`${format.toUpperCase()} exported · ${(blob.size/1e6).toFixed(2)} MB`);
  }catch(e){status(e.message,true);}finally{busy=false;buttons();}
};
window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
init();
