/* Local preview of the built page. Needed because index.html loads assets/ over http.
   Run: node serve.js   then open http://localhost:8792 */
const http=require('http'),fs=require('fs'),path=require('path');
const ROOT=__dirname, PORT=8792;
const TYPES={'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css',
  '.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp',
  '.svg':'image/svg+xml','.ico':'image/x-icon','.json':'application/json'};
http.createServer((req,res)=>{
  let p=decodeURIComponent(req.url.split('?')[0]);
  if(p==='/') p='/index.html';
  const f=path.join(ROOT,p);
  if(!f.startsWith(ROOT)){ res.writeHead(403); return res.end(); }
  fs.readFile(f,(err,data)=>{
    if(err){ res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'}); return res.end('404'); }
    res.writeHead(200,{'Content-Type':TYPES[path.extname(f).toLowerCase()]||'application/octet-stream',
                       'Cache-Control':'no-store'});
    res.end(data);
  });
}).listen(PORT,()=>console.log('preview on http://localhost:'+PORT));
