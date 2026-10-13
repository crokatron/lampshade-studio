// One shared document, independent shade/chandelier fields, conditional saves.
export function createDesignStore(fetcher, path) {
  let document=null, revision=null;
  const tag=r=>r.headers.get('X-Project-Revision')||r.headers.get('ETag')?.replace(/^W\//,'');
  return {
    async load(){
      const r=await fetcher(path); if(!r.ok)throw Error('NAS design unavailable. You can still export a JSON copy.');
      document=await r.json(); revision=tag(r);
      if(!revision)throw Error('NAS save revision unavailable. Reload before saving.');
      return document;
    },
    async save(fields){
      if(!document||!revision)throw Error('Reload the NAS design before saving. Export JSON to keep your changes.');
      const next={...document,...fields,app:'lampshade-studio',version:3};
      const r=await fetcher(path,{method:'PUT',headers:{'Content-Type':'application/json','If-Match':revision},body:JSON.stringify(next)});
      if(r.status===409){revision=null;throw Error('A newer NAS design exists. Export JSON, then reload to avoid replacing it.');}
      if(!r.ok)throw Error('Could not save to NAS. Your changes remain here.');
      revision=tag(r); document=next; return next;
    }
  };
}
