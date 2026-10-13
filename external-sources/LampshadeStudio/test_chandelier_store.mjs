import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const source=await readFile(new URL('./public/chandelier-store.js',import.meta.url),'utf8');
const {createDesignStore}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
let document={app:'lampshade-studio',version:2,parameters:{style:'woven'},custom:'preserve'},rev=1;
const fetcher=async(url,options={})=>{
  assert.equal(url,'/api/designs/lampshade');
  if(options.method==='PUT'){
    if(options.headers['If-Match']!==`"${rev}"`)return new Response('{}',{status:409});
    document=JSON.parse(options.body);rev++;
  }
  return new Response(JSON.stringify(document),{headers:{ETag:`W/"${rev}"`}});
};
const chandelier=createDesignStore(fetcher,'/api/designs/lampshade');
const shade=createDesignStore(fetcher,'/api/designs/lampshade');
await chandelier.load();await shade.load();
await chandelier.save({chandelier:{parameters:{count:3}}});
assert.equal(document.parameters.style,'woven');assert.equal(document.custom,'preserve');
await assert.rejects(shade.save({parameters:{style:'spiral'}}),/newer NAS design/);
await shade.load();await shade.save({parameters:{style:'spiral'}});
assert.equal(document.chandelier.parameters.count,3);
assert.equal(document.parameters.style,'spiral');
await assert.rejects(chandelier.save({chandelier:{parameters:{count:6}}}),/newer NAS design/);
assert.equal(document.chandelier.parameters.count,3);
console.log('PASS: independent shade/chandelier saves, weak ETags, stale-save rejection and field preservation.');
