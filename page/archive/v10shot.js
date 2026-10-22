const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch();
 const p=await b.newPage({viewport:{width:1280,height:900},colorScheme:'light'});
 const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 const html=require('fs').readFileSync('bedexit_proposal.html','utf8');
 await p.setContent('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+html+'</body></html>',{waitUntil:'load'});
 await p.waitForTimeout(800);
 const sc=await p.$('#concept');
 for(const s of ['B','A']){
  await p.click(`#scheme button[data-s="${s}"]`);await p.waitForTimeout(300);
  const n=await p.$$eval('#tabs button',x=>x.length);
  for(let i=0;i<n;i++){await p.click(`#tabs button:nth-child(${i+1})`);await p.waitForTimeout(800);
    await (await p.$('#scene')).screenshot({path:`v10_${s}${i}.png`});}
 }
 // mid-tween frame
 await p.click('#scheme button[data-s="B"]');await p.waitForTimeout(300);
 await p.click('#tabs button:nth-child(5)');await p.waitForTimeout(800);
 await p.click('#tabs button:nth-child(6)');await p.waitForTimeout(300);
 await (await p.$('#scene')).screenshot({path:`v10_Bmid.png`});
 for(const id of ['compare','height','dilemma','delta','risk','explorerA']){const e=await p.$('#'+id);await e.screenshot({path:`v10_${id}.png`});}
 const sw=await p.evaluate(()=>[document.documentElement.scrollWidth,innerWidth]);
 console.log('errors',errs,'scrollW',sw);
 const q=await b.newPage({viewport:{width:390,height:800},colorScheme:'dark'});
 const e2=[];q.on('pageerror',e=>e2.push(e.message));
 await q.setContent('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+html+'</body></html>',{waitUntil:'load'});
 await q.waitForTimeout(800);
 console.log('phone errors',e2,await q.evaluate(()=>[document.documentElement.scrollWidth,innerWidth]));
 await (await q.$('#compare')).screenshot({path:'v10_phone_compare.png'});
 await (await q.$('#concept')).screenshot({path:'v10_phone_concept.png'});
 await b.close();})();
