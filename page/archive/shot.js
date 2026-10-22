const { chromium } = require('playwright');
(async()=>{
 const b=await chromium.launch(); 
 for (const [w,scheme,name] of [[1280,'light','desk'],[400,'dark','phone']]){
  const p=await b.newPage({viewport:{width:w,height:900},colorScheme:scheme});
  const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
  const html=require('fs').readFileSync('bedexit_proposal.html','utf8');
  await p.setContent('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+html+'</body></html>',{waitUntil:'load'});
  await p.waitForTimeout(800);
  const sw=await p.evaluate(()=>[document.documentElement.scrollWidth,innerWidth]);
  console.log(name,'errors',errs,'scrollW',sw);
  await p.screenshot({path:`${name}.png`,fullPage:true});
 }
 await b.close();})();
