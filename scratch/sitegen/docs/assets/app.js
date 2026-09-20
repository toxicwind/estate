
(function(){
function norm(s){return (s||"").toLowerCase();}
var q=document.getElementById("q"), fv=document.getElementById("fv"),
    fc=document.getElementById("fc"), tb=document.querySelector("#mtable tbody");
if(tb){
  var rows=[].slice.call(tb.querySelectorAll("tr.mrow"));
  var det={}; [].slice.call(tb.querySelectorAll("tr.detail-row")).forEach(function(r){det[r.getAttribute("data-for")]=r;});
  function apply(){
    var qq=norm(q&&q.value), vv=fv&&fv.value, cc=fc&&fc.value, n=0;
    rows.forEach(function(r){
      var ok=(!qq||r.getAttribute("data-m").indexOf(qq)>=0)&&(!vv||r.getAttribute("data-v")===vv)&&(!cc||r.getAttribute("data-c")===cc);
      r.style.display=ok?"":"none";
      var d=det[r.id.replace("row-","")]; if(d&&!ok)d.hidden=true;
      if(ok)n++;
    });
    var c=document.getElementById("count"); if(c)c.textContent=n+" shown";
  }
  if(q)q.addEventListener("input",apply);
  if(fv)fv.addEventListener("change",apply);
  if(fc)fc.addEventListener("change",apply);
  rows.forEach(function(r){
    r.addEventListener("click",function(e){
      if(e.target.tagName==="A")return;
      var d=det[r.id.replace("row-","")]; if(d)d.hidden=!d.hidden;
    });
  });
  // sortable headers
  var idx={m:0,c:1,v:2,a:3,t:4};
  document.querySelectorAll("#mtable thead th[data-s]").forEach(function(th){
    th.addEventListener("click",function(){
      var k=th.getAttribute("data-s"), col=idx[k], asc=th.classList.toggle("asc");
      var arr=rows.slice();
      function val(r){
        var t=r.children[col].textContent.trim();
        if(k==="a"||k==="t"){var f=parseFloat(t);return isNaN(f)?(asc?1e18:-1e18):f;}
        if(k==="v"){var o=["alive-fast","timeout-fast","streaming-noheaders","unavailable-503","error-other","dead-404-gated"];return o.indexOf(r.getAttribute("data-v"));}
        return t.toLowerCase();
      }
      arr.sort(function(a,b){var x=val(a),y=val(b);return (x<y?-1:x>y?1:0)*(asc?1:-1);});
      arr.forEach(function(r){tb.appendChild(r);tb.appendChild(det[r.id.replace("row-","")]);});
    });
  });
  // deep link #model=org__name
  function hash(){
    var m=location.hash.match(/^#model=(.+)$/);
    if(!m)return;
    var row=document.getElementById("row-"+m[1]);
    if(row){if(q)q.value="";if(fv)fv.value="";if(fc)fc.value="";apply();
      var d=det[m[1]]; if(d)d.hidden=false;
      row.scrollIntoView({block:"center"});row.style.outline="1px solid #60a5fa";}
  }
  window.addEventListener("hashchange",hash);hash();apply();
}
})();
