const $=id=>document.getElementById(id);
let opened=new Set(['Light_unit_01','Centre_hub','Inter_spoke_webs','Repeated_clip_bridges','Suspension']);
export function renderNavigator(model,select){
  const summary=model.assemblySummary;
  $('assemblySummary').textContent=`${summary.modeledComponents} components · ${summary.uniqueParts} unique CAD parts · ${summary.printedQuantity} to print`;
  const byNumber=new Map(model.bom.map(row=>[row.partNumber,row]));
  const detail=row=>{const spec=Object.entries(row.specification).filter(([,v])=>typeof v==='number').map(([k,v])=>`${k}: ${Number(v.toFixed(2))}`).join(' · ');$('partDetail').textContent=`${row.partNumber} · ${row.quantity} ${row.unit} in total. ${row.notes||spec||'Shared printed component.'}`;};
  const choose=(row,id=null)=>{select(row.partNumber,id);detail(row);document.querySelectorAll('[data-part]').forEach(e=>e.classList.toggle('selected',e.dataset.part===row.partNumber));};
  const nodes=model.tree.children.map(group=>{
    const box=document.createElement('details');box.open=opened.has(group.id);
    const heading=document.createElement('summary');heading.textContent=group.name;box.append(heading);
    box.ontoggle=()=>{if(!box.isConnected)return;if(box.open)opened.add(group.id);else opened.delete(group.id);};
    for(const child of group.children){
      const row=byNumber.get(child.partNumber),button=document.createElement('button');button.type='button';button.dataset.part=child.partNumber;button.className='component-row';
      const text=document.createElement('span');text.textContent=child.name;
      const number=document.createElement('small');number.textContent=child.partNumber;text.append(number);
      const quantity=document.createElement('b');quantity.textContent=`×${child.quantity}`;button.append(text,quantity);
      button.onclick=()=>choose(row,child.modeled?child.id:null);box.append(button);
    }return box;
  });
  $('productTree').replaceChildren(...nodes);
  $('bomRows').replaceChildren(...model.bom.map(row=>{
    const tr=document.createElement('tr'),name=document.createElement('td'),qty=document.createElement('td'),button=document.createElement('button');button.dataset.part=row.partNumber;
    button.textContent=row.name;const small=document.createElement('small');small.textContent=`${row.partNumber} · ${row.category}${row.modeled?'':' · not modeled'}`;button.append(small);button.onclick=()=>choose(row);name.append(button);qty.textContent=row.quantity+(row.unit==='each'?'':` ${row.unit}`);tr.append(name,qty);return tr;
  }));
  $('printChecks').replaceChildren(...model.printChecks.map(check=>{
    const line=document.createElement('div');line.className='print-check'+(check.fits?'':' error');
    const title=document.createElement('b');title.textContent=`${check.fits?'✓':'!'} ${check.name}`;
    const size=document.createElement('span');size.textContent=check.size.map(v=>v.toFixed(1)).join(' × ')+' mm'+(check.fits?'':' · exceeds volume');line.append(title,size);return line;
  }));
}
function toggle(show){$('assemblyPanel').hidden=!show;$('showAssembly').setAttribute('aria-pressed',String(show));}
$('showAssembly').onclick=()=>toggle($('assemblyPanel').hidden);
$('closeAssembly').onclick=()=>toggle(false);
for(const [tab,other,bom]of [['treeTab','bomTab',false],['bomTab','treeTab',true]])$(tab).onclick=()=>{$(tab).setAttribute('aria-pressed','true');$(other).setAttribute('aria-pressed','false');$('productTree').hidden=bom;$('bomView').hidden=!bom;};
